import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.services.metadata_router import obtener_metadata_liviana, detectar_fuente
from app.services.news_search import buscar_notas_similares
from app.services.classifier import generar_propuesta_rapida
from app.services.databricks_sql_client import guardar_en_cola_pendiente
from app.models.schemas import PendingDownload

logger = logging.getLogger(__name__)
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

        await update.message.reply_text("⏳ Buscando contexto y generando propuesta...")

        try:
            url = estado["url"]
            equipo = estado["equipo"]
            contexto = estado["texto_referencia"]
            tipo_contenido = estado["tipo_contenido"]

            fuente = detectar_fuente(url)
            metadata = await obtener_metadata_liviana(url)
            notas_similares = await buscar_notas_similares(equipo, contexto)

            propuesta_raw = generar_propuesta_rapida(
                equipo=equipo, contexto=contexto, tipo_contenido=tipo_contenido,
                metadata=metadata, notas_similares=notas_similares,
            )
            propuesta = json.loads(propuesta_raw)

            registro_id = await guardar_en_cola_pendiente(PendingDownload(
                url=url, fuente=fuente, equipo=equipo, contexto=contexto,
                chat_id=str(user_id), metadata_liviana=metadata,
            ))

            frases_texto = "\n".join(f"• {f}" for f in propuesta.get("frases_potentes", []))
            mensaje = (
                f"✅ *Propuesta generada* ({tipo_contenido})\n\n"
                f"📌 *Título:* {propuesta.get('titulo', 'N/A')}\n\n"
                f"📝 *Descripción:*\n{propuesta.get('descripcion', 'N/A')}\n\n"
                f"🏷️ *Hashtags:* {' '.join('#' + h for h in propuesta.get('hashtags', []))}\n\n"
                f"🔑 *Etiquetas:* {', '.join(propuesta.get('etiquetas', []))}\n\n"
                f"💥 *Frases para thumbnail:*\n{frases_texto}\n\n"
                f"📦 Video encolado para descarga (id: `{registro_id[:8]}...`)"
            )
            await update.message.reply_text(mensaje, parse_mode="Markdown")

        except Exception as e:
            logger.exception(f"Error generando propuesta rápida: {e}")
            await update.message.reply_text(f"❌ Ocurrió un error generando la propuesta: {e}")

        user_state.pop(user_id, None)
        return

    user_state[user_id] = estado