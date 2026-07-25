from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "YouTube Automation API"
    debug: bool = True
    anthropic_api_key: str = ""
    google_credentials_path: str = ""
    google_drive_folder_id: str = ""
    google_sheet_id: str = ""
    downloads_path: str = "downloads"
    openai_api_key: str = ""
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_http_path: str = ""
    youtube_api_key: str = ""
    telegram_bot_token: str = ""
    class Config:
        env_file = ".env"

settings = Settings()