import asyncio
from urllib.parse import quote
from app.services.rss_fetcher import obtener_noticias_rss

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es-419&gl=MX&ceid=MX:es-419"

EQUIPO_KEYWORDS = {
    "america": "Club América",
    "seleccion": "Selección Mexicana",
}


def _construir_query(equipo: str, contexto: str) -> str:
    equipo_texto = EQUIPO_KEYWORDS.get(equipo, equipo)
    query = f"{equipo_texto} {contexto}".strip()
    return quote(query)


def _separar_titulo_y_medio(titulo_completo: str) -> tuple[str, str]:
    if " - " in titulo_completo:
        partes = titulo_completo.rsplit(" - ", 1)
        return partes[0].strip(), partes[1].strip()
    return titulo_completo.strip(), "Desconocido"


async def buscar_notas_similares(equipo: str, contexto: str, max_resultados: int = 5) -> list[dict]:
    query = _construir_query(equipo, contexto)
    feed_url = GOOGLE_NEWS_RSS.format(query=query)

    loop = asyncio.get_event_loop()
    noticias = await loop.run_in_executor(None, obtener_noticias_rss, feed_url)

    resultado = []
    for n in noticias[:max_resultados]:
        titulo_limpio, medio_real = _separar_titulo_y_medio(n["titulo"])
        resultado.append({
            "titulo": titulo_limpio,
            "fuente": medio_real,
            "resumen": n["resumen"],
        })
    return resultado