#Modelo de cuentas de acceso al sistema, cada usuario tiene un rol fijo

from datetime import datetime
from flask_login import UserMixin 
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash, generate_password_hash
from app import db 

class Usuario(db.Model, UserMixin):

    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)

    #Usado por el flujo de "olvidé mi contraseña" para ubicar la
    #cuenta y enviar el enlace de restablecimiento. Sin restricción de
    #unicidad por ahora: el esquema ya está en uso y varias cuentas viejas
    #no tendrán correo capturado todavía.
    email = db.Column(db.String(255), nullable=True)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    id_conductor = db.Column(
        db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=True
    )
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    conductor = db.relationship("Conductor", backref=db.backref("usuarios", lazy=True))

    