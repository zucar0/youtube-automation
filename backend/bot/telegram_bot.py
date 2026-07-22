import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import settings

API_URL = "http://localhost:8000/api/control/"

# Guardamos el estado de la conversación por usuario (simple, en memoria)
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"paso": "url"}
    await update.message.reply_text("Mándame la URL del video:")

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text
    estado = user_state.get(user_id, {"paso": "url"})

    if estado["paso"] == "url":
        estado["url"] = texto
        estado["paso"] = "equipo"
        await update.message.reply_text("¿Qué equipo/canal? (ej. América)")
    elif estado["paso"] == "equipo":
        estado["equipo"] = texto
        estado["paso"] = "contexto"
        await update.message.reply_text("Dame un texto de contexto/referencia:")
    elif estado["paso"] == "contexto":
        estado["texto_referencia"] = texto
        payload = {
            "url": estado["url"],
            "equipo": estado["equipo"],
            "texto_referencia": estado["texto_referencia"],
            "usuario": update.effective_user.username or "telegram_user"
        }
        response = requests.post(API_URL, json=payload)
        await update.message.reply_text(f"✅ Registrado: {response.json()}")
        user_state.pop(user_id)

    user_state[user_id] = estado

app = Application.builder().token(settings.telegram_bot_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.run_polling()