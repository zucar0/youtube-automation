import requests
from app.config import settings

def obtener_metadata_youtube(video_id: str) -> dict:
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": video_id,
        "key": settings.youtube_api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get("items"):
        raise ValueError(f"No se encontró el video {video_id}")

    item = data["items"][0]
    return {
        "video_id": video_id,
        "titulo": item["snippet"]["title"],
        "fecha_publicacion": item["snippet"]["publishedAt"],
        "descripcion": item["snippet"]["description"],
        "vistas": int(item["statistics"].get("viewCount", 0)),
        "likes": int(item["statistics"].get("likeCount", 0)),
        "comentarios": int(item["statistics"].get("commentCount", 0)),
        "duracion": item["contentDetails"]["duration"],
    }