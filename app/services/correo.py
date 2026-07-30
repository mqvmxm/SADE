# Servicio de envío de correo para el flujo de "olvidé mi contraseña" (RF-1).
# Con EMAIL_SIMULATE=True (default, ver config.py) no se conecta a ningún
# servidor SMTP real: solo se imprime el envío simulado, exactamente la
# misma filosofía que app/services/notificaciones.py usa con Twilio, para
# poder desarrollar y probar el flujo completo sin credenciales de correo.
# La simulación reemplaza únicamente la conexión SMTP, nunca la validación
# del destinatario: un correo vacío o con formato inválido debe fallar igual
# en modo simulado que en modo real.

import re # para validar el formato del correo
import smtplib # para enviar correos reales a traves de un servidor smtp
from email.message import EmailMessage #para crear el mensaje de correo real que se envia a traves del servidor smtp

from flask import current_app #  es para acceder a las variables de configuracion de la app

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$") # el formato del correo, debe tener un @ y un . despues del @, y no puede tener espacios ni caracteres especiales


def _email_valido(correo): #si el formato del correo, si es valido regresa True y si no es valido regresa False
    return bool(correo) and bool(_PATRON_EMAIL.match(correo))


def _simulacion_activa(): 
    return current_app.config.get("EMAIL_SIMULATE", True)


def enviar_correo(destinatario, asunto, cuerpo):
    """Envía un correo (usado por RF-1: recuperación de contraseña).

    Devuelve (exito: bool, error: str | None), igual que
    enviar_whatsapp()/enviar_sms() en notificaciones.py. El destinatario se
    valida ANTES de decidir si simular o conectar de verdad: si el correo no
    tiene formato válido, la función falla con "correo inválido o no
    configurado" sin importar el valor de EMAIL_SIMULATE.
    """
    if not _email_valido(destinatario):
        return False, "correo inválido o no configurado"

    if _simulacion_activa():
        print(
            "[SIMULADO][Correo] "
            f"Para: {destinatario} | Asunto: {asunto}\n{cuerpo}"
        )
        return True, None

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = current_app.config.get("EMAIL_FROM", "")
    mensaje["To"] = destinatario
    mensaje.set_content(cuerpo)

    host = current_app.config.get("EMAIL_HOST", "")
    puerto = int(current_app.config.get("EMAIL_PORT", 587))
    usuario_smtp = current_app.config.get("EMAIL_USER", "")
    password_smtp = current_app.config.get("EMAIL_PASSWORD", "")

    try: # si hay un error al enviar el correo real, regresa False y el error
        with smtplib.SMTP(host, puerto, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(usuario_smtp, password_smtp)
            servidor.send_message(mensaje)
        return True, None
    except smtplib.SMTPException as error: # errores de SMTP (autenticación, destinatario rechazado, etc.) heredan de SMTPException
        return False, str(error)
    except OSError as error: # errores de conexión (host inalcanzable, timeout, DNS) no heredan de SMTPException, por eso se captura aparte
        return False, str(error)
