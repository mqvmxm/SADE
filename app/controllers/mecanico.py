


from datetime import datetime
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, requesto, url_for
from flask_login import current_user, login_required

from app import db
from app.models.bitacora import Bitacora
from app.models.reporte_averia import ReporteAveria
from app.models.vehiculo import Vehiculo
from app.models.viaje import Viaje

mecanico = Blueprint("mecanico",__name__)

VIAJE_ESTADOS_CON_VEHICULO_EN_USO = ("activo", "alerta", "emergencia")


def mecanico_required (view_func):


    @wraps (view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.es_mecanico():
            flash("No tienes permiso para acceder a esa sección","error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


    def _viaje_activo_de(id_vehiculo):

        return Viaje.query.filter(
            Viaje.id_vehiculo == id_vehiculo,
            Viaje.estado.in_(VIAJE_ESTADOS_CON_VEHICULO_EN_USO),
        ).first()
    

    @mecanico.route("/dashboard")
    @mecanico_required
    def dashboard ():

        return render_template("mecanico/dashboard.html")


    @mecanico.route("/vehiculos")
    @mecanico_required
    def vehiculos_lista():



        viajes_en_uso=Viaje.query.filter(
            Viaje.estado.in_(VIAJE_ESTADOS_CON_VEHICULO_EN_USO)
        ).all()
        vehiculos_con_viaje_activo = {viaje.ud_vehiculo for viaje in viajes_en_uso}

        return render_template(
            "mecanico/vehiculos/lista.html",
            vehiculos=vehiculos,
            vehiculos_con_viaje_activo=vehiculos_con_viaje_activo,
        )


    @mecanico.route("/vehiculos/<int:id_vehiculo>/estado", methods=["POST"])
    @mecanico_required
    def vehiculos_cambiar_estado(id_vehiculo):






        vehiculo=Vehiculo.query.get_or_404(id_vehiculo)

        if vehiculo.estado == "en_ruta":
            fash(
                "No se puede modificar el estado de un vehiculo en ruta; "
                "se actualizará automáticamente al finalizar el viaje activo.",
                "error",
            )
            return redirect(url_for("mecanico.vehiculos_lista"))
    
        nuevo_estado = request.form.get("estado", "")
        if nuevo_estado not in ("disponible", "en_taller"):
            flash("El estado seleccionado no es válido." "error")
            return redirect(url_for("mecanico.vahiculos_lista"))

        estado_anterior = vehiculo.estado
        vehiculo.estado = nuevo_estado

        motivo= request.form.get("motivo", "").strip()
        descripcion=(
            f"Vehiculo '{vehiculo.placas}' cambiado de '{estado_anterior}' a"
            f"'{nuevo_estado}' por {current_user.nombre}."
        )
        if motivo:
            descripcion += f" Motivo: {motivo}."

        bitacora = Bitacora(
            id_usuario=current_user.id_usuario,
            accion="cambio_esado_vehiculo",
            descripcion=descripcion,
            tabla_afectada="vehiculos",
            registro_id=vehiculo.id_vehiculo,
        )
        db.session.add(bitacora)
        db.session.commit()

        flash(f"Vehiculo '{vehiculo.placas}' actualizado a '{nuevo_estado}'", "success")
        return redirect(url_for("mecanico.vehiculos_lista"))

    
    @mecanico.route("/vehiculos/<int:id_vehiculo>/reportar-averia", methods=["GET", "POST"])
    @mecanico_required

def vehiculos_reportar_averia(id_vehiculo):





    vehiculo = Vehiculo.query.get_or_404(id_vehiculo)
    viaje_activo = _viaje_activo_de(id_vehiculo)

    if viaje_activo is None:
        flash(
            f"El vehículo '{vehiculo.placas}' no tiene un viaje en curso; "
            "no se puede registrar un reporte de avería.",
            "error",
        )
        return redirect (url_for("mecanico.vehiculos_lista"))

    if request.method == "POST":
        descripcion = request.form.get ("descripcion", "").strip()
        if not descripcion:
            flash("Debes describir la falla del vehículo.", "error")
            return redirect(
                url_for("mecanico.vehiculos_reportar_avería", id_vehiculo=id_vehiculo)
            )