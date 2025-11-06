import os
from flask import Flask, render_template, request, session, redirect
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_login import LoginManager
from .models import db, User
from .api.user_routes import user_routes
from .api.auth_routes import auth_routes
from .api.posts_routes import posts_routes
from .api.platforms_routes import platforms_routes
from .api.user_platforms_routes import user_platforms_routes
from .api.post_platforms_routes import post_platforms_routes
from .api.media_routes import media_routes
from .api.post_media_routes import post_media_routes
from .api.health_routes import health_bp
from .api.admin_jobs_routes import admin_jobs_routes
from .seeds import seed_commands
from .config import Config
from .extensions.queue import init_redis

#! //// ///////////////////////////////////////////////////////////////////////////
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, conn_record):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass

#! Flask App ///////////////////////////////////////////////////////////////////////////
app = Flask(__name__, static_folder='../react-app/build', static_url_path='/')

#! Setup login manager ///////////////////////////////////////////////////////////////////////////
login = LoginManager(app)
login.login_view = 'auth.unauthorized'

#! User Loader ///////////////////////////////////////////////////////////////////////////
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

#! Seed Commands ///////////////////////////////////////////////////////////////////////////
# Tell flask about our seed commands
app.cli.add_command(seed_commands)
#1-Blueprints ///////////////////////////////////////////////////////////////////////////
app.config.from_object(Config)
app.register_blueprint(user_routes, url_prefix='/api/users')
app.register_blueprint(auth_routes, url_prefix='/api/auth')
app.register_blueprint(posts_routes, url_prefix='/api/posts')
app.register_blueprint(platforms_routes, url_prefix='/api/platforms')
app.register_blueprint(user_platforms_routes, url_prefix='/api/user-platforms')
app.register_blueprint(post_platforms_routes, url_prefix='/api')
app.register_blueprint(media_routes, url_prefix='/api/media')
app.register_blueprint(post_media_routes, url_prefix='/api')
app.register_blueprint(health_bp)
app.register_blueprint(admin_jobs_routes)
db.init_app(app)
Migrate(app, db)

# Add Redis + Queue ///////////////////////////////////////////////////////////////////////////
#! This set up Avoids crashes when config isn’t loaded the way you expect (tests, scripts, different envs). 
app.config.setdefault("REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

redis_url = app.config.get("REDIS_URL")
if not redis_url:
    raise RuntimeError("REDIS_URL not configured")
init_redis(redis_url)

# Application Security ///////////////////////////////////////////////////////////////////////////
CORS(app)

# Since we are deploying with Docker and Flask,
# we won't be using a buildpack when we deploy to Heroku.
# Therefore, we need to make sure that in production any
# request made over http is redirected to https.
# Well.........
#! HTTPS Redirect ///////////////////////////////////////////////////////////////////////////
@app.before_request
def https_redirect():
    if os.environ.get('FLASK_ENV') == 'production':
        if request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

#! CSRF Token ///////////////////////////////////////////////////////////////////////////
@app.after_request
def inject_csrf_token(response):
    response.set_cookie(
        'csrf_token',
        generate_csrf(),
        secure=True if os.environ.get('FLASK_ENV') == 'production' else False,
        samesite='Strict' if os.environ.get(
            'FLASK_ENV') == 'production' else None,
        httponly=True)
    return response

#! API Documentation ///////////////////////////////////////////////////////////////////////////
@app.route("/api/docs")
def api_help():
    """
    Returns all API routes and their doc strings
    """
    acceptable_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    route_list = { rule.rule: [[ method for method in rule.methods if method in acceptable_methods ],
                    app.view_functions[rule.endpoint].__doc__ ]
                    for rule in app.url_map.iter_rules() if rule.endpoint != 'static' }
    return route_list

#! React Root ///////////////////////////////////////////////////////////////////////////
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def react_root(path):
    """
    This route will direct to the public directory in our
    react builds in the production environment for favicon
    or index.html requests
    """
    if path == 'favicon.ico':
        return app.send_from_directory('public', 'favicon.ico')
    return app.send_static_file('index.html')

#! Error Handler ///////////////////////////////////////////////////////////////////////////
@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')