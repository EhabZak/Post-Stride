from app.models import db, PostMedia, Post, Media, environment, SCHEMA
from sqlalchemy.sql import text


# Adds demo post media relationships
def seed_post_media():
    # Get demo post and media
    demo_post = Post.query.filter_by(caption='Just launched my new portfolio website! Check it out and let me know what you think. Link in bio! ✨ #portfolio #webdesign #launch').first()
    demo_image = Media.query.filter_by(media_type='image').first()
    demo_video = Media.query.filter_by(media_type='video').first()
    
    if demo_post and demo_image:
        post_image = PostMedia(
            post_id=demo_post.id,
            media_id=demo_image.id,
            sort_order=1
        )
        db.session.add(post_image)
    
    if demo_post and demo_video:
        post_video = PostMedia(
            post_id=demo_post.id,
            media_id=demo_video.id,
            sort_order=2
        )
        db.session.add(post_video)
    
    # Get marnie's post and media
    marnie_post = Post.query.filter_by(caption='Working on some exciting new features for our app! The team has been incredible. #teamwork #innovation #coding').first()
    marnie_image = Media.query.filter_by(user_id=2).first()  # Assuming marnie has user_id=2
    
    if marnie_post and marnie_image:
        marnie_post_image = PostMedia(
            post_id=marnie_post.id,
            media_id=marnie_image.id,
            sort_order=1
        )
        db.session.add(marnie_post_image)
    
    db.session.commit()


def undo_post_media():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.post_media RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM post_media"))
        
    db.session.commit()
