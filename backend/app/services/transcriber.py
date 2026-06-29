import whisper
import os

def transcribe_video(file_path: str, model_size: str = "base") -> dict:
    model = whisper.load_model(model_size)
    
    result = model.transcribe(file_path, language="es")
    
    return {
        "text": result["text"],
        "segments": result["segments"],
        "language": result["language"],
    }