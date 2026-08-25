import re
import json
import uuid
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.downloader import download_video as svc_download
from app.services.transcriber import transcribe_video
from app.services.classifier import clasificar_tema, generar_propuesta_contenido
from app.services.youtube_metadata import obtener_metadata_youtube
from app.services.databricks_uploader import guardar_en_volume
from app.services.news_search import buscar_notas_similares

router = APIRouter()

class ControlRequest(BaseModel):
    url: str
    equipo: str
    texto_referencia: str
    tipo_contenido: str = "short"
    usuario: str = "toño"
    inicio: str | None = None
    fin: str | None = None

def extraer_youtube_id(url: str) -> str | None:
    if "youtube.com" not in url and "youtu.be" not in url:
        return None
    match = re.search(r"(?:v=|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def _tiempo_a_segundos(cadena: str) -> int:
    """Convierte 'MM:SS' o 'HH:MM:SS' a segundos totales."""
    partes = [int(p) for p in cadena.strip().split(":")]
    while len(partes) < 3:
        partes.insert(0, 0)
    h, m, s = partes[-3:]
    return h * 3600 + m * 60 + s

@router.post("/")
async def registrar_url(request: ControlRequest):
    registro_id = str(uuid.uuid4())
    registro = {
        "id": registro_id,
        "url": request.url,
        "equipo": request.equipo,
        "texto_referencia": request.texto_referencia,
        "tipo_contenido": request.tipo_contenido,   # <-- nuevo
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
        resultado_transcripcion = transcribe_video(file_path, inicio=request.inicio, fin=request.fin)
        tema_data = clasificar_tema(resultado_transcripcion["text"])
        notas_similares = await buscar_notas_similares(request.equipo, request.texto_referencia)


        propuesta_raw = generar_propuesta_contenido(
            resultado_transcripcion["text"],
            request.equipo,
            request.texto_referencia,
            request.tipo_contenido,
            notas_similares=notas_similares,
            segments=resultado_transcripcion.get("segments"),
        )

        propuesta_dict = json.loads(propuesta_raw)
        capitulos = propuesta_dict.get("capitulos") or []
        if capitulos:
            capitulos_texto = "\n".join(
                f"{c.get('tiempo', '00:00')} {c.get('titulo', '')}" for c in capitulos
            )
            propuesta_dict["descripcion"] = (
                f"{propuesta_dict.get('descripcion', '')}\n\nCapítulos:\n{capitulos_texto}"
            )

        thumbnails = []
        momentos = propuesta_dict.get("momentos_clave") or []
        print(f"🔍 momentos_clave recibidos de GPT: {momentos}")
        if momentos:
            # Si se usó recorte de rango, los timestamps que regresó GPT son relativos
            # al segmento recortado — hay que sumar el offset para ubicar el frame
            # correcto en el video ORIGINAL (file_path sigue siendo el archivo completo).
            offset_seg = _tiempo_a_segundos(request.inicio) if request.inicio else 0
            thumb_dir = tempfile.mkdtemp(prefix="thumbnails_")
            for i, m in enumerate(momentos):
                try:
                    absoluto = offset_seg + _tiempo_a_segundos(m.get("tiempo", "00:00"))
                    frame_path = os.path.join(thumb_dir, f"frame_{i}.jpg")
                    subprocess.run(
                        ["ffmpeg", "-y", "-ss", str(absoluto), "-i", file_path,
                         "-frames:v", "1", "-q:v", "2", frame_path],
                        check=True, capture_output=True,
                    )
                    thumbnails.append({
                        "tiempo": m.get("tiempo"),
                        "frase": m.get("frase"),
                        "path": frame_path,
                    })
                except Exception as e:
                    print(f"❌ Error extrayendo frame {i} para thumbnail: {e}")
                    continue  # si un frame falla, no bloquea el resto de la propuesta

        else:
            print("⚠️ GPT no regresó momentos_clave — no se generarán thumbnails.")

        propuesta = json.dumps(propuesta_dict, ensure_ascii=False)
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
        registro["thumbnails"] = thumbnails
        guardar_en_volume(registro, registro_id, tipo="control")

    except Exception as e:
        registro["estatus"] = "error"
        registro["error"] = str(e)
        guardar_en_volume(registro, registro_id, tipo="control")
        raise HTTPException(status_code=500, detail=str(e))

    return registro