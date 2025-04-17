from flask_login import UserMixin
from datetime import datetime
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id', ''))
        self.username = user_data.get('username', '')
        self.email = user_data.get('email', '')
        self.password = user_data.get('password', '')
        self.created_at = user_data.get('created_at', datetime.now())
        self.is_admin = user_data.get('is_admin', False)
    
    @staticmethod
    def create_user(username, email, password_hash):
        return {
            'username': username,
            'email': email,
            'password': password_hash,
            'created_at': datetime.now(),
            'is_admin': False
        }
    
    def get_id(self):
        return self.id

class Case:
    STATUS_OPTIONS = ['Pending', 'Open', 'Closed']
    
    @staticmethod
    def create_case(title, description, latitude, longitude, images, user_id):
        return {
            'title': title,
            'description': description,
            'latitude': latitude, 
            'longitude': longitude,
            'images': images,  # Now stores GridFS IDs as strings
            'status': 'Pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'created_by': user_id
        }
    
    @staticmethod
    def format_case(case):
        """Format case for frontend display"""
        if case.get('_id'):
            case['id'] = str(case['_id'])
        
        # Format dates
        if case.get('created_at'):
            case['timestamp'] = case['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Make sure images is always a list
        if 'images' not in case:
            case['images'] = []
            
        return case 