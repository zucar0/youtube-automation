import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.transcriber import transcribe_video
from app.services.classifier import clasificar_tema
from app.services.databricks_uploader import guardar_en_volume
import traceback


router = APIRouter()

class TranscriptionRequest(BaseModel):
    file_path: str
    video_id: str
    model_size: str = "base"

@router.post("/")
async def transcribe(request: TranscriptionRequest):
    try:
        # Paso 1: Transcribir 
        result = transcribe_video(request.file_path, request.model_size)

        # Paso 2: Clasificar el tema con OpenAI
        tema_data = clasificar_tema(result["text"])

        # Paso 3: Armar el payload completo
        payload = {
            "video_id": request.video_id,
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "clasificacion": tema_data,
        }

        # Paso 4: Subir al Volume de Databricks (capa Bronze)
        guardar_en_volume(payload, request.video_id, tipo="transcripts")

        return {
            "status": "transcribed",
            "text": result["text"],
            "language": result["language"],
            "clasificacion": tema_data,
        }
    except Exception as e:
        traceback.print_exc()  # <-- esto imprime el error completo en consola
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def transcription_placeholder():
    return {"message": "transcription endpoint - coming soon"}