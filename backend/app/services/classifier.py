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