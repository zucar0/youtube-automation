import whisper
import os
import subprocess
import tempfile


def _recortar_audio(file_path: str, inicio: str | None, fin: str | None) -> str:
    """Si se especifica inicio/fin, extrae solo ese rango del video con ffmpeg
    (audio mono 16kHz, listo para Whisper) y devuelve la ruta al .wav temporal.
    Si no se especifica nada, regresa el archivo original sin tocar."""
    if not inicio and not fin:
        return file_path

    tmp_dir = tempfile.mkdtemp(prefix="recorte_")
    tmp_path = os.path.join(tmp_dir, "audio_recortado.wav")

    cmd = ["ffmpeg", "-y"]
    if inicio:
        cmd += ["-ss", inicio]
    cmd += ["-i", file_path]
    if fin:
        cmd += ["-to", fin]
    cmd += ["-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", tmp_path]

    subprocess.run(cmd, check=True, capture_output=True)
    return tmp_path


def transcribe_video(file_path: str, model_size: str = "base", inicio: str | None = None, fin: str | None = None) -> dict:
    audio_path = _recortar_audio(file_path, inicio, fin)
    model = whisper.load_model(model_size)

    result = model.transcribe(audio_path, language="es", verbose=False)

    return {
        "text": result["text"],
        "segments": result["segments"],
        "language": result["language"],
    }