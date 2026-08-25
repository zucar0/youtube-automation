from app.config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.openai_api_key)


def _formatear_tiempo(segundos: float) -> str:
    """Convierte segundos a formato MM:SS, o HH:MM:SS si el video dura más de 1 hora."""
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    if horas > 0:
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    return f"{minutos:02d}:{segs:02d}"

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

def generar_propuesta_contenido(transcript_texto: str, equipo: str, contexto: str, tipo_contenido: str, notas_similares: list | None = None, segments: list | None = None) -> dict:
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

    tiene_segments = bool(segments)
    usar_capitulos = tipo_contenido == "largo" and tiene_segments

    instrucciones_capitulos = ""
    instrucciones_momentos = ""
    segments_texto = ""
    claves_extra_json = ""

    if tiene_segments:
        segments_texto = "\n".join(
            f"[{_formatear_tiempo(seg['start'])}] {seg['text'].strip()}"
            for seg in segments
        )
        instrucciones_momentos = (
            "\n\nADEMÁS, identifica entre 2 y 3 momentos pico/más impactantes del video usando la transcripción "
            "segmentada con timestamps que se te proporciona más abajo — ideales para usarse como frame de "
            "thumbnail. Regresa esto en la clave 'momentos_clave': lista de objetos con 'tiempo' (mismo formato "
            "que los timestamps recibidos), 'frase' (frase corta y contundente para overlay de thumbnail, puede "
            "repetir alguna de las frases_potentes si aplica), e 'instrucciones_thumbnail' (1-2 oraciones muy "
            "específicas, en español, describiendo qué está pasando exactamente en ese momento real del video — "
            "quién anota/qué jugada ocurre, de qué equipo, con qué emoción — pensadas para guiar la edición de "
            "una fotografía REAL de ese instante sin inventar un escenario distinto)."
        )
        claves_extra_json += (
            "momentos_clave (lista de 2 a 3 objetos con las claves 'tiempo', 'frase' e 'instrucciones_thumbnail'), "
        )
    if usar_capitulos:
        instrucciones_capitulos = (
            "\n\nADEMÁS, genera una lista de capítulos para YouTube usando la transcripción segmentada con "
            "timestamps que se te proporciona más abajo (bloque 'Transcripción segmentada con timestamps'). "
            "Reglas obligatorias: el primer capítulo debe iniciar en 00:00, debe haber mínimo 3 capítulos, y "
            "cada capítulo debe durar al menos 10 segundos. Usa el mismo formato de tiempo que ves en los "
            "timestamps (MM:SS o HH:MM:SS) y un título corto (máximo 8 palabras) que resuma el tema de esa sección."
        )
        claves_extra_json += (
            "capitulos (lista de objetos con las claves 'tiempo' (string, mismo formato que los timestamps "
            "recibidos) y 'titulo' (string corto)), "
        )

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
                    f"{instrucciones_formato}"
                    f"{instrucciones_momentos}"
                    f"{instrucciones_capitulos}\n\n"
                    "Responde SOLO en formato JSON con las claves:\n"
                    "titulo, descripcion, "
                    "hashtags (lista de 15-20, sin el símbolo #), "
                    "etiquetas (lista de 12-20 tags de búsqueda con el límite de 500 caracteres), "
                    "frases_potentes (lista de 5 a 10 frases y contundentes para thumbnail (utilizar las frases que vienen literales dela transcripción)), "
                    f"{claves_extra_json}"
                    "(si no se te pide generar capítulos o momentos clave, simplemente omite esas claves)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Equipo del canal: {equipo}\n\n"
                    f"Contexto proporcionado por el usuario: {contexto}\n\n"
                    f"Transcripción del video: {transcript_texto}\n\n"
                    + (f"Transcripción segmentada con timestamps:\n{segments_texto}\n\n" if tiene_segments else "")
                    + f"Noticias relacionadas encontradas:\n{noticias_texto}"
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