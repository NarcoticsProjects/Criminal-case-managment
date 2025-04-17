"""
Migration script to move existing images from the filesystem to MongoDB GridFS.
Run this script once to migrate images from local storage to MongoDB.
"""

import os
import io
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from gridfs import GridFS
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime
import glob

# Load environment variables
load_dotenv()

# MongoDB setup
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
db = client['criminal_case_db']
cases_collection = db['cases']

# Initialize GridFS
fs = GridFS(db, collection='images')

# Path to local images
UPLOAD_FOLDER = 'static/uploads'

def migrate_images():
    """Migrate all images from local storage to GridFS"""
    
    print("Starting image migration...")
    total_images = 0
    total_cases_updated = 0
    migration_failures = 0
    
    # Get all cases
    cases = list(cases_collection.find())
    
    for case in cases:
        case_id = case.get('_id')
        old_images = case.get('images', [])
        
        if not old_images:
            continue
        
        new_images = []
        
        for old_image in old_images:
            image_path = os.path.join(UPLOAD_FOLDER, old_image)
            
            # Check if the file exists
            if not os.path.exists(image_path):
                print(f"Warning: Image {image_path} not found, skipping")
                migration_failures += 1
                continue
                
            try:
                # Open and process the image
                with Image.open(image_path) as img:
                    # Convert to RGB if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize if too large (optional)
                    max_size = (1200, 1200)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    # Save to buffer
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85, optimize=True)
                    buffer.seek(0)
                    
                    # Store in GridFS
                    image_id = fs.put(
                        buffer,
                        filename=old_image,
                        contentType='image/jpeg',
                        metadata={
                            'migrated_at': datetime.now(),
                            'original_path': image_path,
                            'case_id': str(case_id)
                        }
                    )
                    
                    # Add the new image ID to the list
                    new_images.append(str(image_id))
                    total_images += 1
                    
                    print(f"Migrated image: {old_image} -> {image_id}")
                    
            except Exception as e:
                print(f"Error migrating image {old_image}: {str(e)}")
                migration_failures += 1
        
        # Update the case with new image IDs
        if new_images:
            cases_collection.update_one(
                {'_id': case_id},
                {'$set': {'images': new_images}}
            )
            total_cases_updated += 1
    
    print(f"\nMigration complete!")
    print(f"Total images migrated: {total_images}")
    print(f"Total cases updated: {total_cases_updated}")
    print(f"Migration failures: {migration_failures}")
    
    # Optional: suggest cleanup of local files after confirmation
    print("\nYou can now manually delete the files in the static/uploads directory")
    print("once you've confirmed the migration was successful.")

if __name__ == "__main__":
    migrate_images() 