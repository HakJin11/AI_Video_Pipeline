import json

import httpx

from app.config import DEFAULT_VIDEO_DURATION_SEC, OLLAMA_MODEL, OLLAMA_URL

_client = httpx.Client(base_url=OLLAMA_URL, timeout=180.0)

_LINE_SECONDS = DEFAULT_VIDEO_DURATION_SEC // 2
_MIN_CHARS = _LINE_SECONDS * 4
_MAX_CHARS = _LINE_SECONDS * 8


class OllamaError(RuntimeError):
    pass


def _length_guidance() -> str:
    return (
        f"- 이 대사는 영상에서 약 {_LINE_SECONDS}초 분량을 채워야 합니다. 소리 내어 자연스럽게 말했을 때 "
        f"{_LINE_SECONDS}초 정도 걸리도록 {_MIN_CHARS}자에서 {_MAX_CHARS}자 사이로, 한두 문장으로 충분히 풀어서 씁니다."
    )


def _build_opening_prompt(keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str) -> str:
    return f"""당신은 20초 분량 짧은 영상용 한국어 대본을 쓰는 작가입니다.

키워드: {keyword}
말하는 사람: {speaker_name} ({speaker_desc})
상대방: {other_name} ({other_desc})

요구사항:
- {speaker_name}이(가) {other_name}에게 건네는 대사만 씁니다. 아직 상대방은 대답하지 않은 상태입니다.
- 키워드의 상황과 감정이 분명히 드러나는 자연스러운 구어체 한국어 대사로 씁니다.
{_length_guidance()}
- 다른 설명이나 지문 없이 아래 JSON 형식으로만 답하세요.

{{"line": "{speaker_name}의 대사"}}"""


def _build_reply_prompt(
    keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str, other_line: str
) -> str:
    return f"""당신은 20초 분량 짧은 영상용 한국어 대본을 쓰는 작가입니다.

키워드: {keyword}
{other_name} ({other_desc})이(가) 방금 {speaker_name}에게 이렇게 말했습니다: "{other_line}"

말하는 사람: {speaker_name} ({speaker_desc})

요구사항:
- {speaker_name}이(가) 방금 들은 말에 자연스럽게 반응/대답하는 대사를 씁니다.
- 키워드의 상황과 감정이 분명히 드러나는 자연스러운 구어체 한국어 대사로 씁니다.
{_length_guidance()}
- 다른 설명이나 지문 없이 아래 JSON 형식으로만 답하세요.

{{"line": "{speaker_name}의 대사"}}"""


def _call_gemma_json(prompt: str) -> str:
    last_error: Exception | None = None
    for _ in range(2):
        resp = _client.post(
            "/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "think": False,
                "options": {"temperature": 0.8},
            },
        )
        if resp.status_code != 200:
            raise OllamaError(f"Ollama /api/generate failed ({resp.status_code}): {resp.text}")
        raw_text = resp.json().get("response", "")
        try:
            data = json.loads(raw_text)
            line = str(data["line"]).strip()
            if not line:
                raise ValueError("empty line in response")
            return line
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            last_error = exc
            continue
    raise OllamaError(f"Failed to parse dialogue line JSON from gemma response: {last_error}")


def generate_opening_line(keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str) -> str:
    return _call_gemma_json(_build_opening_prompt(keyword, speaker_name, speaker_desc, other_name, other_desc))


def generate_reply_line(
    keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str, other_line: str
) -> str:
    return _call_gemma_json(
        _build_reply_prompt(keyword, speaker_name, speaker_desc, other_name, other_desc, other_line)
    )


def _build_video_prompt_request(
    situation: str,
    char1_name: str,
    char1_desc: str,
    char2_name: str,
    char2_desc: str,
    background_desc: str,
    line1: str,
    line2: str,
    t1: int,
    t2: int,
) -> str:
    duration_sec = t1 + t2
    return f"""You are a prompt writer for the LTX-2 image-to-video generation model. Write ONE structured video \
generation prompt in English that will be used as-is, following EXACTLY this structure and nothing else \
(no markdown, no extra commentary before or after):

<a descriptive paragraph, 3-5 sentences, describing the two-shot scene, who speaks first and who replies, \
and that only one person's mouth moves at a time while the other listens with their mouth closed>

scene: <scene description>
character: <character1 description>, and <character2 description>
action: <describe, in two segments ("First ~{t1} seconds: ..." and "Remaining ~{t2} seconds: ..."), the natural \
body language, gestures, and facial expressions each speaker shows while/after speaking, fitting the situation \
and emotional tone of their line, plus the exact spoken line in quotes>
audio: <sequencing description>
camera: <camera framing description>

STRICT RULES:
- character1's line and character2's line must appear EXACTLY as given below, character-for-character, inside \
double quotes. Do not translate, paraphrase, shorten, or alter them in any way.
- Total duration is {duration_sec} seconds: character1 speaks for about {t1} seconds, then character2 speaks for \
about {t2} seconds.
- Predict and describe natural actions, gestures, and facial expressions that fit the situation and the emotional \
tone of each line — go beyond lip movement (e.g. body posture, hand gestures, eye contact, small movements).
- Output ONLY the prompt text described above.

Inputs:
situation: {situation}
scene description: {background_desc}
character1: {char1_name} — {char1_desc}
character2: {char2_name} — {char2_desc}
character1's line (first ~{t1} seconds): "{line1}"
character2's line (remaining ~{t2} seconds): "{line2}\""""


def generate_video_prompt(
    situation: str,
    char1_name: str,
    char1_desc: str,
    char2_name: str,
    char2_desc: str,
    background_desc: str,
    line1: str,
    line2: str,
    t1: int,
    t2: int,
) -> str:
    """Ask gemma to write the full LTX prompt (scene/action/audio/camera) around the given dialogue,
    predicting fitting actions/expressions. Caller should validate line1/line2 appear verbatim and
    fall back to the deterministic template if not. t1/t2 are each speaker's actual measured TTS
    duration in seconds."""
    prompt = _build_video_prompt_request(
        situation, char1_name, char1_desc, char2_name, char2_desc, background_desc, line1, line2, t1, t2
    )
    resp = _client.post(
        "/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.7, "num_predict": 800},
        },
    )
    if resp.status_code != 200:
        raise OllamaError(f"Ollama /api/generate failed ({resp.status_code}): {resp.text}")
    text = resp.json().get("response", "").strip()
    if not text:
        raise OllamaError("gemma returned an empty video prompt")
    return text
