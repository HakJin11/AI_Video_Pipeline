from app.config import MANUAL_DIALOGUE_KEYWORD as _MANUAL_KEYWORD


def build_ltx_prompt(
    char1_name: str,
    char1_desc: str,
    char2_name: str,
    char2_desc: str,
    background_desc: str,
    line1: str,
    line2: str,
    t1: int,
    t2: int,
    situation: str | None = None,
) -> str:
    """Build the structured LTX text-to-video prompt, embedding the gemma-generated dialogue
    lines (and the keyword/situation behind them) so mood and lip-sync timing both match
    who is actually speaking, when, and why. t1/t2 are each speaker's actual measured TTS
    duration in seconds, so the described timing matches the real audio and nothing gets cut."""
    duration_sec = t1 + t2

    has_situation = bool(situation) and situation != _MANUAL_KEYWORD
    situation_clause = f", in a moment about {situation}" if has_situation else ""

    paragraph = (
        f"A two-shot scene of {char1_name} and {char2_name} in {background_desc}{situation_clause}. "
        f"{char1_name} speaks first with natural lip movement, while {char2_name}'s mouth stays fully "
        f"closed and motionless, listening attentively. After {char1_name} finishes, {char2_name} responds "
        f"with natural lip movement, while {char1_name}'s mouth stays fully closed and motionless, reacting "
        f"to what was said. At no point do both people's mouths move at the same time. The static camera "
        f"captures both of them in a medium two-shot, both faces clearly visible throughout, the whole "
        f"exchange finishing within about {duration_sec} seconds."
    )

    situation_line = f"situation: {situation}\n" if has_situation else ""

    return (
        f"{paragraph}\n\n"
        f"{situation_line}"
        f"scene: {background_desc}\n"
        f"character: {char1_desc}, and {char2_desc}\n"
        f'action: First ~{t1} seconds: {char1_name} speaks ("{line1}"), subtle natural lip movement, '
        f"expression and emotion matching the situation and the line; {char2_name}'s mouth stays fully "
        f'closed and motionless, listening, no lip movement. Remaining ~{t2} seconds: {char2_name} speaks ("{line2}"), '
        f"subtle natural lip movement, expression and emotion matching the situation and the line; "
        f"{char1_name}'s mouth stays fully closed and motionless, reacting, no lip movement.\n"
        f"audio: sequential dialogue — {char1_name}'s line first (about {t1} seconds), then {char2_name}'s "
        f"reply (about {t2} seconds); lip movement strictly synced to each speaker's own segment only.\n"
        f"camera: Static medium two-shot, both faces fully visible, no zoom or pan, matching the natural "
        f"pacing of the speech."
    )
