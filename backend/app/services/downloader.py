import yt_dlp
import os
import uuid
from app.config import settings

def download_video(url: str) -> dict:
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
