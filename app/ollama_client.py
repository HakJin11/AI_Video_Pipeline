import json

import httpx

from app.config import OLLAMA_MODEL, OLLAMA_URL

_client = httpx.Client(base_url=OLLAMA_URL, timeout=120.0)


class OllamaError(RuntimeError):
    pass


def _build_opening_prompt(keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str) -> str:
    return f"""당신은 20초 분량 짧은 영상용 한국어 대본을 쓰는 작가입니다.

키워드: {keyword}
말하는 사람: {speaker_name} ({speaker_desc})
상대방: {other_name} ({other_desc})

요구사항:
- {speaker_name}이(가) {other_name}에게 건네는 대사 한 문장만 씁니다. 아직 상대방은 대답하지 않은 상태입니다.
- 키워드의 상황과 감정이 분명히 드러나는 자연스러운 구어체 한국어 대사로 씁니다.
- 10자에서 40자 사이로, 소리 내어 읽었을 때 5~10초 정도 분량이어야 합니다.
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
- {speaker_name}이(가) 방금 들은 말에 자연스럽게 반응/대답하는 대사 한 문장만 씁니다.
- 키워드의 상황과 감정이 분명히 드러나는 자연스러운 구어체 한국어 대사로 씁니다.
- 10자에서 40자 사이로, 소리 내어 읽었을 때 5~10초 정도 분량이어야 합니다.
- 다른 설명이나 지문 없이 아래 JSON 형식으로만 답하세요.

{{"line": "{speaker_name}의 대사"}}"""


def _call_gemma(prompt: str) -> str:
    last_error: Exception | None = None
    for _ in range(2):
        resp = _client.post(
            "/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
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
    return _call_gemma(_build_opening_prompt(keyword, speaker_name, speaker_desc, other_name, other_desc))


def generate_reply_line(
    keyword: str, speaker_name: str, speaker_desc: str, other_name: str, other_desc: str, other_line: str
) -> str:
    return _call_gemma(
        _build_reply_prompt(keyword, speaker_name, speaker_desc, other_name, other_desc, other_line)
    )
