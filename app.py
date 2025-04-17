from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import os
from werkzeug.utils import secure_filename
import uuid
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import User, Case
from datetime import datetime
from gridfs import GridFS
import io
from PIL import Image

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure upload folder temporarily (for processing only)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to fix MongoDB URI format
def get_formatted_mongodb_uri():
    uri = os.getenv('MONGODB_URI')
    if not uri:
        return None
        
    # Remove any existing parameters to add our own
    if '?' in uri:
        base_uri = uri.split('?')[0]
    else:
        base_uri = uri
        
    # Ensure URI ends with the database name
    if not base_uri.split('/')[-1]:
        base_uri += 'criminal_case_db'
    elif base_uri.split('/')[-1] == '':
        base_uri += 'criminal_case_db'
        
    # Add required parameters
    final_uri = f"{base_uri}?retryWrites=true&w=majority&tls=true"
    
    return final_uri

# MongoDB setup
mongodb_uri = get_formatted_mongodb_uri()

# Only proceed with MongoDB init if URI is available
if mongodb_uri:
    try:
        # Create a MongoClient instance that will work on Render
        # Use fully explicit parameters to avoid SSL issues
        client = MongoClient(
            host=mongodb_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,  # Proper certificate validation
            retryWrites=True,
            w='majority',
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=30000,
            appName='criminal-case-app'
        )
        
        # Test connection with longer timeout for initial connection
        client.server_info()
        print("MongoDB connection successful")
        
        # Access database and collections
        db = client['criminal_case_db']
        users_collection = db['users']
        cases_collection = db['cases']
        
        # Initialize GridFS for storing images
        fs = GridFS(db, collection='images')
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        client = None
        db = None
        users_collection = None
        cases_collection = None
        fs = None
else:
    print("No MongoDB URI provided")
    client = None
    db = None
    users_collection = None
    cases_collection = None
    fs = None

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Bcrypt
bcrypt = Bcrypt(app)

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if MongoDB is connected
        if users_collection is None:
            flash('Database service unavailable. Please try again later.')
            return render_template('login.html')
        
        try:
            user_data = users_collection.find_one({'username': username})
            
            if user_data and bcrypt.check_password_hash(user_data['password'], password):
                user = User(user_data)
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Login failed. Please check your username and password.')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again later.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))
        
        # Check if MongoDB is connected
        if users_collection is None:
            flash('Database service unavailable. Please try again later.')
            return render_template('register.html')
            
        try:    
            existing_user = users_collection.find_one({
                '$or': [
                    {'username': username},
                    {'email': email}
                ]
            })
            
            if existing_user:
                flash('Username or email already exists.')
                return redirect(url_for('register'))
                
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User.create_user(username, email, hashed_password)
            
            result = users_collection.insert_one(new_user)
            if result.inserted_id:
                flash('Registration successful! You can now log in.')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.')
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again later.')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Validate form data
        if not title:
            flash('Title is required!')
            return redirect(request.url)
        
        if client is None or cases_collection is None:
            flash('Database connection error. Please try again later or contact support.')
            return redirect(request.url)
        
        # Handle multiple file uploads
        uploaded_files = []
        if 'images' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        files = request.files.getlist('images')
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                try:
                    # Create a unique filename
                    filename = str(uuid.uuid4()) + secure_filename(file.filename)
                    
                    # Process and optimize the image
                    image = Image.open(file)
                    
                    # Convert to RGB if needed
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Resize if too large (optional)
                    max_size = (1200, 1200)
                    image.thumbnail(max_size, Image.LANCZOS)
                    
                    # Save to in-memory buffer
                    buffer = io.BytesIO()
                    image.save(buffer, format='JPEG', quality=85, optimize=True)
                    buffer.seek(0)
                    
                    # Store in MongoDB GridFS with metadata
                    image_id = fs.put(
                        buffer, 
                        filename=filename,
                        contentType='image/jpeg', 
                        metadata={
                            'uploaded_at': datetime.now(),
                            'original_filename': file.filename
                        }
                    )
                    
                    # Save the GridFS ID as a string to reference later
                    uploaded_files.append(str(image_id))
                except Exception as e:
                    print(f"Error processing image: {e}")
                    flash(f"Error processing image: {file.filename}")
                    continue
        
        try:
            # Save data to MongoDB
            user_id = current_user.id if current_user.is_authenticated else None
            case_data = Case.create_case(
                title, 
                description, 
                latitude, 
                longitude, 
                uploaded_files,
                user_id
            )
            
            result = cases_collection.insert_one(case_data)
            
            if result.inserted_id:
                flash('Case submitted successfully!')
                if current_user.is_authenticated:
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('submission_success'))
            else:
                flash('Error submitting case. Please try again.')
        except Exception as e:
            print(f"Error saving case to database: {e}")
            flash('Database error. Please try again later.')
            
        return redirect(url_for('index'))
        
    return render_template('index.html')

@app.route('/image/<image_id>')
def get_image(image_id):
    """Route to serve images from GridFS"""
    if fs is None:
        return redirect(url_for('static', filename='img/no-image.svg')), 404
        
    try:
        # Find image in GridFS by ID
        image = fs.get(ObjectId(image_id))
        return send_file(
            io.BytesIO(image.read()),
            mimetype=image.content_type or 'image/jpeg',
            download_name=image.filename
        )
    except Exception as e:
        print(f"Error serving image: {e}")
        # Return a default image
        return redirect(url_for('static', filename='img/no-image.svg')), 404

@app.route('/submission-success')
def submission_success():
    return render_template('submission_success.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if cases_collection is None:
        flash('Database connection error. Please try again later.')
        return render_template('dashboard.html', cases=[])
    
    try:
        # Get all cases, sorted by creation date (newest first)
        cases = list(cases_collection.find().sort('created_at', -1))
        
        # Format cases for display
        formatted_cases = [Case.format_case(case) for case in cases]
        
        return render_template('dashboard.html', cases=formatted_cases)
    except Exception as e:
        print(f"Error retrieving cases: {e}")
        flash('Error retrieving cases. Please try again later.')
        return render_template('dashboard.html', cases=[])

@app.route('/case/<case_id>')
@login_required
def view_case(case_id):
    if cases_collection is None:
        flash('Database connection error. Please try again later.')
        return redirect(url_for('dashboard'))
    
    try:
        case = cases_collection.find_one({'_id': ObjectId(case_id)})
        if not case:
            flash('Case not found.')
            return redirect(url_for('dashboard'))
        
        formatted_case = Case.format_case(case)
        return render_template('case_details.html', case=formatted_case)
    except Exception as e:
        print(f"Error retrieving case details: {e}")
        flash('Error retrieving case details. Please try again later.')
        return redirect(url_for('dashboard'))

@app.route('/api/update-status/<case_id>', methods=['POST'])
@login_required
def update_status(case_id):
    try:
        new_status = request.json.get('status')
        
        if new_status not in Case.STATUS_OPTIONS:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
            
        result = cases_collection.update_one(
            {'_id': ObjectId(case_id)},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.now()
                }
            }
        )
        
        if result.modified_count:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Case not found or status not changed'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Test MongoDB connection
    try:
        client.server_info()
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    
    # Get port from environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 