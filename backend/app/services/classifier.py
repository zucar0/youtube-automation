from app.config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.openai_api_key)

def clasificar_tema(transcript_texto: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Clasifica el siguiente texto de un video sobre Club América. Responde SOLO en formato JSON con las claves: tema_principal, jugador_mencionado, torneo, sentimiento."
            },
            {
                "role": "user",
                "content": transcript_texto
            }
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generar_propuesta_contenido(transcript_texto: str, equipo: str, contexto: str, tipo_contenido: str) -> dict:
    if tipo_contenido == "largo":
        instrucciones_formato = (
            "Este contenido es para un VIDEO LARGO/NORMAL de YouTube (no un short). "
            "El título debe ser descriptivo pero atractivo, puede tener hasta 150 caracteres, "
            "y puede incluir palabras clave de búsqueda de forma natural. "
            "La descripción debe ser más completa (10-20 líneas y al menos 550 caracteres), incluyendo contexto "
            "y una invitación a suscribirse. Las frases para thumbnail deben transmitir el tema central del video completo, "
            "no un solo momento puntual."
        )
    else:
        instrucciones_formato = (
            "Este contenido es para un SHORT de YouTube. "
            "El título debe ser corto (máximo 150 caracteres y mínimo 100 caracteres), directo y con gancho inmediato — "
            "la persona debe entender el video en menos de 2 segundos de lectura. "
            "La descripción debe ser más completa (10-20 líneas y al menos 550 caracteres), incluyendo contexto "
            "y una invitación a suscribirse. Las frases para thumbnail deben capturar el momento más impactante o sorprendente del clip, "
            "pensadas para generar curiosidad inmediata."
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en marketing de contenido para YouTube sobre fútbol mexicano. "
                    "Vas a recibir dos fuentes de información: un contexto proporcionado manualmente por el usuario, "
                    "y la transcripción completa del video. Usa la fuente que tenga más información útil y relevante: "
                    "si el contexto ya describe claramente el contenido del video, básate principalmente en él; "
                    "si el contexto es breve o genérico, apóyate más en la transcripción para extraer detalles concretos.\n\n"
                    f"{instrucciones_formato}\n\n"
                    "Responde SOLO en formato JSON con las claves:\n"
                    "titulo, descripcion, "
                    "hashtags (lista de 15-20, sin el símbolo #), "
                    "etiquetas (lista de 12-20 tags de búsqueda con el límite de 500 caracteres), "
                    "frases_potentes (lista de 5 a 10 frases y contundentes para thumbnail (utilizar las frases que vienen literales dela transcripción))."
                )
            },
            {
                "role": "user",
                "content": f"Contexto proporcionado por el usuario: {contexto}\n\nTranscripción del video: {transcript_texto}"
            }
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content