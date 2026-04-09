from flask import Blueprint

booking_bp = Blueprint('booking', __name__, template_folder='templates/booking', static_folder='static/js')

from app.booking import routes
