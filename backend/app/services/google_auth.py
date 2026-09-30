"""
Servicio de autenticación con Google (Drive + Sheets).

Arquitectura de dos pasos:
  1. run_local_authorization_flow(): se corre UNA SOLA VEZ, en local,
     vía scripts/google_oauth_authorize.py. Abre el navegador, el
     usuario autoriza, y se guarda token.json con refresh_token.
  2. get_google_credentials(): se usa en producción (Railway). Lee
     el token desde GOOGLE_OAUTH_TOKEN_JSON (variable de entorno) si
     existe, o desde el archivo token.json en local. Si el
     access_token expiró, lo refresca solo usando el refresh_token.
     Nunca dispara un flujo interactivo.

Scopes usados: Drive (solo archivos creados por la app) y Sheets.
"""
import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleAuthNotConfigured(Exception):
    """
    Se lanza cuando falta el token (ni en archivo ni en variable de
    entorno), o el token existente no se pudo refrescar (por ejemplo,
    si el refresh_token fue revocado). En estos casos hay que volver a
    correr run_local_authorization_flow() en local y actualizar
    GOOGLE_OAUTH_TOKEN_JSON en Railway con el nuevo contenido.
    """
    pass


def run_local_authorization_flow() -> None:
    """
    Flujo interactivo, solo para correr en local (nunca en Railway).

    Abre el navegador, el usuario entra con la cuenta de Google dueña
    del Drive/Sheet, autoriza, y se guarda el token resultante
    (con refresh_token incluido) en GOOGLE_OAUTH_TOKEN_PATH.
    """
    credentials_path = settings.google_credentials_path
    token_path = settings.google_oauth_token_path

    logger.info(f"Iniciando flujo de autorización local con {credentials_path}")

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())

    logger.info(f"Token guardado exitosamente en {token_path}")
    logger.info(
        "Copia el contenido de ese archivo y pégalo como la variable de "
        "entorno GOOGLE_OAUTH_TOKEN_JSON en Railway."
    )


def _load_raw_credentials() -> Credentials:
    """
    Carga las credenciales sin refrescar, ya sea desde la variable de
    entorno GOOGLE_OAUTH_TOKEN_JSON (Railway/producción) o desde el
    archivo token.json en disco (local).
    """
    if settings.google_oauth_token_json:
        try:
            token_info = json.loads(settings.google_oauth_token_json)
        except json.JSONDecodeError as exc:
            raise GoogleAuthNotConfigured(
                "GOOGLE_OAUTH_TOKEN_JSON no contiene un JSON válido."
            ) from exc
        return Credentials.from_authorized_user_info(token_info, SCOPES)

    token_path = settings.google_oauth_token_path
    try:
        return Credentials.from_authorized_user_file(token_path, SCOPES)
    except FileNotFoundError:
        raise GoogleAuthNotConfigured(
            f"No se encontró {token_path} ni GOOGLE_OAUTH_TOKEN_JSON. "
            "Corre run_local_authorization_flow() en local primero "
            "(scripts/google_oauth_authorize.py)."
        )


def get_google_credentials() -> Credentials:
    """
    Devuelve credenciales válidas para usar en producción.

    - Si el access_token sigue vigente, lo regresa tal cual.
    - Si expiró pero hay refresh_token, lo refresca automáticamente.
      Si el token vino de archivo (local), sobreescribe token.json.
      Si vino de GOOGLE_OAUTH_TOKEN_JSON (Railway), el refresco solo
      vive en memoria durante esa ejecución del proceso (el
      refresh_token no cambia, así que en el próximo restart se vuelve
      a refrescar sin problema).
    - Si no hay token disponible, o el refresh falla, lanza
      GoogleAuthNotConfigured.

    Esta función NUNCA dispara un flujo interactivo (no sirve de nada
    en un servidor sin navegador como Railway).
    """
    creds = _load_raw_credentials()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            raise GoogleAuthNotConfigured(
                f"No se pudo refrescar el token de Google: {exc}. "
                "Puede que el refresh_token haya sido revocado; corre "
                "run_local_authorization_flow() de nuevo en local y "
                "actualiza GOOGLE_OAUTH_TOKEN_JSON en Railway."
            ) from exc

        if not settings.google_oauth_token_json:
            token_path = settings.google_oauth_token_path
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info("Token de Google refrescado y guardado en disco")
        else:
            logger.info(
                "Token de Google refrescado en memoria "
                "(GOOGLE_OAUTH_TOKEN_JSON no se modifica automáticamente)"
            )

        return creds

    raise GoogleAuthNotConfigured(
        "El token disponible no es válido y no tiene refresh_token. "
        "Corre run_local_authorization_flow() de nuevo en local."
    )