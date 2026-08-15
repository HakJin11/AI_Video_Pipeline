import copy
import json
import random
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import comfy_client, db
from app.config import MEDIA_DIR, VOICELINES_DIR, WORKFLOWS_DIR
from app.schemas import VoiceLineCreate

router = APIRouter(prefix="/api/voice-lines", tags=["voice_lines"])

_TEMPLATE = json.loads((WORKFLOWS_DIR / "tts.json").read_text(encoding="utf-8"))


def generate_voice_line(text: str, voice_id: int) -> dict:
    """Return a cached voice_line for (text, voice_id), generating it via ComfyUI TTS if needed."""
    cached = db.find_voice_line(text, voice_id)
    if cached:
        return {**cached, "cached": True}

    voice = db.get_voice(voice_id)
    if not voice:
        raise HTTPException(404, "voice not found")

    graph = copy.deepcopy(_TEMPLATE)
    graph["62"]["inputs"]["audio"] = comfy_client.copy_to_comfy_input(MEDIA_DIR / voice["reference_audio_path"])
    graph["59"]["inputs"]["target_text"] = text
    graph["59"]["inputs"]["seed"] = random.randint(0, 2**48 - 1)

    prompt_id = comfy_client.queue_prompt(graph)
    outputs = comfy_client.wait_for_outputs(prompt_id, timeout=180)

    dest = VOICELINES_DIR / f"{voice_id}_{uuid4().hex}.mp3"
    comfy_client.save_output_to(outputs, dest, media_keys=["audio"])

    row = db.create_voice_line(text, voice_id, f"voicelines/{dest.name}")
    return {**row, "cached": False}


@router.post("")
def create_voice_line(payload: VoiceLineCreate):
    return generate_voice_line(payload.text, payload.voice_id)
