from fastapi import APIRouter, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from app.services.telegram_bot_logic import start, manejar_mensaje

router = APIRouter()

telegram_app = Application.builder().token(settings.telegram_bot_token_dev).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))


@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}