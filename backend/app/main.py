import os
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import download, transcription, metadata, approval, rss, control, rapido, telegram_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_url:
        await telegram_webhook.telegram_app.initialize()
        await telegram_webhook.telegram_app.start()

        webhook_url = f"https://{railway_url}/api/telegram/webhook"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token_dev}/setWebhook",
                json={"url": webhook_url}
            )
        logger.info(f"Webhook registrado en: {webhook_url} | respuesta: {resp.json()}")
    else:
        logger.info("RAILWAY_PUBLIC_DOMAIN no detectado — corriendo en modo local, webhook NO se activa.")

    yield

    if railway_url:
        await telegram_webhook.telegram_app.stop()
        await telegram_webhook.telegram_app.shutdown()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(download.router,       prefix="/api/download",      tags=["Download"])
app.include_router(transcription.router,  prefix="/api/transcription", tags=["Transcription"])
app.include_router(metadata.router,       prefix="/api/metadata",      tags=["Metadata"])
app.include_router(approval.router,       prefix="/api/approval",      tags=["Approval"])
app.include_router(rss.router,            prefix="/api/rss",           tags=["RSS"])
app.include_router(control.router,        prefix="/api/control",       tags=["Control"])
app.include_router(rapido.router,         prefix="/api/rapido",        tags=["Rapido"])
app.include_router(telegram_webhook.router, prefix="/api/telegram",    tags=["Telegram"])


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}