from app import create_app, db
from app.auth.models import User
from flask import redirect


app = create_app()

# Crear tablas y usuario admin si no existe
with app.app_context():
    db.create_all()
    
    admin_username = "admin"
    admin_password = "admin123"  # Cambiar esto en producción

    if not User.query.filter_by(username=admin_username).first():
        User.create_user(username=admin_username, password=admin_password, is_admin=True)

@app.route('/')
def home_redirect():
    return redirect('/login')

if __name__ == '__main__':
    app.run()
