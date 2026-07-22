from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.youtube_metadata import obtener_metadata_youtube
from app.services.databricks_uploader import guardar_en_volume

router = APIRouter()

class MetadataRequest(BaseModel):
    video_id: str

@router.post("/")
async def obtener_metadata(request: MetadataRequest):
    try:
        metadata = obtener_metadata_youtube(request.video_id)
        guardar_en_volume(metadata, request.video_id, tipo="metadata")
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def metadata_placeholder():
    return {"message": "metadata endpoint - coming soon"}