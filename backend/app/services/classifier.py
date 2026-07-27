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

def generar_propuesta_contenido(transcript_texto: str, equipo: str, contexto: str, tipo_contenido: str, notas_similares: list | None = None) -> dict:
    notas_similares = notas_similares or []

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

    noticias_texto = "\n".join(
        f"- {n.get('titulo', 'N/A')} ({n.get('fuente', 'N/A')}): {n.get('resumen', '')}"
        for n in notas_similares
    ) or "No se encontraron noticias relacionadas recientes."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en marketing de contenido para YouTube sobre fútbol mexicano, "
                    f"escribiendo para un canal enfocado en {equipo}. "
                    "Vas a recibir tres fuentes de información: un contexto proporcionado manualmente por el usuario, "
                    "la transcripción completa del video, y noticias relacionadas encontradas en la web.\n\n"
                    "REGLA DE PRIORIDAD: la transcripción del video es la fuente de verdad principal sobre lo que "
                    "ocurre en el clip. Las noticias relacionadas son solo contexto adicional (situación de la jornada, "
                    "reacciones, declaraciones externas) — si hay conflicto entre la transcripción y las noticias, "
                    "prioriza siempre la transcripción.\n\n"
                    "MANEJO DE TRANSCRIPCIÓN DEFECTUOSA: si la transcripción del video llega vacía, es ruido sin sentido, "
                    "mezcla de idiomas o caracteres sin coherencia, o simplemente no aporta información útil, IGNÓRALA "
                    "por completo — no intentes interpretarla ni extraer nada de ella. En ese caso, apóyate únicamente "
                    "en el contexto proporcionado por el usuario y en las noticias relacionadas para construir la "
                    "propuesta.\n\n"
                    f"IMPORTANTE SOBRE PERSPECTIVA: el canal es de {equipo}, así que el contenido debe redactarse "
                    f"siempre desde el punto de vista de {equipo}, sin importar quién habla en la transcripción "
                    "(puede ser un jugador, técnico o comentarista del equipo rival). No asumas que la transcripción "
                    f"habla en nombre de {equipo} solo porque el video se publica en este canal — identifica correctamente "
                    "de quién es la declaración/jugada y mantén la coherencia del relato en función de eso.\n\n"
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
                "content": (
                    f"Equipo del canal: {equipo}\n\n"
                    f"Contexto proporcionado por el usuario: {contexto}\n\n"
                    f"Transcripción del video: {transcript_texto}\n\n"
                    f"Noticias relacionadas encontradas:\n{noticias_texto}"
                )
            }
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generar_propuesta_rapida(equipo: str, contexto: str, tipo_contenido: str, metadata: dict, notas_similares: list) -> dict:
    """
    Igual que generar_propuesta_contenido, pero SIN transcripción.
    Se basa en: contexto del usuario + metadata liviana + noticias relacionadas.
    """
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

    noticias_texto = "\n".join(
        f"- {n.get('titulo', 'N/A')} ({n.get('fuente', 'N/A')}): {n.get('resumen', '')}"
        for n in notas_similares
    ) or "No se encontraron noticias relacionadas recientes."

    metadata_texto = (
        f"Título original: {metadata.get('titulo') or 'N/A'}\n"
        f"Descripción original: {metadata.get('descripcion') or 'N/A'}\n"
        f"Canal/fuente: {metadata.get('canal') or 'N/A'}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en marketing de contenido para YouTube sobre fútbol mexicano. "
                    "IMPORTANTE: NO tienes acceso a la transcripción del video ni lo has visto. "
                    "Vas a recibir tres fuentes de información: el contexto proporcionado manualmente por el usuario, "
                    "metadata básica del video/clip (título y descripción originales de la fuente), "
                    "y noticias relacionadas encontradas en la web.\n\n"
                    "REGLA DE PRIORIDAD: si el título original del video (metadata) describe una jugada o "
                    "resultado específico, ese título es la fuente de verdad sobre lo que ocurre en el clip. "
                    "Las noticias relacionadas son solo contexto de la jornada o situación general del equipo — "
                    "NO asumas que describen la misma jugada del clip. Si hay conflicto entre el título original "
                    "y las noticias (por ejemplo, distinto marcador, distinto jugador, distinto resultado), "
                    "prioriza siempre el título original y usa las noticias solo para detalles de contexto "
                    "que no contradigan lo que dice el título.\n\n"
                    "Usa principalmente el contexto del usuario, y complementa con la metadata y las noticias "
                    "para enriquecer detalles. No inventes datos que no estén respaldados por estas fuentes.\n\n"
                    f"{instrucciones_formato}\n\n"
                    "Responde SOLO en formato JSON con las claves:\n"
                    "titulo, descripcion, "
                    "hashtags (lista de 15-20, sin el símbolo #), "
                    "etiquetas (lista de 12-20 tags de búsqueda con el límite de 500 caracteres), "
                    "frases_potentes (lista de 5 a 10 frases contundentes para thumbnail, "
                    "basadas en el contexto y las noticias, ya que no hay transcripción disponible)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Equipo: {equipo}\n\n"
                    f"Contexto proporcionado por el usuario: {contexto}\n\n"
                    f"Metadata del video/clip:\n{metadata_texto}\n\n"
                    f"Noticias relacionadas encontradas:\n{noticias_texto}"
                )
            }
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content