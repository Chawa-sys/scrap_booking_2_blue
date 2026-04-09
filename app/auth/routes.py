from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.auth.models import User
from app import db

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("Ya has iniciado sesión.", "info")
        return redirect(url_for('booking.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('booking.index'))
        else:
            flash("Credenciales inválidas.", "danger")
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin:
        flash("Solo un administrador puede crear nuevos usuarios.", "warning")
        return redirect(url_for('booking.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        User.create_user(
            username=form.username.data,
            password=form.password.data,
            is_admin=False  # Por defecto, los nuevos usuarios NO son admin
        )
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for('auth.login'))
    return render_template('registration.html', form=form)

@auth_bp.app_errorhandler(404)
def auth_page_not_found(error):
    flash("Página no encontrada. Intenta iniciar sesión nuevamente.", "warning")
    return redirect(url_for('auth.login'))

