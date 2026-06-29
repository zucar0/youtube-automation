from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.transcriber import transcribe_video

router = APIRouter()

class TranscriptionRequest(BaseModel):
    file_path: str
    model_size: str = "base"

@router.post("/")
async def transcribe(request: TranscriptionRequest):
    try:
        result = transcribe_video(request.file_path, request.model_size)
        return {
            "status": "transcribed",
            "text": result["text"],
            "language": result["language"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def transcription_placeholder():
    return {"message": "transcription endpoint - coming soon"}