# Criminal Case Management System

A Flask application that provides a complete system for submitting and managing criminal case information, including user authentication, form submission, and case tracking.

## Features

- User authentication (register, login, logout)
- Responsive design that works on both mobile and desktop
- Multiple image upload with preview
- Geolocation support that automatically requests user permission
- Case management dashboard with status tracking
- Detailed case view
- MongoDB integration for data storage

## Requirements

- Python 3.8+
- MongoDB (Cloud or Local)
- Dependencies in requirements.txt

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd criminal-case
```

2. Create and activate a virtual environment (optional but recommended):
```
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Configure the environment variables:
   - Create a `.env` file in the root directory
   - Add the following variables (replace with your actual values):
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MONGODB_URI=mongodb+srv://vikazztalreja:<db_password>@criminalsdata.bnckc6y.mongodb.net/?retryWrites=true&w=majority&appName=criminalsdata
```
   - Replace `<db_password>` with the actual database password

## Running the Application

1. Start the Flask development server:
```
python app.py
```

2. Open a web browser and navigate to:
```
http://127.0.0.1:5000/
```

3. Register a new user account and log in to access the system.

## Usage

### Authentication
- Register a new user account at `/register`
- Login at `/login`
- Logout at `/logout`

### Case Management
- Submit new cases at `/` (requires login)
- View all cases in the dashboard at `/dashboard` (requires login)
- View case details at `/case/<case_id>` (requires login)
- Update case status via dropdown menus

## API Endpoints

- `POST /api/update-status/<case_id>`: Update the status of a case (Pending/Open/Closed)

## Deployment

For production deployment, consider using a production-ready WSGI server like Gunicorn:

```
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Database Schema

### Users Collection
- `_id`: ObjectId (automatically generated)
- `username`: String
- `email`: String
- `password`: Hashed String
- `created_at`: DateTime
- `is_admin`: Boolean

### Cases Collection
- `_id`: ObjectId (automatically generated)
- `title`: String
- `description`: String
- `latitude`: String
- `longitude`: String
- `images`: Array of Strings (filenames)
- `status`: String (Pending/Open/Closed)
- `created_at`: DateTime
- `updated_at`: DateTime
- `created_by`: User ID Reference 