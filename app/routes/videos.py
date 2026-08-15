import asyncio
import copy
import json
import random
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import comfy_client, db, jobs
from app.config import MEDIA_DIR, VIDEOS_DIR, WORKFLOWS_DIR
from app.prompt_builder import build_ltx_prompt
from app.routes.voice_lines import generate_voice_line
from app.schemas import VideoCreate

router = APIRouter(prefix="/api/videos", tags=["videos"])

_TEMPLATE = json.loads((WORKFLOWS_DIR / "video.json").read_text(encoding="utf-8"))


@router.get("")
def list_videos():
    return db.list_videos()


def _run_video_generation(
    video_id: int,
    composite: dict,
    char1: dict,
    char2: dict,
    bg: dict,
    line1: str,
    line2: str,
    voice_line1: dict,
    voice_line2: dict,
    duration_sec: int,
    situation: str | None,
) -> dict:
    try:
        db.update_video_status(video_id, "running")

        prompt_text = build_ltx_prompt(
            char1["name"],
            char1["description"],
            char2["name"],
            char2["description"],
            bg["description"],
            line1,
            line2,
            duration_sec,
            situation,
        )

        graph = copy.deepcopy(_TEMPLATE)
        graph["269"]["inputs"]["image"] = comfy_client.copy_to_comfy_input(MEDIA_DIR / composite["image_path"])
        graph["276"]["inputs"]["audio"] = comfy_client.copy_to_comfy_input(MEDIA_DIR / voice_line1["audio_path"])
        graph["350"]["inputs"]["audio"] = comfy_client.copy_to_comfy_input(MEDIA_DIR / voice_line2["audio_path"])
        graph["340:319"]["inputs"]["value"] = prompt_text
        graph["340:331"]["inputs"]["value"] = duration_sec
        graph["340:285"]["inputs"]["noise_seed"] = random.randint(0, 2**48 - 1)
        graph["340:286"]["inputs"]["noise_seed"] = random.randint(0, 2**48 - 1)

        prompt_id = comfy_client.queue_prompt(graph)
        outputs = comfy_client.wait_for_outputs(prompt_id, timeout=1800, poll_interval=5)

        dest = VIDEOS_DIR / f"{video_id}_{uuid4().hex}.mp4"
        comfy_client.save_output_to(outputs, dest, media_keys=["video", "videos", "gifs", "images"])

        db.update_video_status(video_id, "done", video_path=f"videos/{dest.name}")
        return db.get_video(video_id)
    except Exception as exc:  # noqa: BLE001 - persist failure for the polling client
        db.update_video_status(video_id, "error", error_message=str(exc))
        raise


@router.post("")
async def create_video(payload: VideoCreate):
    composite = db.get_composite(payload.composite_id)
    dialogue = db.get_dialogue(payload.dialogue_id)
    if not (composite and dialogue):
        raise HTTPException(404, "composite or dialogue not found")

    char1 = db.get_character(composite["character1_id"])
    char2 = db.get_character(composite["character2_id"])
    bg = db.get_background(composite["background_id"])

    voice_line1 = await asyncio.to_thread(generate_voice_line, dialogue["line1"], payload.voice1_id)
    voice_line2 = await asyncio.to_thread(generate_voice_line, dialogue["line2"], payload.voice2_id)

    video_row = await asyncio.to_thread(
        db.create_video,
        payload.composite_id,
        payload.dialogue_id,
        voice_line1["id"],
        voice_line2["id"],
        payload.duration_sec,
    )

    job_id = jobs.start_job(
        _run_video_generation,
        video_row["id"],
        composite,
        char1,
        char2,
        bg,
        dialogue["line1"],
        dialogue["line2"],
        voice_line1,
        voice_line2,
        payload.duration_sec,
        dialogue["keyword"],
    )
    return {"video_id": video_row["id"], "job_id": job_id}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job
