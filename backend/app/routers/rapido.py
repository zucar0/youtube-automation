import asyncio
from functools import partial
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.databricks_sql_client import guardar_en_cola_pendiente, actualizar_propuesta_generada
from app.services.metadata_router import obtener_metadata_liviana, detectar_fuente

from app.services.news_search import buscar_notas_similares
from app.services.classifier import generar_propuesta_rapida
from app.models.schemas import PendingDownload

router = APIRouter()


class RapidoRequest(BaseModel):
    url: str
    equipo: str
    texto_referencia: str
    tipo_contenido: str = "short"
    chat_id: str
    usuario: str = "toño"


@router.post("/proponer")
async def proponer_contenido(request: RapidoRequest):
    fuente = detectar_fuente(request.url)

    # 1. Metadata liviana (sin descarga)
    metadata = await obtener_metadata_liviana(request.url)

    # 2. Noticias relacionadas vía Google News RSS
    notas_similares = await buscar_notas_similares(request.equipo, request.texto_referencia)

    # 3. Propuesta de contenido con GPT-4o-mini (síncrona -> threadpool)
    loop = asyncio.get_event_loop()
    propuesta_raw = await loop.run_in_executor(
        None,
        partial(
            generar_propuesta_rapida,
            equipo=request.equipo,
            contexto=request.texto_referencia,
            tipo_contenido=request.tipo_contenido,
            metadata=metadata,
            notas_similares=notas_similares,
        )
    )

    # 4. Encolar la URL para que el pipeline pesado (Databricks) la descargue después
    registro_id = await guardar_en_cola_pendiente(PendingDownload(
        url=request.url,
        fuente=fuente,
        equipo=request.equipo,
        contexto=request.texto_referencia,
        chat_id=request.chat_id,
        metadata_liviana=metadata,
    ))

    propuesta = json.loads(propuesta_raw)
    await actualizar_propuesta_generada(registro_id, propuesta)

    return {
        "registro_id": registro_id,
        "fuente_detectada": fuente,
        "metadata": metadata,
        "propuesta": propuesta_raw,
    }