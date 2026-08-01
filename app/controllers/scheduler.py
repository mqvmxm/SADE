



from datetime import datetime

from flask import current_app

from app import db
from app.models.alerta import Alerta
from app.models.bitacora import Bitacora
from app.models.usuario import Usuario
from app.models.viaje import Viaje
from app.services.notificaciones import(
    enviar_sms,
    enviar_whatsapp,
    generar_mensaje_retraso,
    quitar_codigos_ansi,
)


def revisar_viajes_activos():










    alertas_nuevas=[]

    try: 
        ahora=datetime.now()
        viajes_activos = Viaje.query.filter_by(estado="activo").all()

        for viaje in viajes_activos:
            if ahora <= viaje.eta:
                continue
            
            ya_tiene_alerta_retraso = Alerta.query.filter_by(
                id_viaje=viaje.id_viaje, tipo="retraso"
            ).first()
            if ya_tiene_alerta_retraso is not None:
                continue

            alerta=Alerta(
                id_viaje=viaje.id_viaje,
                id_conductor=viaje.id_conductor,
                tipo="retraso",
                prioridad=2,
                mensaje=(
                    f"Conductor {viaje.conductor.nombre} superó su ETA "
                    "sin confirmar llegada"
            ),
            atendida=False,
            )
            db.session.add(alerta)
            viaje.estado="alerta"
            alertas_nuevas.append((alerta,viaje))
        



        db.session.commit()
    except Exception as error:
        db.session.rollback()
        print(f"[scheduler] Error al revisar viajes activos: {error}")
        return

    for alerta, viaje in alertas_nuevas:
        _notificar_retraso (alerta,viaje)


def _notificar_retraso(alerta, viaje):









    try: 
        conductor=viaje.conductor
        mensaje = generar_mensaje_retraso(
            conductor.nombre, viaje.origen, viaje.destino, viaje.eta
        )
        numero_conductor = conductor.tel_emergencia
        numero_admin = current_app.config.get("ADMIN_PHONE_NUMBER","")

        exito_ws_conductor, error_ws_conductor=enviar_whatsapp(numero_conductor,mensaje)
        exito_ws_admin, error_ws_admin=enviar_whatsapp(numero_admin,mensaje)
        exito_sms_conductor,error_sms_conductor=enviar_sms(numero_conductor,mensaje)
        exito_sms_admin, error_sms_admin=enviar_sms(numero_admin,mensaje)







        usuario_conductor=Usuario.query.filter_by(
            id_conductor=viaje.id_conductor
        ).first()
        if usuario_conductor is not None:
            _registrar_bitacora_retraso(usuario_conductor,alerta,"WhatsApp","contacto de emergencia", exito_ws_conductor, error_ws_conductor)
            _registrar_bitacora_retraso(usuario_conductor,alerta,"WhatsApp","administrador", exito_ws_admin, error_ws_admin)
            _registrar_bitacora_retraso(usuario_conductor,alerta,"SMS","contacto de emergencia",exito_sms_conductor,error_sms_conductor)
            _registrar_bitacora_retraso(usuario_conductor,alerta,"SMS","administrador",exito_sms_admin,error_sms_admin)

            db.session.commit()
    except Exception as error:
        db.session.rollback()
        print(f"[scheduler] Error al notificar retraso del viaje {viaje.id_viaje}: {error}")

    
def _registrar_bitacora_retraso(usuario,alerta,canal,destinatario,exito,error):
    
    error_limpio=quitar_codigos_ansi(error)
    resultado="enviado" if exito else f"fallido ({error_limpio})" if error_limpio else "fallido"
    bitacora=Bitacora(
        id_usuario=usuario.id_usuario,
        accion="envio_notificación_retraso",
        descripción=f"{canal} a {destinatario}: {resultado}.",
        tabla_afectada="alertas",
        registro_id=alerta.id_alerta,
    )
    db.session.add(bitacora)