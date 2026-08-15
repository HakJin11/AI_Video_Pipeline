import copy
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

import httpx

from app.config import COMFYUI_INPUT_DIR, COMFYUI_OUTPUT_DIR, COMFYUI_URL, FFPROBE_PATH

_client = httpx.Client(base_url=COMFYUI_URL, timeout=30.0)

# ComfyUI has one GPU and processes its queue serially, but our FastAPI routes can call in from
# multiple threads at once (e.g. the two per-character TTS calls fired together). Submitting two
# prompts back-to-back without waiting risks interleaving with in-node state like
# unload_models, degrading whichever job wasn't first. Serialize every submit+wait cycle through
# this app so ComfyUI only ever works on one of our jobs at a time.
_comfy_lock = threading.Lock()


class ComfyError(RuntimeError):
    pass


def audio_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def copy_to_comfy_input(src_path: Path) -> str:
    """Copy a local file into ComfyUI's input folder under a unique name, return that filename."""
    unique_name = f"{uuid.uuid4().hex}{src_path.suffix.lower()}"
    dest = COMFYUI_INPUT_DIR / unique_name
    shutil.copyfile(src_path, dest)
    return unique_name


def queue_prompt(graph: dict) -> str:
    payload = {"prompt": copy.deepcopy(graph), "client_id": uuid.uuid4().hex}
    resp = _client.post("/prompt", json=payload)
    if resp.status_code != 200:
        raise ComfyError(f"ComfyUI /prompt failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    if "prompt_id" not in data:
        raise ComfyError(f"ComfyUI /prompt did not return prompt_id: {data}")
    return data["prompt_id"]


def wait_for_outputs(prompt_id: str, timeout: float = 300.0, poll_interval: float = 2.0) -> dict:
    """Poll /history/{prompt_id} until the job finishes. Returns the outputs mapping {node_id: {...}}."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = _client.get(f"/history/{prompt_id}")
        if resp.status_code == 200:
            history = resp.json()
            entry = history.get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise ComfyError(f"ComfyUI job {prompt_id} failed: {status}")
                outputs = entry.get("outputs")
                if outputs:
                    return outputs
        time.sleep(poll_interval)
    raise ComfyError(f"ComfyUI job {prompt_id} timed out after {timeout}s")


def run_prompt_and_wait(graph: dict, timeout: float = 300.0, poll_interval: float = 2.0) -> dict:
    """Queue a graph and wait for its outputs, holding the ComfyUI lock for the whole cycle so no
    other job from this app can be submitted in between."""
    with _comfy_lock:
        prompt_id = queue_prompt(graph)
        return wait_for_outputs(prompt_id, timeout=timeout, poll_interval=poll_interval)


def _find_output_file(filename: str, subfolder: str) -> Path:
    candidate = COMFYUI_OUTPUT_DIR / subfolder / filename if subfolder else COMFYUI_OUTPUT_DIR / filename
    if candidate.exists():
        return candidate
    matches = list(COMFYUI_OUTPUT_DIR.rglob(filename))
    if matches:
        return matches[0]
    raise ComfyError(f"Could not locate ComfyUI output file: {filename} (subfolder={subfolder})")


def collect_first_file(outputs: dict, media_keys: str | list[str]) -> Path:
    """Find the first output file matching any of media_keys (e.g. 'images', 'audio', 'video(s)')."""
    keys = [media_keys] if isinstance(media_keys, str) else media_keys
    for node_output in outputs.values():
        for key in keys:
            files = node_output.get(key)
            if files:
                f = files[0]
                return _find_output_file(f["filename"], f.get("subfolder", ""))
    raise ComfyError(f"No output found for keys {keys} in ComfyUI result: {outputs}")


def save_output_to(outputs: dict, dest_path: Path, media_keys: str | list[str] = "images") -> Path:
    src = collect_first_file(outputs, media_keys)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest_path)
    return dest_path
