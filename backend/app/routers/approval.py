from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def approval_placeholder():
    return {"message": "approval endpoint - coming soon"}