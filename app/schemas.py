from pydantic import BaseModel


class DialogueCreate(BaseModel):
    keyword: str
    character1_id: int
    character2_id: int


class DialogueUpdate(BaseModel):
    line1: str
    line2: str
    background_id: int | None = None


class DialogueManualCreate(BaseModel):
    character1_id: int
    character2_id: int
    line1: str
    line2: str = ""


class DialogueReplyRequest(BaseModel):
    line1: str
    background_id: int | None = None


class VoiceLineCreate(BaseModel):
    text: str
    voice_id: int


class VideoCreate(BaseModel):
    composite_id: int
    dialogue_id: int
    voice1_id: int
    voice2_id: int
    ltx_prompt: str | None = None
