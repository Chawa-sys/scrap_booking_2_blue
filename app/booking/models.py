from datetime import datetime
from app import db
from app.auth.models import User  # al inicio del archivo

class Busqueda(db.Model):
    __tablename__ = 'busquedas'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tipo = db.Column(db.String(30), nullable=False)  # 'completa', 'por_dia', 'precios_por_dia'
    destino = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    nombre_hotel = db.Column(db.String(150))  # Solo si aplica para 'precios_por_dia'
    es_guardado = db.Column(db.Boolean, default=False)  # False = historial temporal, True = guardado permanente
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resultados = db.relationship('Resultado', backref='busqueda', cascade="all, delete-orphan")
    usuario = db.relationship("User", backref="busquedas")
    def __repr__(self):
        return f'<Busqueda {self.tipo} - {self.destino}>'

class Resultado(db.Model):
    __tablename__ = 'resultados'

    id = db.Column(db.Integer, primary_key=True)
    busqueda_id = db.Column(db.Integer, db.ForeignKey('busquedas.id'), nullable=False, index=True)
    datos = db.Column(db.JSON, nullable=False)  # Resultado completo en formato JSON
    fecha_resultado = db.Column(db.Date)  # Aplica solo para resultados por día
    posicion = db.Column(db.Integer)  # Aplica si hay orden por día

    def __repr__(self):
        return f'<Resultado de búsqueda {self.busqueda_id}>'
