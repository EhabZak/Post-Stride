from app.models import db, UserPlatform, User, SocialPlatform, environment, SCHEMA
from sqlalchemy.sql import text
from datetime import datetime, timedelta


# Adds demo user platform connections
def seed_user_platforms():
    # Get demo user and platforms
    demo_user = User.query.filter_by(username='Demo').first()
    linkedin = SocialPlatform.query.filter_by(name='LinkedIn').first()
    instagram = SocialPlatform.query.filter_by(name='Instagram').first()
    x_twitter = SocialPlatform.query.filter_by(name='X').first()
    
    if demo_user and linkedin:
        demo_linkedin = UserPlatform(
            user_id=demo_user.id,
            platform_id=linkedin.id,
            platform_user_id='demo_linkedin_123',
            access_token='demo_access_token_linkedin',
            refresh_token='demo_refresh_token_linkedin',
            token_expiry=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(demo_linkedin)
    
    if demo_user and instagram:
        demo_instagram = UserPlatform(
            user_id=demo_user.id,
            platform_id=instagram.id,
            platform_user_id='demo_instagram_456',
            access_token='demo_access_token_instagram',
            refresh_token='demo_refresh_token_instagram',
            token_expiry=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(demo_instagram)
    
    if demo_user and x_twitter:
        demo_x_twitter = UserPlatform(
            user_id=demo_user.id,
            platform_id=x_twitter.id,
            platform_user_id='demo_x_twitter_789',
            access_token='demo_access_token_x_twitter',
            refresh_token='demo_refresh_token_x_twitter',
            token_expiry=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(demo_x_twitter)
    
    db.session.commit()


def undo_user_platforms():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.user_platforms RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM user_platforms"))
        
    db.session.commit()
