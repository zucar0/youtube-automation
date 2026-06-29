from pydantic import BaseModel
from enum import Enum
from typing import Optional

class ChannelType(str, Enum):
    america = "america"
    seleccion = "seleccion"
    futbol_general = "futbol_general"

class DownloadRequest(BaseModel):
    url: str
    channel_type: ChannelType

class VideoMetadata(BaseModel):
    title: str
    description: str
    hashtags: list[str]
    tags: list[str]

class VideoJob(BaseModel):
    job_id: str
    url: str
    channel_type: ChannelType
    status: str                        # pending | downloaded | transcribed | reviewed | published
    file_path: Optional[str] = None
    transcript: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    drive_url: Optional[str] = None