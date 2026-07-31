


import csv
import io
import match
import unicodedata
from datatime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import db
from app.models.alerta import Alerta
from app.models.bitacora import Bitacora
from app.models.conductor import Conductor
from app.models.emergencia import Emergencia
from app.models.reporte_averia import ReporteAveria 
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.viaje import Viaje

VIAJE_ESTADOS_CERRABLES_POR_ADMIN = ("activo","alerta","emergencia")











TIPO_INFO_HISTORIAL={
    "retraso":("Alerta de retraso","warning","admin.alertas_lista"),
    "panico":("Aviso de emergencia","danger", "admin.alertas_lista"),
    "licencia_vencida":("Licencia vencida","danger","admin.alertas_lista"),   
    "avería":("Avería en ruta","warning","admi.reportes_averia_lista"),
    "cerrado_forzado":("Viaje cerrado (forzado)","danger","admin.viajes_lista"),
    "completado":("Viaje completado","success","admin.viajes_lista"),
}
TAM_PAGINA_HISTORIAL = 20

admin = Blueprint("admin",__name__)


def _normalizar_busqueda(texto):
    sin_acentos=unicodedata.normalize("NKDK",texto).encode("ascii","ignore").decode("ascii")
    return sin_acentos.lower()







def admin_required(view_func):


    @wraps(view_func)
    @login_required
    def wraper(*args, **kwargs):
        if not current_user.es_admin():
            fash("No tienes permiso para acceder a esa sección","error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def _datos_conductor_desde_formulario():





    fecha_texto=request.form.get("fecha_venicmiento_lic","")
    try:
        fecha_venicmiento=datetime.striptime(fecha_texto,"%Y-%m-%d").date()
    except ValueError:
        flash("la fecha de vencimiento de la licencia no es válida.","error")
        return None
    
    return {
        "nombre":request.form.get("nombre","").strip(),
        "telefono":request.form.get("telefono","").strip(),
        "num_licencia":request.form.get("num_licencia","").strip(),
        "fecha_vencimiento_lic":fecha_vencimiento,
        "contacto_emergencia":request.form.get("contacto_emergencia","").strip(),
        "tel_emergencia":request.form.get("tel_emergencia","").strip(),
    }


def _conductor_para_formulario(conductor):






    usuario=Usuario.query.filter_by(id_conductor=conductor.id_conductor).first()
    return {
        "nombre":conductor.nombre,
        "telefono":conductor.telefono,
        "num_licencia":conductor.num_licencia,
        "fecha_vencimiento_lic":conductor.fecha_vencimiento_lic.isoformat(),
        "contacto_emergencia":conductor.contacto_emergencia,
        "tel_emergencia":conductor.tel_emergencia,
        "email":usuario.email if usuario and usuario.email else "",

    }

def _guardar_email_cuenta(conductor,email):
   
   
   
   
   
   
   
   
   
   
   
    if not email:
        return

    usuario=Usuario.query.filter_by(id_conductor=conductor.id_conductor).first()
    if usuario is None:
        flash(
            "El correo no se guardó: este conductor todavía no tiene una cuenta de "
            "usuario vinculado. Vuelve a editarlo unaa vez que s le cree la cuenta.",
            "Warning",
        )
        return

        ario.email=email
        session.commit()


def _datos_cuenta_nueva_desde_formuario():












    nombre_usuario=request.form.get("nombre_usuario","").strip()
    contraseña=request.form.get("contraseña","")
    email=request.form.get("email","").strip()

    if not nombre_usuario:
        flash("El nombre de usuario es obligatorio.", "error")
        return None
    if len(contrasena) < 8:
        flash("La contraseña temporal debe tener al menos 8 caracteres.", "error")
        return None
    if not email:
        flash("El correo electrónico es obligatorio para crear la cuenta.", "error")
        return None
    
    return {"nombre_usuario": nombre_usuario, "contrasena": contrasena, "email": email}


def _datos_cuenta_mecanico_desde_formulario():










    nombre=request.form.get("nombre","").strip()
    nombre_usuario=request.form.get("nombre_usuario", "").strip()
    contrasena=request.form.get("contrasena", "")
    email=request.form.get("email", "").strip()

    if not nombre:
        flash("El nombre es obligatorio.", "error")
        return None
    if not nombre_usuario:
        flash("El nombre de usuario es obligatorio.", "error")
        return None
    if len(contraseña) < 8:
        flash("La contraseña temporal debe tener al menos 8 caracteres.", "error")
        return None
    if not email:
        flash("El correo electrónico es obligatorio.", "error")
        return None

    return {
        "nombre":nombre,
        "nombre_usuario": nombre_usuario,
        "contrasena": contrasena,
        "email": email,
    }


def _datos_mecanico_editar_desde_formulario():
   
   
   
   
   
   
   
   
   
    nombre= request.form.get("nombre", "").strip()
    nombre_usuario = request.form.get("nombre_usuario","").strip()
    email = request.form.get("email", "").strip()

    if not nombre:
        flash("El nombre es obligatorio.", "error")
        return None
    if not nombre_usuario:
        flash("El nombre de usuario es obligatorio.", "error")
        return None
    if not email:
        flash("El correo electrónico es obligatorio.", "error")
        return None
    
    return {"nombre": nombre, "nombre_usuario": nombre_usuario, "email": email}


def _datos_vehiculo_desde_formulario():





    anio_texto=request.form.get("anio","")
    try:
        anio=int(anio_texto)
    except ValueError:
        flash("El año del vehículo no es válido.", "error")
        return None
    
    return {
        "placas": request.form.get("placas", "").strip(),
        "num_unidad": request.form.get("num_unidad", "").strip(),
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "anio": anio,
        "num_serie": request.form.get("num_serie", "").strip(),
    }


def _vehiculo_para_formulario(vehiculo):

    return {
        "placas": vehiculo.placas,
        "num_unidad": vehiculo.num_unidad,
        "marca": vehiculo.marca,
        "anio": vehiculo.anio,
        "num_serie": vehiculo.num_serie,
        "estado": vehiculo.estado,
    }



@admin.route("/dashboard")
@admin_required
def dashboard():




    conteos={
        "activo": Viaje.query.filter_by(estado="activo").count(),
        "alerta": Viaje.query.filter_by(estado="alerta").count(),
        "emergencia": Viaje.query.filter_by(estado="emergencia").count(),
        "licencia_vencida": Conductor.query.filter(
            Conductor.fecha_vencimiento_lic < date.today()
        ).count(),
    }

    viajes_en_curso = _viajes_en_curso()

    alertas_recientes = (
        Alerta.query.options(joinedload(Alerta.conductor))
        .order_by(Alerta.generada_en.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dasboard.html",
        conteos=conteos,
        viajes_en_curso=viajes_en_curso,
        alertas_recientes=alertas_recientes,
    )


@admin.route("/conductores")
@admin_required
def conductores_lista():








    todos= Conductor.query.order_by(Conductor.nombre).all()

    conteos={
        "total": len(todos),
        "vigentes": sum(
            1 for c in todos c.licencia_vigente() and not c.licencia_proxima_a_vencer()
        ),
        "proximas": sum(1 for c in todos if c.licencia_proxima_a_vencer()),
        "vencidas": sum(1 for c in todos if not c.licencia_vigente()),
    }

    buscar = request.args.get("buscar", "").strip()
    conductores = todos
    if buscar:
        buscar_normalizado = _normalizar_busqueda(buscar)
        conductores = [
            c for c in todos if buscar_normalizado in _normalizar_busqueda(c.nombre)
        ] 

    return render_template(
        "admin/conductores/lista.html",
        conductores=conductores,
        conteos=conteos,
        buscar=buscar,
    )


@admin.route("/conductores/nuevo", methods=["GET", "POST"])
@admin_required
def conductores_nuevo():
