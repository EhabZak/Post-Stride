from app.models import db, SocialPlatform, environment, SCHEMA
from sqlalchemy.sql import text


# Adds demo social platforms
def seed_social_platforms():
    instagram = SocialPlatform(
        name='Instagram',
        api_base_url='https://graph.instagram.com/v12.0'
    )
    tiktok = SocialPlatform(
        name='TikTok',
        api_base_url='https://open.tiktokapis.com/v2'
    )
    x_twitter = SocialPlatform(
        name='X',
        api_base_url='https://api.twitter.com/2'
    )
    bluesky = SocialPlatform(
        name='Blue Sky',
        api_base_url='https://bsky.social/xrpc'
    )
    linkedin = SocialPlatform(
        name='LinkedIn',
        api_base_url='https://api.linkedin.com/v2'
    )
    facebook = SocialPlatform(
        name='Facebook',
        api_base_url='https://graph.facebook.com/v18.0'
    )
    youtube = SocialPlatform(
        name='YouTube',
        api_base_url='https://www.googleapis.com/youtube/v3'
    )
    pinterest = SocialPlatform(
        name='Pinterest',
        api_base_url='https://api.pinterest.com/v5'
    )
    threads = SocialPlatform(
        name='Threads',
        api_base_url='https://graph.instagram.com/v12.0'  # Threads uses Instagram's API
    )

    db.session.add(instagram)
    db.session.add(tiktok)
    db.session.add(x_twitter)
    db.session.add(bluesky)
    db.session.add(linkedin)
    db.session.add(facebook)
    db.session.add(youtube)
    db.session.add(pinterest)
    db.session.add(threads)
    db.session.commit()


def undo_social_platforms():
    if environment == "production":
        db.session.execute(f"TRUNCATE table {SCHEMA}.social_platforms RESTART IDENTITY CASCADE;")
    else:
        db.session.execute(text("DELETE FROM social_platforms"))
        
    db.session.commit()
