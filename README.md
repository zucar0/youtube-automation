# YouTube Automation - 

Pipeline de datos end-to-end que automatiza la ingesta, transcripción, clasificación y análisis de contenido de video relacionado con el Club América y la Selección Mexicana usando arquitectura Medallion (Bronze/Silver/Gold) en Databricks.

## 🎯 Problema que resuelve

Como creador de contenido en YouTube enfocado en Club América y en la Selección Mexicana de Fútbol, necesito identificar rápidamente qué temas, jugadores y tipo de contenido generan más engagement, para tomar mejores decisiones editoriales. Este proyecto automatiza la captura de videos (propios y de terceros usados como referencia), su transcripción, clasificación temática con IA, y análisis de performance — todo alimentando un dashboard analítico.

## 🏗️ Arquitectura
Telegram Bot / Web (Angular)
↓
FastAPI Backend
(yt-dlp, Whisper, OpenAI, YouTube Data API)
↓
Unity Catalog Volume (landing zone)
↓
Bronze (ingesta cruda)
↓
Silver (limpieza, dedup, tipado)
↓
Gold (modelo dimensional)
↓
Views semánticas → Dashboard

**Orquestación:** 
Databricks Workflow con 4 tareas encadenadas (Bronze → Silver → Gold → Fact/Views), corriendo automáticamente todos los días a las 6:00 AM (America/Mexico_City).

## 🛠️ Stack técnico

- **Backend:** FastAPI (Python 3.12)
- **Ingesta de video:** yt-dlp
- **Transcripción:** OpenAI Whisper
- **Clasificación de contenido:** OpenAI API (GPT-4o-mini)
- **Metadata de YouTube:** YouTube Data API v3
- **Bot conversacional:** python-telegram-bot
- **Data Lakehouse:** Databricks (Unity Catalog, Delta Lake, Auto Loader)
- **Orquestación:** Databricks Workflows
- **Visualización:** Databricks SQL Dashboards

## 📊 Dataset y fuentes

- **Transcripciones de video:** capturadas vía Telegram bot o API, desde YouTube y X (Twitter), con contexto manual (equipo, referencia, información relevante)
- **Metadata de YouTube:** vistas, likes, comentarios, duración (vía YouTube Data API v3)
- **Noticias RSS:** feed de ESPN México, filtrado por relevancia a Club América y Selección Mexicana

## 🧩 Modelo de datos (capa Gold)

| Tabla | Tipo | Descripción |
|---|---|---|
| `dim_video` | Dimensión | Catálogo de videos procesados |
| `dim_tema` | Dimensión | Temas y jugadores clasificados por IA |
| `dim_tiempo` | Dimensión | Calendario (año, mes, trimestre, día de semana) |
| `fact_video_performance` | Hechos | Vistas, likes, comentarios, engagement por video |

### Views semánticas
- `v_video_completo` — vista desnormalizada para análisis exploratorio
- `v_metricas_tema` — agregaciones de performance por tema
- `v_tendencia_mensual` — evolución de métricas en el tiempo

## 🔑 Decisiones técnicas relevantes

- **`video_id` como llave natural consistente** entre transcripción y metadata, para permitir el cruce correcto en el modelo dimensional (evitando duplicados por fan-out en los joins).
- **Filtrado de relevancia en Silver** para el feed RSS: de fuentes generales de noticias deportivas, solo se retiene contenido relacionado a Club América y México antes de llegar a Gold.
- **Dedup con `ROW_NUMBER()` + `mode("overwrite")`** en Silver para todas las fuentes, garantizando idempotencia ante reprocesos.
- **Auto Loader con `multiLine=true`** para ingesta de JSON, y `_metadata.file_path` en lugar de `input_file_name()` por restricciones de Unity Catalog en clusters serverless.
- **Doble canal de entrada (Telegram + API web)** apuntando al mismo endpoint FastAPI, permitiendo captura de contenido desde cualquier dispositivo sin duplicar lógica de backend.

## 🚀 Cómo ejecutar

### Backend
```bash
cd backend
python -m venv venv312
source venv312/Scripts/activate  # Windows: venv312\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Bot de Telegram
```bash
python -m bot.telegram_bot
```

### Variables de entorno requeridas (`.env`)
OPENAI_API_KEY=xxxx
DATABRICKS_HOST=xxxx
DATABRICKS_TOKEN=xxx
YOUTUBE_API_KEY=xxxx
TELEGRAM_BOT_TOKEN=xxxx

### Pipeline en Databricks
El Workflow `youtube_automation_pipeline` corre automáticamente vía schedule. Para ejecución manual: **Jobs & Pipelines → youtube_automation_pipeline → Run now**.

## 📈 Dashboard

Dashboard `YouTube Automation - Club América` en Databricks SQL, con KPIs de vistas totales, engagement promedio, distribución por tema y tendencia mensual.

---
*Proyecto desarrollado como capstone del bootcamp "De Cero a Data Engineer de Luciano Argolo (https://www.lucianoargolo.com/)" (Databricks SQL).*