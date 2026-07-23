import requests
import json
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
        estado["paso"] = "tipo_contenido"
        await update.message.reply_text("¿Es para short o video largo? (responde: short / largo)")

    elif estado["paso"] == "tipo_contenido":
        tipo = texto.strip().lower()
        estado["tipo_contenido"] = tipo if tipo in ("short", "largo") else "short"

        payload = {
            "url": estado["url"],
            "equipo": estado["equipo"],
            "texto_referencia": estado["texto_referencia"],
            "tipo_contenido": estado["tipo_contenido"],
            "usuario": update.effective_user.username or "telegram_user"
        }

        await update.message.reply_text("⏳ Procesando video, esto puede tardar 1-2 minutos...")
        response = requests.post(API_URL, json=payload)
        resultado = response.json()

        if resultado.get("estatus") == "completado" and resultado.get("propuesta_contenido"):
            propuesta = json.loads(resultado["propuesta_contenido"])
            frases = propuesta.get("frases_potentes", [])
            frases_texto = "\n".join(f"• {f}" for f in frases)
            transcripcion = resultado.get("transcripcion", "N/A")
            transcripcion_corta = transcripcion[:500] + "..." if len(transcripcion) > 500 else transcripcion

            mensaje = (
                f"✅ *Video procesado* ({estado['tipo_contenido']})\n\n"
                f"📌 *Título:* {propuesta.get('titulo', 'N/A')}\n\n"
                f"📝 *Descripción:*\n{propuesta.get('descripcion', 'N/A')}\n\n"
                f"🏷️ *Hashtags:* {' '.join('#' + h for h in propuesta.get('hashtags', []))}\n\n"
                f"🔑 *Etiquetas:* {', '.join(propuesta.get('etiquetas', []))}\n\n"
                f"💥 *Frases para thumbnail:*\n{frases_texto}\n\n"
                f"🎙️ *Transcripción:*\n{transcripcion_corta}"

            )
            await update.message.reply_text(mensaje, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Estatus: {resultado.get('estatus')}\nDetalle: {resultado}")

        user_state.pop(user_id)

    user_state[user_id] = estado

app = Application.builder().token(settings.telegram_bot_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.run_polling()