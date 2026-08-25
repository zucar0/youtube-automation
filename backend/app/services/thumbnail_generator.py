import os
import time
from google import genai
from google.genai import types
from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generar_thumbnail_ia(frame_path: str, instrucciones: str, output_dir: str, intentos: int = 3) -> str | None:
    """Toma un frame real del video (extraído con ffmpeg) y una instrucción específica
    de qué está pasando en ese momento, y le pide a Nano Banana 2 que genere una versión
    visualmente mejorada del MISMO momento real (sin inventar un escenario distinto),
    SIN texto quemado en la imagen (el usuario agrega el texto después al editar).
    Devuelve la ruta al archivo generado, o None si falla tras agotar los reintentos.
    Reintenta automáticamente ante errores temporales del servidor (503 alta demanda, 429)."""
    if not settings.gemini_api_key:
        return None

    try:
        with open(frame_path, "rb") as f:
            imagen_bytes = f.read()
    except Exception as e:
        print(f"❌ Error leyendo frame para thumbnail IA: {e}")
        return None

    prompt = (
        "Esta es una captura REAL de una transmisión de fútbol. "
        f"Contexto de lo que ocurre en este instante: {instrucciones}\n\n"
        "Edita esta fotografía para usarse como thumbnail de YouTube. Debe notarse una mejora "
        "visual CLARA y perceptible respecto a la original: colores más vivos y saturados, "
        "mayor contraste, mayor nitidez/definición, mejor manejo de luces y sombras, y si ayuda "
        "a la composición, puedes recortar/hacer zoom ligeramente para acercar al sujeto principal "
        "y que se vea más impactante como thumbnail. No entregues una imagen casi idéntica a la "
        "original — el resultado debe verse notablemente más pulido y profesional.\n\n"
        "REGLAS ESTRICTAS que debes seguir de todas formas:\n"
        "1. NO inventes un escenario, fondo, cancha ni jugadores distintos a los que aparecen "
        "en la imagen original. Debe seguir siendo reconociblemente LA MISMA fotografía y las "
        "mismas personas.\n"
        "2. Conserva los uniformes, colores de equipo, marcador y elementos gráficos visibles "
        "tal como están (mismo contenido, no mismo pixel por pixel).\n"
        "3. NO agregues ningún texto, letra, título ni subtítulo en la imagen."
    )

    client = _get_client()
    for intento in range(1, intentos + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=[
                    prompt,
                    types.Part.from_bytes(data=imagen_bytes, mime_type="image/jpeg"),
                ],
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    output_path = os.path.join(output_dir, "thumbnail_ia.jpg")
                    with open(output_path, "wb") as out:
                        out.write(part.inline_data.data)
                    return output_path

            # El modelo respondió 200 pero sin imagen — casi siempre es texto
            # explicando por qué no generó nada (ej. filtro de seguridad).
            texto_respuesta = ""
            for part in response.candidates[0].content.parts:
                if getattr(part, "text", None):
                    texto_respuesta += part.text
            print(f"⚠️ Gemini respondió 200 OK pero sin imagen. Texto de respuesta: {texto_respuesta or '(vacío)'}")
            return None

 
        except Exception as e:
            es_temporal = "503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if es_temporal and intento < intentos:
                espera = 15 * intento  # 15s, 30s, 45s...
                print(f"⏳ Thumbnail IA: intento {intento}/{intentos} falló ({e}). Reintentando en {espera}s...")
                time.sleep(espera)
                continue
            print(f"❌ Error generando thumbnail con IA (intento {intento}/{intentos}): {e}")
            return None

    return None