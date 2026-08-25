import yt_dlp
import os
import uuid
from pathlib import Path
from app.config import settings


def _es_ruta_local(url: str) -> bool:
    """True si 'url' es en realidad la ruta a un archivo ya existente en disco
    (ej. una grabación local .mkv), en vez de un link de internet."""
    if url.startswith("http://") or url.startswith("https://"):
        return False
    return Path(url).expanduser().is_file()


def _usar_archivo_local(ruta: str) -> dict:
    """Usa un archivo ya grabado localmente (ej. .mkv de OBS/app web) sin pasar
    por yt-dlp. Se salta descarga porque el archivo ya está en disco."""
    path = Path(ruta).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo local: {ruta}")

    job_id = str(uuid.uuid4())
    return {
        "job_id": job_id,
        "title": path.stem,
        "duration": None,
        "file_path": str(path),
        "platform": "local",
    }


def download_video(url: str) -> dict:
    if _es_ruta_local(url):
        return _usar_archivo_local(url)

    job_id = str(uuid.uuid4())
    output_path = os.path.join(settings.downloads_path, job_id)
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "format": "best",
        "merge_output_format": "mp4",
        "quiet": False,
        "noplaylist": True,
        "cookiefile": "cookies.txt",
        "js_runtimes": {"node": {}},
        "ignoreerrors": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Asegurar extensión .mp4
        if not filename.endswith(".mp4"):
            filename = os.path.splitext(filename)[0] + ".mp4"

    return {
        "job_id": job_id,
        "title": info.get("title"),
        "duration": info.get("duration"),
        "file_path": filename,
        "platform": info.get("extractor"),
    }