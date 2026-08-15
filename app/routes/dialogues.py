from fastapi import APIRouter, HTTPException

from app import db, ollama_client
from app.config import MANUAL_DIALOGUE_KEYWORD
from app.schemas import DialogueCreate, DialogueManualCreate, DialogueReplyRequest, DialogueUpdate

router = APIRouter(prefix="/api/dialogues", tags=["dialogues"])

KEYWORD_PRESETS = ["사랑", "결혼", "싸움", "이별", "화해", "고백", "재회", "오해"]


@router.get("")
def list_dialogues():
    return db.list_dialogues()


@router.get("/keyword-presets")
def keyword_presets():
    return KEYWORD_PRESETS


@router.post("")
def create_dialogue(payload: DialogueCreate):
    """Generate only 인물1's opening line for the keyword. 인물2 replies later via /reply."""
    char1 = db.get_character(payload.character1_id)
    char2 = db.get_character(payload.character2_id)
    if not (char1 and char2):
        raise HTTPException(404, "character not found")

    try:
        line1 = ollama_client.generate_opening_line(
            payload.keyword, char1["name"], char1["description"], char2["name"], char2["description"]
        )
    except ollama_client.OllamaError as exc:
        raise HTTPException(502, f"Ollama dialogue generation failed: {exc}") from exc

    return db.create_dialogue(payload.keyword, payload.character1_id, payload.character2_id, line1, "")


@router.post("/manual")
def create_manual_dialogue(payload: DialogueManualCreate):
    if not (db.get_character(payload.character1_id) and db.get_character(payload.character2_id)):
        raise HTTPException(404, "character not found")
    return db.create_dialogue(
        MANUAL_DIALOGUE_KEYWORD, payload.character1_id, payload.character2_id, payload.line1, payload.line2
    )


@router.post("/{dialogue_id}/reply")
def generate_reply(dialogue_id: int, payload: DialogueReplyRequest):
    """Generate 인물2's line as a natural reply to the (possibly user-edited) 인물1 line."""
    dialogue = db.get_dialogue(dialogue_id)
    if not dialogue:
        raise HTTPException(404, "dialogue not found")
    char1 = db.get_character(dialogue["character1_id"])
    char2 = db.get_character(dialogue["character2_id"])

    try:
        line2 = ollama_client.generate_reply_line(
            dialogue["keyword"],
            char2["name"],
            char2["description"],
            char1["name"],
            char1["description"],
            payload.line1,
        )
    except ollama_client.OllamaError as exc:
        raise HTTPException(502, f"Ollama dialogue generation failed: {exc}") from exc

    return db.update_dialogue_lines(dialogue_id, payload.line1, line2)


@router.patch("/{dialogue_id}")
def update_dialogue(dialogue_id: int, payload: DialogueUpdate):
    if not db.get_dialogue(dialogue_id):
        raise HTTPException(404, "dialogue not found")
    return db.update_dialogue_lines(dialogue_id, payload.line1, payload.line2)
