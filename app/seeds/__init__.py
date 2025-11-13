from flask.cli import AppGroup
from .users import seed_users, undo_users
from .social_platforms import seed_social_platforms, undo_social_platforms
from .user_platforms import seed_user_platforms, undo_user_platforms
from .media import seed_media, undo_media
from .posts import seed_posts, undo_posts
from .post_platforms import seed_post_platforms, undo_post_platforms
from .post_media import seed_post_media, undo_post_media

from app.models.db import db, environment, SCHEMA

# Creates a seed group to hold our commands
# So we can type `flask seed --help`
seed_commands = AppGroup('seed')


# Creates the `flask seed all` command
@seed_commands.command('all')
def seed():
    if environment == 'production':
        # Before seeding in production, you want to run the seed undo 
        # command, which will  truncate all tables prefixed with 
        # the schema name (see comment in users.py undo_users function).
        # Make sure to add all your other model's undo functions below
        undo_post_media()
        undo_post_platforms()
        undo_posts()
        undo_media()
        undo_user_platforms()
        undo_social_platforms()
        undo_users()
    
    # Seed in order of dependencies
    seed_users()
    seed_social_platforms()
    seed_user_platforms()
    seed_media()
    seed_posts()
    seed_post_platforms()
    seed_post_media()


# Creates the `flask seed undo` command
@seed_commands.command('undo')
def undo():
    # Undo in reverse order of dependencies
    undo_post_media()
    undo_post_platforms()
    undo_posts()
    undo_media()
    undo_user_platforms()
    undo_social_platforms()
    undo_users()