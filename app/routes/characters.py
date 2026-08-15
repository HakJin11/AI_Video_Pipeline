from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import db
from app.uploads import save_upload

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("")
def list_characters():
    return db.list_characters()


@router.post("")
def create_character(
    name: str = Form(...),
    description: str = Form(...),
    gender: str = Form("unspecified"),
    image: UploadFile = File(...),
):
    image_path = save_upload(image, "characters")
    return db.create_character(name, description, gender, image_path)


@router.delete("/{character_id}")
def delete_character(character_id: int):
    if not db.get_character(character_id):
        raise HTTPException(404, "character not found")
    db.delete_character(character_id)
    return {"ok": True}
