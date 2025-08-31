from app.models import db, Post, User, environment, SCHEMA
from sqlalchemy.sql import text
from datetime import datetime, timedelta


# Adds demo posts
def seed_posts():
    # Get demo user
    demo_user = User.query.filter_by(username='Demo').first()
    
    if demo_user:
        # Draft post
        draft_post = Post(
            user_id=demo_user.id,
            caption='Just finished an amazing project! Can\'t wait to share the details with you all. #coding #webdev #excited',
            status='draft'
        )
        
        # Scheduled post
        scheduled_post = Post(
            user_id=demo_user.id,
            caption='Big announcement coming tomorrow! Stay tuned for something special. 🚀 #announcement #excited',
            scheduled_time=datetime.utcnow() + timedelta(days=1),
            status='scheduled'
        )
        
        # Published post
        published_post = Post(
            user_id=demo_user.id,
            caption='Just launched my new portfolio website! Check it out and let me know what you think. Link in bio! ✨ #portfolio #webdesign #launch',
            status='published'
        )
        
        db.session.add(draft_post)
        db.session.add(scheduled_post)
        db.session.add(published_post)
    
    # Get marnie user
    marnie_user = User.query.filter_by(username='marnie').first()
    
    if marnie_user:
        # Marnie's post
        marnie_post = Post(
            user_id=marnie_user.id,
            caption='Working on some exciting new features for our app! The team has been incredible. #teamwork #innovation #coding',
            status='published'
        )
        
        db.session.add(marnie_post)
    
    db.session.commit()


def undo_posts():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.posts RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM posts"))
        
    db.session.commit()
