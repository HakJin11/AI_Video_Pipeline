from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import db
from app.uploads import save_upload

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("")
def list_voices():
    return db.list_voices()


@router.post("")
def create_voice(
    name: str = Form(...),
    gender: str = Form("unspecified"),
    audio: UploadFile = File(...),
):
    audio_path = save_upload(audio, "voices")
    return db.create_voice(name, gender, audio_path)


@router.delete("/{voice_id}")
def delete_voice(voice_id: int):
    if not db.get_voice(voice_id):
        raise HTTPException(404, "voice not found")
    db.delete_voice(voice_id)
    return {"ok": True}
