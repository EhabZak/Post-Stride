from app.models import db, PostPlatform, Post, SocialPlatform, environment, SCHEMA
from sqlalchemy.sql import text
from datetime import datetime


# Adds demo post platforms
def seed_post_platforms():
    # Get demo post and platforms
    demo_post = Post.query.filter_by(caption='Just launched my new portfolio website! Check it out and let me know what you think. Link in bio! ✨ #portfolio #webdesign #launch').first()
    linkedin = SocialPlatform.query.filter_by(name='LinkedIn').first()
    instagram = SocialPlatform.query.filter_by(name='Instagram').first()
    
    if demo_post and linkedin:
        linkedin_post = PostPlatform(
            post_id=demo_post.id,
            platform_id=linkedin.id,
            platform_caption='Just launched my new portfolio website! Check it out and let me know what you think. Link in bio! ✨ #portfolio #webdesign #launch #professional #career',
            media_urls=[{
                'url': 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=600&fit=crop',
                'type': 'image',
                'alt': 'Portfolio website screenshot'
            }],
            platform_post_id='linkedin_post_12345',
            status='published',
            published_at=datetime.utcnow()
        )
        db.session.add(linkedin_post)
    
    if demo_post and instagram:
        instagram_post = PostPlatform(
            post_id=demo_post.id,
            platform_id=instagram.id,
            platform_caption='Just launched my new portfolio website! ✨ Check it out and let me know what you think. Link in bio! #portfolio #webdesign #launch #creative #design',
            media_urls=[{
                'url': 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=600&fit=crop',
                'type': 'image',
                'alt': 'Portfolio website screenshot'
            }],
            platform_post_id='instagram_post_67890',
            status='published',
            published_at=datetime.utcnow()
        )
        db.session.add(instagram_post)
    
    # Get marnie's post
    marnie_post = Post.query.filter_by(caption='Working on some exciting new features for our app! The team has been incredible. #teamwork #innovation #coding').first()
    
    if marnie_post and linkedin:
        marnie_linkedin = PostPlatform(
            post_id=marnie_post.id,
            platform_id=linkedin.id,
            platform_caption='Working on some exciting new features for our app! The team has been incredible. #teamwork #innovation #coding #tech #development',
            status='published',
            published_at=datetime.utcnow()
        )
        db.session.add(marnie_linkedin)
    
    db.session.commit()


def undo_post_platforms():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.post_platforms RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM post_platforms"))
        
    db.session.commit()
