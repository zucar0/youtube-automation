from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def metadata_placeholder():
    return {"message": "metadata endpoint - coming soon"}