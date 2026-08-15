import copy
import shutil
import time
import uuid
from pathlib import Path

import httpx

from app.config import COMFYUI_INPUT_DIR, COMFYUI_OUTPUT_DIR, COMFYUI_URL

_client = httpx.Client(base_url=COMFYUI_URL, timeout=30.0)


class ComfyError(RuntimeError):
    pass


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
