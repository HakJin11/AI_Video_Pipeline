from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR, MEDIA_DIR, ensure_dirs
from app.db import init_db
from app.routes import (
    backgrounds,
    characters,
    composites,
    dialogues,
    health,
    library_import,
    videos,
    voice_lines,
    voices,
)

ensure_dirs()
init_db()

app = FastAPI(title="AI Video Pipeline")

app.include_router(characters.router)
app.include_router(backgrounds.router)
app.include_router(composites.router)
app.include_router(dialogues.router)
app.include_router(voices.router)
app.include_router(voice_lines.router)
app.include_router(videos.router)
app.include_router(library_import.router)
app.include_router(health.router)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
