import feedparser
import hashlib
from datetime import datetime, timezone

def obtener_noticias_rss(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    noticias = []

    for entry in feed.entries:
        # Generamos un ID único y estable a partir del link de la noticia
        noticia_id = hashlib.md5(entry.link.encode()).hexdigest()

        noticias.append({
            "noticia_id": noticia_id,
            "titulo": entry.get("title", ""),
            "link": entry.get("link", ""),
            "resumen": entry.get("summary", ""),
            "fecha_publicacion": entry.get("published", ""),
            "fuente": feed.feed.get("title", feed_url),
            "fecha_ingesta": datetime.now(timezone.utc).isoformat(),
        })

    return noticias