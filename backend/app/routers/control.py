import re
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.downloader import download_video as svc_download
from app.services.transcriber import transcribe_video
from app.services.classifier import clasificar_tema, generar_propuesta_contenido
from app.services.youtube_metadata import obtener_metadata_youtube
from app.services.databricks_uploader import guardar_en_volume

router = APIRouter()

class ControlRequest(BaseModel):
    url: str
    equipo: str
    texto_referencia: str
    tipo_contenido: str = "short"
    usuario: str = "toño"

def extraer_youtube_id(url: str) -> str | None:
    if "youtube.com" not in url and "youtu.be" not in url:
        return None
    match = re.search(r"(?:v=|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@router.post("/")
async def registrar_url(request: ControlRequest):
    registro_id = str(uuid.uuid4())
    registro = {
        "id": registro_id,
        "url": request.url,
        "equipo": request.equipo,
        "texto_referencia": request.texto_referencia,
        "fecha_ingreso": datetime.now(timezone.utc).isoformat(),
        "usuario": request.usuario,
        "estatus": "pendiente",
        "video_id": None,
        "error": None
    }
    guardar_en_volume(registro, registro_id, tipo="control")

    youtube_id = extraer_youtube_id(request.url)
    video_id = youtube_id or registro_id

    try:
        registro["estatus"] = "descargando"
        guardar_en_volume(registro, registro_id, tipo="control")
        resultado_descarga = svc_download(request.url)
        file_path = resultado_descarga["file_path"]

        registro["estatus"] = "transcribiendo"
        guardar_en_volume(registro, registro_id, tipo="control")
        resultado_transcripcion = transcribe_video(file_path)
        tema_data = clasificar_tema(resultado_transcripcion["text"])
        propuesta = generar_propuesta_contenido(
            resultado_transcripcion["text"],
            request.equipo,
            request.texto_referencia,
            request.tipo_contenido
        )
        payload_transcripcion = {
            "video_id": video_id,
            "text": resultado_transcripcion["text"],
            "segments": resultado_transcripcion["segments"],
            "language": resultado_transcripcion["language"],
            "clasificacion": tema_data,
            "propuesta_contenido": propuesta,
        }
        guardar_en_volume(payload_transcripcion, video_id, tipo="transcripts")

        if youtube_id:
            registro["estatus"] = "obteniendo_metadata"
            guardar_en_volume(registro, registro_id, tipo="control")
            metadata = obtener_metadata_youtube(youtube_id)
            guardar_en_volume(metadata, youtube_id, tipo="metadata")

        registro["estatus"] = "completado"
        registro["video_id"] = video_id
        registro["propuesta_contenido"] = propuesta  
        registro["transcripcion"] = resultado_transcripcion["text"]
        guardar_en_volume(registro, registro_id, tipo="control")

    except Exception as e:
        registro["estatus"] = "error"
        registro["error"] = str(e)
        guardar_en_volume(registro, registro_id, tipo="control")
        raise HTTPException(status_code=500, detail=str(e))

    return registro