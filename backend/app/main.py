from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import download, transcription, metadata, approval, rss, control, rapido

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(download.router,       prefix="/api/download",      tags=["Download"])
app.include_router(transcription.router,  prefix="/api/transcription",  tags=["Transcription"])
app.include_router(metadata.router,       prefix="/api/metadata",       tags=["Metadata"])
app.include_router(approval.router,       prefix="/api/approval",       tags=["Approval"])
app.include_router(rss.router, prefix="/api/rss", tags=["RSS"])
app.include_router(control.router, prefix="/api/control", tags=["Control"])
app.include_router(rapido.router, prefix="/api/rapido", tags=["Rapido"])

@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}