from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class BookingForm(FlaskForm):
    destino = StringField('Destino', validators=[DataRequired()])
    fecha_inicio = DateField('Fecha de inicio', validators=[DataRequired()])
    fecha_fin = DateField('Fecha de fin', validators=[DataRequired()])
    cantidad_hoteles = IntegerField('Cantidad de hoteles', default=20, validators=[NumberRange(min=1, max=100)])
    submit = SubmitField('Buscar')
