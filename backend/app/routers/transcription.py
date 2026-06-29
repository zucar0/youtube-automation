from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def transcription_placeholder():
    return {"message": "transcription endpoint - coming soon"}
