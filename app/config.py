from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

MEDIA_DIR = BASE_DIR / "media"
CHARACTERS_DIR = MEDIA_DIR / "characters"
BACKGROUNDS_DIR = MEDIA_DIR / "backgrounds"
COMPOSITES_DIR = MEDIA_DIR / "composites"
VOICES_DIR = MEDIA_DIR / "voices"
VOICELINES_DIR = MEDIA_DIR / "voicelines"
VIDEOS_DIR = MEDIA_DIR / "videos"

FRONTEND_DIR = BASE_DIR / "frontend"
WORKFLOWS_DIR = Path(__file__).resolve().parent / "workflows"

COMFYUI_URL = "http://127.0.0.1:8188"
COMFYUI_INPUT_DIR = Path(
    r"C:\Users\DSU\AppData\Local\Comfy-Desktop\ComfyUI-Shared\input"
)
COMFYUI_OUTPUT_DIR = Path(
    r"C:\Users\DSU\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output"
)

OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "gemma4:12b"

DEFAULT_VIDEO_DURATION_SEC = 20
MANUAL_DIALOGUE_KEYWORD = "직접 입력"
FFPROBE_PATH = r"C:\ffmpeg\bin\ffprobe.exe"

ALL_MEDIA_DIRS = [
    DATA_DIR,
    CHARACTERS_DIR,
    BACKGROUNDS_DIR,
    COMPOSITES_DIR,
    VOICES_DIR,
    VOICELINES_DIR,
    VIDEOS_DIR,
]


def ensure_dirs() -> None:
    for d in ALL_MEDIA_DIRS:
        d.mkdir(parents=True, exist_ok=True)
