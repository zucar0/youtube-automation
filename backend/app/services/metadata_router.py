import asyncio
import re
import logging
from app.services.youtube_metadata import obtener_metadata_youtube
from app.services.espn_metadata import obtener_metadata_espn

logger = logging.getLogger(__name__)


def detectar_fuente(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "espn.com" in url or "espndeportes" in url:
        return "espn"
    return "desconocida"


def extraer_youtube_id(url: str) -> str | None:
    if "youtube.com" not in url and "youtu.be" not in url:
        return None
    match = re.search(r"(?:v=|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def _metadata_vacia(fuente: str, motivo: str) -> dict:
    return {
        "titulo": None,
        "descripcion": None,
        "canal": None,
        "fuente_detectada": fuente,
        "metadata_error": motivo,
    }


async def obtener_metadata_liviana(url: str) -> dict:
    """
    Punto único de entrada para metadata SIN descarga de video.
    NUNCA lanza excepción — si algo falla, regresa metadata vacía
    con el motivo, para que el flujo de propuesta pueda continuar.
    """
    fuente = detectar_fuente(url)

    try:
        if fuente == "youtube":
            youtube_id = extraer_youtube_id(url)
            if not youtube_id:
                return _metadata_vacia(fuente, "youtube_id_invalido")

            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, obtener_metadata_youtube, youtube_id)
            metadata["fuente_detectada"] = fuente
            return metadata

        if fuente == "espn":
            metadata = await obtener_metadata_espn(url)
            metadata["fuente_detectada"] = fuente
            return metadata

        return _metadata_vacia(fuente, "fuente_no_soportada")

    except Exception as e:
        logger.warning(f"No se pudo obtener metadata para {url}: {e}")
        return _metadata_vacia(fuente, str(e))