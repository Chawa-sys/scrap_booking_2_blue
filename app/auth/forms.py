from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.auth.models import User

# Validador personalizado: evita nombres de usuario duplicados
def username_exists(form, field):
    if User.query.filter_by(username=field.data).first():
        raise ValidationError("Este nombre de usuario ya está registrado.")

class RegistrationForm(FlaskForm):
    username = StringField(
        'Nombre de usuario',
        validators=[DataRequired(), Length(min=3, max=20), username_exists]
    )
    password = PasswordField(
        'Contraseña',
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        'Confirmar contraseña',
        validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')]
    )
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

