#Modelo central de monitoreo de rutas: un viaje une un conductor con un vehiculo
#entre un origen y un destino, con ETA y seguimiento de estado

from datetime import datetime
from sqlalchemy import CheckConstraint
from app import db 

#hora_salida se registra al hacer el check_in y hora_llegada al confirmar llegada
class Viaje(db.Model):
    
    __tablename__ = "viajes"

    id_viaje = db.Column(db.Integer, primary_key=True)
    id_conductor = db.Column(
        db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=False
    )
    id_vehiculo = db.Column(
        db.Integer, db.ForeignKey("vehiculo.id_vehiculo"), nullable=False
    )
    origen = db.Column(db.String(120), nullable=False)
    destino = db.Column(db.String(120), nullable=False)
    hora_salida = db.column(db.DateTime, nullable=False)
    eta = db.Column(db.DateTime, nullable=False)
    hora_llegada = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    conductor = db.relationship("Conductor", backref=db.backref("viajes", lazy=True))
    vehiculo = db.relationship("Vehiculo", backref=db.backref("viajes", lazy=True))

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo', 'completado', 'alerta', 'emergencia', 'cerrado_admin')",
            name="ck_viajes_estado",
        ),
    )