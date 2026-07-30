# Servicio de notificaciones de emergencia por WhatsApp y SMS vía Twilio
# (RF-4.3: alertas WhatsApp; RF-4.4: SMS de respaldo; RF-4.5: mensaje con ubicación).
# Con SIMULATE_TWILIO=True (default, ver config.py) no se llama a la API
# real: solo se imprime el envío simulado, para poder desarrollar y probar
# el flujo completo sin credenciales de Twilio. La simulación reemplaza
# únicamente la llamada al canal (WhatsApp/SMS), nunca la validación del
# número de destino: un número vacío o inválido debe fallar igual en modo
# simulado que en modo real.

import re ##limpia el texto y deja solo numeros de telefono

from flask import current_app ## acceder a las variables de configuracion de la app
from twilio.base.exceptions import TwilioRestException ##es para enviar mensajes  reales de texto  y whatsapp a traves de la api de twilio 
from twilio.rest import Client 


def normalizar_numero(numero): ## es un formato estandarizado para numeros de telefono mexicanos (que salgan =527751652306)
    """Normaliza un número de teléfono mexicano a formato E.164 (+52...).

    Acepta números con o sin lada de país, con espacios, guiones o
    paréntesis. No agrega el prefijo 'whatsapp:' — eso lo hace
    enviar_whatsapp() únicamente para ese canal.

    Devuelve None (no lanza excepción) si `numero` es None, cadena vacía, o
    no tiene exactamente 10 dígitos de número local mexicano después de
    limpiar todo lo que no sea dígito y quitar la lada de país si venía
    incluida. Se eligió None en vez de una excepción porque
    enviar_whatsapp()/enviar_sms() ya reportan sus fallas como tupla
    (exito, error), y así todo el módulo usa un solo mecanismo de error.
    """
    if not numero:## si no manda nada y llega vacio manda un none
        return None

    solo_digitos = re.sub(r"\D", "", numero) ##quita lo que no sean numeros 

    if len(solo_digitos) == 12 and solo_digitos.startswith("52"): ## quita la lada para quedarse con 10 digitos
        solo_digitos = solo_digitos[2:]
    elif len(solo_digitos) == 13 and solo_digitos.startswith("521"): 
        solo_digitos = solo_digitos[3:]

    if len(solo_digitos) != 10: ## si al limpiar el numero no quedan 10 digitos manda un none
        return None

    return f"+52{solo_digitos}" ## si mide 10 digitos regresa el numero con la lada y los 10 digitos del numero


def generar_mensaje_emergencia(nombre_conductor, latitud, longitud): ##crea el mensaje de emergencia que se envia por whatsapp o sms
    """Arma el texto de la notificación: conductor, tipo de aviso y ubicación (RF-4.5).

    latitud/longitud pueden venir en None cuando el conductor activó el
    aviso sin que el navegador lograra obtener su ubicación: en ese caso se
    avisa que la ubicación no está disponible en vez de armar un link de
    Google Maps roto con "None, None".
    """
    if latitud is None or longitud is None: 
        ubicacion = "Ubicación no disponible (el conductor no pudo compartir su ubicación)." ## si no se puede obtener la ubicacion manda un mensaje de que no se pudo obtener la ubicacion
    else:
        ubicacion = f"Ubicación: https://maps.google.com/?q={latitud},{longitud}" ## genera un link de google maps con la ubicacion del conductor

    return f"[S.A.D.E.] Aviso silencioso activado por {nombre_conductor}. {ubicacion}" ## regresa el mensaje de emergencia que se envia por whatsapp o sms


def _simulacion_activa(): ## devuelve True si la configuracion SIMULATE_TWILIO es True
    return current_app.config.get("SIMULATE_TWILIO", True)


def _cliente_twilio(): ## crea un cliente de twilio con las credenciales de la app
    account_sid = current_app.config.get("TWILIO_ACCOUNT_SID", "")
    auth_token = current_app.config.get("TWILIO_AUTH_TOKEN", "")
    return Client(account_sid, auth_token)


def enviar_whatsapp(numero_destino, mensaje): ## envía un WhatsApp 
    """Envía un WhatsApp vía Twilio (RF-4.3).

    Devuelve (exito: bool, error: str | None). El número se valida ANTES de
    decidir si simular o llamar a la API real: si normalizar_numero()
    devuelve None, la función falla con "número inválido o no configurado"
    sin importar el valor de SIMULATE_TWILIO. En modo simulado (con número
    válido) siempre devuelve éxito sin llamar a la API real.
    """
    numero_e164 = normalizar_numero(numero_destino) ## valida el numero de telefono, si es valido le agrega el +52 y si no es valido regresa None
    if numero_e164 is None:
        return False, "número inválido o no configurado"

    destino = f"whatsapp:{numero_e164}"

    if _simulacion_activa():
        print(f"[SIMULADO][WhatsApp] Para {destino}: {mensaje}")
        return True, None

    remitente = current_app.config.get("TWILIO_WHATSAPP_FROM", "")
    try:
        _cliente_twilio().messages.create(from_=remitente, to=destino, body=mensaje) ## envia el mensaje de whatsapp real a traves de twilio
        return True, None
    except TwilioRestException as error:
        return False, str(error)


def enviar_sms(numero_destino, mensaje):
    """Envía un SMS de respaldo vía Twilio (RF-4.4).

    Devuelve (exito: bool, error: str | None). El número se valida ANTES de
    decidir si simular o llamar a la API real: si normalizar_numero()
    devuelve None, la función falla con "número inválido o no configurado"
    sin importar el valor de SIMULATE_TWILIO. En modo simulado (con número
    válido) siempre devuelve éxito sin llamar a la API real.
    """
    numero_e164 = normalizar_numero(numero_destino) ## valida el numero de telefono, si es valido le agrega el +52 y si no es valido regresa None
    if numero_e164 is None:
        return False, "número inválido o no configurado"

    if _simulacion_activa():
        print(f"[SIMULADO][SMS] Para {numero_e164}: {mensaje}") ## imprime el mensaje simulado en consola
        return True, None

    remitente = current_app.config.get("TWILIO_SMS_FROM", "") ## obtiene el numero de telefono para enviar el mensaje de texto real
    try:
        _cliente_twilio().messages.create(from_=remitente, to=numero_e164, body=mensaje) ## envia el mensaje de texto real a traves de twilio
        return True, None
    except TwilioRestException as error: ## si hay un error al enviar el mensaje de texto real, regresa False y el error
        return False, str(error)
