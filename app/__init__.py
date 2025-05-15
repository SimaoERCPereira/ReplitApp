from flask import Flask
from .extensions import db, login_manager, cache, limiter, talisman
from .routes.main import main_bp
from .routes.auth import auth_bp
from .routes.api import api_bp
import os

def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "teamtalk.db")
    db_url = os.getenv("DATABASE_URL") or f"sqlite:///{db_path}"
    # Use SimpleCache on Replit, otherwise Redis
    if os.getenv("REPLIT_DB_URL") or os.getenv("REPL_OWNER"):
        cache_type = 'SimpleCache'
        cache_redis_url = None
    else:
        cache_type = 'redis'
        cache_redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(24)),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE=cache_type,
        CACHE_REDIS_URL=cache_redis_url,
        CACHE_DEFAULT_TIMEOUT=300
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
        
    cache.init_app(app)
    limiter.init_app(app)
    # Only enforce HTTPS in production
    if os.getenv("FLASK_ENV") == "production":
        talisman.init_app(app)
    else:
        talisman.init_app(app, force_https=False)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    return app 