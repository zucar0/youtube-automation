from fastapi import APIRouter, HTTPException
from app.models.schemas import DownloadRequest, VideoJob
from app.services.downloader import download_video as svc_download

router = APIRouter()

@router.post("/", response_model=VideoJob)
async def download_video_endpoint(request: DownloadRequest):
    try:
        result = svc_download(request.url)
        return VideoJob(
            job_id=result["job_id"],
            url=request.url,
            channel_type=request.channel_type,
            status="downloaded",
            file_path=result["file_path"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    return {"job_id": job_id, "status": "pending"}