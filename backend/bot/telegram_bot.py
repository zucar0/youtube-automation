import requests
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import settings

API_URL = "http://localhost:8000/api/control/"

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"paso": "url"}
    await update.message.reply_text(
        "Mándame la URL del video (o la ruta local del archivo, ej. /home/antonio/videos/programa.mkv):"
    )

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text
    estado = user_state.get(user_id, {"paso": "url"})

    if estado["paso"] == "url":
        estado["url"] = texto
        estado["paso"] = "rango"
        await update.message.reply_text(
            "¿Quieres transcribir solo un rango de tiempo? Responde 'no' para transcribir todo el video, "
            "o dame el rango así: 00:05:00-00:20:00 (inicio-fin)"
        )

    elif estado["paso"] == "rango":
        texto_limpio = texto.strip().lower()
        if texto_limpio in ("no", "n", "todo"):
            estado["inicio"] = None
            estado["fin"] = None
        else:
            try:
                inicio, fin = texto.strip().split("-")
                estado["inicio"] = inicio.strip()
                estado["fin"] = fin.strip()
            except ValueError:
                await update.message.reply_text(
                    "Formato no reconocido. Usa 00:05:00-00:20:00 o escribe 'no'."
                )
                user_state[user_id] = estado
                return
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
            "usuario": update.effective_user.username or "telegram_user",
            "inicio": estado.get("inicio"),
            "fin": estado.get("fin"),
        }

        await update.message.reply_text("⏳ Procesando video, esto puede tardar varios minutos (videos largos tardan más)...")
        try:
            response = requests.post(API_URL, json=payload, timeout=7200)  # hasta 2h para videos largos
            resultado = response.json()
        except requests.exceptions.Timeout:
            await update.message.reply_text(
                "⏱️ El video sigue procesándose en el backend, pero tardó más de 2 horas y el bot dejó de esperar. "
                "Revisa la terminal del backend para confirmar si ya terminó."
            )
            user_state.pop(user_id, None)
            return
        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"❌ Error de conexión con el backend: {e}")
            user_state.pop(user_id, None)
            return

        if resultado.get("estatus") == "completado" and resultado.get("propuesta_contenido"):
            try:
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
                    f"🎙️ *Transcripción:*\n{transcripcion_corta}"
                )
                await update.message.reply_text(mensaje)

                # Todo lo relacionado a thumbnail va en mensajes separados (Telegram
                # limita a 4096 caracteres por mensaje, así que va aparte del principal).
                if frases_texto:
                    await update.message.reply_text(f"💥 *Frases para thumbnail:*\n{frases_texto}")

                momentos_clave = propuesta.get("momentos_clave", [])
                if momentos_clave:
                    await update.message.reply_text(
                        "🎨 *Instrucciones para generar thumbnail con IA* "
                        "(copia/pega en Nano Banana u otra IA, junto con la foto correspondiente):"
                    )
                    for idx, m in enumerate(momentos_clave, start=1):
                        instrucciones = m.get("instrucciones_thumbnail", "")
                        if not instrucciones:
                            continue
                        prompt_listo = (
                            f"Esta es una captura real de una transmisión de fútbol. "
                            f"Contexto de lo que ocurre en este instante: {instrucciones}\n"
                            f"Edita esta fotografía para usarse como thumbnail de YouTube. Debe notarse "
                            f"una mejora visual clara: colores más vivos, mayor contraste y nitidez, mejor "
                            f"manejo de luces y sombras. Puedes recortar/hacer zoom ligeramente para acercar "
                            f"al sujeto principal. NO inventes un escenario, fondo ni personas distintas a "
                            f"las de la imagen original — debe seguir siendo reconociblemente la misma foto. "
                            f"NO agregues texto, letras ni títulos en la imagen."
                        )
                        await update.message.reply_text(
                            f"*Opción {idx}* ({m.get('tiempo', '')} — {m.get('frase', '')}):\n`{prompt_listo}`"
                        )

                thumbnails = resultado.get("thumbnails") or []
                for thumb in thumbnails:
                    ruta = thumb.get("path")
                    frase = thumb.get("frase", "")
                    es_ia = thumb.get("generado_ia", False)
                    if ruta and os.path.exists(ruta):
                        try:
                            with open(ruta, "rb") as foto:
                                if es_ia:
                                    caption = "🎨 Versión mejorada con IA (sin texto, para editar)"
                                else:
                                    caption = f"🖼️ {frase}" if frase else None
                                await update.message.reply_photo(photo=foto, caption=caption)
                        except Exception as e:
                            print(f"❌ Error al enviar thumbnail: {e}")
            except Exception as e:
                print(f"❌ Error al formatear/enviar mensaje: {e}")
                await update.message.reply_text(
                    f"✅ Procesado, pero hubo un error al formatear el mensaje: {e}"
                )
        else:
            await update.message.reply_text(f"Estatus: {resultado.get('estatus')}\nDetalle: {resultado}")

        user_state.pop(user_id)

    user_state[user_id] = estado

app = Application.builder().token(settings.telegram_bot_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.run_polling()