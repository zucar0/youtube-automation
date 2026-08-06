from databricks import sql
import uuid
import json
from datetime import datetime, timezone
from app.config import settings
from app.models.schemas import PendingDownload


def _get_connection():
    return sql.connect(
        server_hostname=settings.databricks_host,
        http_path=settings.databricks_http_path,
        access_token=settings.databricks_token,
    )


async def guardar_en_cola_pendiente(data: PendingDownload) -> str:
    registro_id = str(uuid.uuid4())
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO workspace.youtube_automation.bronze_pending_download
                (id, url, fuente, equipo, contexto, chat_id, metadata_liviana, estado, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)
            """, (
                registro_id, data.url, data.fuente, data.equipo, data.contexto,
                data.chat_id, json.dumps(data.metadata_liviana),
                datetime.now(timezone.utc)
            ))
    return registro_id

async def actualizar_propuesta_generada(registro_id: str, propuesta: dict):
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE workspace.youtube_automation.bronze_pending_download
                SET propuesta_generada = ?
                WHERE id = ?
            """, (
                json.dumps(propuesta),
                registro_id,
            ))