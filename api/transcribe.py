import os
import tempfile
from fastapi import APIRouter, UploadFile, File
from faster_whisper import WhisperModel

router_transcribe = APIRouter()
model = WhisperModel("base", device="cpu", compute_type="int8")

@router_transcribe.post("/transcribe/")
async def transcribe(audio: UploadFile = File(...)):
    content = await audio.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        segments, _ = model.transcribe(tmp_path, language="es")
        text = " ".join([seg.text for seg in segments])
    finally:
        os.remove(tmp_path)

    return {"text": text.strip()} 