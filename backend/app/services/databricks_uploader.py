import io
import json
from app.config import settings
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(
    host=settings.databricks_host,
    token=settings.databricks_token
)

VOLUME_BASE = "/Volumes/workspace/youtube_automation/landing"

def guardar_en_volume(data: dict, video_id: str, tipo: str):
    ruta = f"{VOLUME_BASE}/{tipo}/{video_id}.json"
    contenido = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    w.files.upload(ruta, io.BytesIO(contenido), overwrite=True)
    print(f"✅ Subido a Databricks: {ruta}")