from flask import Flask
from flask_session import Session  # NUEVO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirige si no está logueado


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    #configurar sesiones
    app.secret_key = app.config['SECRET_KEY']  # Cámbiala en producción - ya esta cambiada
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    Session(app)  # ← NUEVO

    # Registro de blueprints
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.booking import booking_bp
    app.register_blueprint(booking_bp)
    
    from app.booking import models  # 👈 Esto es necesario para que SQLAlchemy registre las nuevas tablas

    if app.config['DEBUG']:
        with app.app_context():
            db.create_all()
    
    return app
