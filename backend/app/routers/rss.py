from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rss_fetcher import obtener_noticias_rss
from app.services.databricks_uploader import guardar_en_volume

router = APIRouter()

class RSSRequest(BaseModel):
    feed_url: str

@router.post("/")
async def procesar_rss(request: RSSRequest):
    try:
        noticias = obtener_noticias_rss(request.feed_url)
        for noticia in noticias:
            guardar_en_volume(noticia, noticia["noticia_id"], tipo="rss")
        return {"status": "ok", "total_noticias": len(noticias), "noticias": noticias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))