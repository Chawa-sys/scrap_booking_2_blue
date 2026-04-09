from datetime import datetime
from app import db
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from app import login_manager

bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @classmethod
    def create_user(cls, username, password, is_admin=False):
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = cls(username=username, password_hash=hashed_pw, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        return user

# Requerido por Flask-Login para cargar usuario desde la sesión
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
