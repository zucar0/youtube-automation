from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "YouTube Automation API"
    debug: bool = True
    anthropic_api_key: str = ""
    google_credentials_path: str = ""
    google_drive_folder_id: str = ""
    google_sheet_id: str = ""
    downloads_path: str = "downloads"

    class Config:
        env_file = ".env"

settings = Settings()