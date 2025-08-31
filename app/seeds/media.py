from app.models import db, Media, User, environment, SCHEMA
from sqlalchemy.sql import text


# Adds demo media files
def seed_media():
    # Get demo user
    demo_user = User.query.filter_by(username='Demo').first()
    
    if demo_user:
        demo_image = Media(
            user_id=demo_user.id,
            media_type='image',
            url='https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=600&fit=crop'
        )
        demo_video = Media(
            user_id=demo_user.id,
            media_type='video',
            url='https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4'
        )
        demo_gif = Media(
            user_id=demo_user.id,
            media_type='gif',
            url='https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif'
        )
        
        db.session.add(demo_image)
        db.session.add(demo_video)
        db.session.add(demo_gif)
    
    # Get marnie user
    marnie_user = User.query.filter_by(username='marnie').first()
    
    if marnie_user:
        marnie_image = Media(
            user_id=marnie_user.id,
            media_type='image',
            url='https://images.unsplash.com/photo-1494790108755-2616b612b786?w=800&h=600&fit=crop'
        )
        marnie_document = Media(
            user_id=marnie_user.id,
            media_type='document',
            url='https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
        )
        
        db.session.add(marnie_image)
        db.session.add(marnie_document)
    
    db.session.commit()


def undo_media():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.media RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM media"))
        
    db.session.commit()
