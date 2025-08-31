"""
Database migration script to create all tables for Post_Stride application
Run this script to set up your database schema
"""

from app.models import db, User, SocialPlatform, UserPlatform, Post, PostPlatform, Media, PostMedia
from app import create_app

def create_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ All tables created successfully!")
        
        # Create some default social platforms
        platforms = [
            {'name': 'LinkedIn', 'api_base_url': 'https://api.linkedin.com/v2'},
            {'name': 'Instagram', 'api_base_url': 'https://graph.instagram.com/v12.0'},
            {'name': 'X (Twitter)', 'api_base_url': 'https://api.twitter.com/2'},
            {'name': 'TikTok', 'api_base_url': 'https://open.tiktokapis.com/v2'},
            {'name': 'Facebook', 'api_base_url': 'https://graph.facebook.com/v18.0'},
        ]
        
        for platform_data in platforms:
            existing = SocialPlatform.query.filter_by(name=platform_data['name']).first()
            if not existing:
                platform = SocialPlatform(**platform_data)
                db.session.add(platform)
                print(f"✅ Added platform: {platform_data['name']}")
        
        db.session.commit()
        print("✅ Default social platforms created!")

if __name__ == '__main__':
    create_tables()
