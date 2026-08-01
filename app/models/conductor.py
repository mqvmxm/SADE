#Modelo para el perfil del conductor: datos de su licencia y contacto de emergencia, 
#es independiente de Usuario para que pueda existir un conductor registrado 
#antes de tener una cuenta de acceso

from datetime import date, datetime
from app import db 

class Conductor(db.Model):
#perfil del conductor 
    __table__name = "conductores"

    id_conductor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    num_licencia = db.Column(db.String(50), unique=True, nullable=False)
    contacto_emergencia = db.Column(db.String(120), nullable=False)
    tel_emergencia = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)

#compara la fecha de vencimiento de la licencian contra la fecha actual
    def licencia_vigente(self):
    return self.fecha_vencimiento_lic >= date.today()

#indica si la licencia sigue vigente pero vence dentro de los proximos dias
    def licencia_proxima_a_vencer(self, dias=30):
        if not self.licencia_vigente():
            return False
        return (self.fecha_vencimiento_lic - date.today()).days <= dias

        