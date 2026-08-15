from app.config import MANUAL_DIALOGUE_KEYWORD as _MANUAL_KEYWORD


def gendered_ref(name: str, gender: str | None) -> str:
    """A visually-groundable reference the model can actually check against the image
    (unlike an arbitrary name), paired with the name for readability."""
    if gender == "male":
        return f"the man ({name})"
    if gender == "female":
        return f"the woman ({name})"
    return name


def paired_refs(name1: str, gender1: str | None, name2: str, gender2: str | None) -> tuple[str, str]:
    """Only use gendered phrasing when it actually disambiguates the pair (different, known
    genders) — two men both called "the man" would be worse than using their names."""
    if gender1 in ("male", "female") and gender2 in ("male", "female") and gender1 != gender2:
        return gendered_ref(name1, gender1), gendered_ref(name2, gender2)
    return name1, name2


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
    char1_gender: str | None = None,
    char2_gender: str | None = None,
) -> str:
    """Build the structured LTX text-to-video prompt, embedding the gemma-generated dialogue
    lines (and the keyword/situation behind them) so mood and lip-sync timing both match
    who is actually speaking, when, and why. t1/t2 are each speaker's actual measured TTS
    duration in seconds, so the described timing matches the real audio and nothing gets cut."""
    duration_sec = t1 + t2
    ref1, ref2 = paired_refs(char1_name, char1_gender, char2_name, char2_gender)

    has_situation = bool(situation) and situation != _MANUAL_KEYWORD
    situation_clause = f", in a moment about {situation}" if has_situation else ""

    paragraph = (
        f"A two-shot scene of {ref1} and {ref2} in {background_desc}{situation_clause}. "
        f"{ref1} speaks first with natural lip movement, while {ref2}'s mouth stays fully "
        f"closed and motionless, listening attentively. After {ref1} finishes, {ref2} responds "
        f"with natural lip movement, while {ref1}'s mouth stays fully closed and motionless, reacting "
        f"to what was said. At no point do both people's mouths move at the same time. The static camera "
        f"captures both of them in a medium two-shot, both faces clearly visible throughout, the whole "
        f"exchange finishing within about {duration_sec} seconds."
    )

    situation_line = f"situation: {situation}\n" if has_situation else ""

    return (
        f"{paragraph}\n\n"
        f"{situation_line}"
        f"scene: {background_desc}\n"
        f"character: {ref1} — {char1_desc}, and {ref2} — {char2_desc}\n"
        f'action: First ~{t1} seconds: {ref1} steps or shifts weight slightly while speaking ("{line1}"), '
        f"natural lip movement, hand or head gesture matching the emotion of the line; {ref2}'s mouth stays "
        f"fully closed and motionless, listening with a small continuous motion such as a nod or slight sway, no "
        f'lip movement. Remaining ~{t2} seconds: {ref2} shifts posture or gestures while speaking ("{line2}"), '
        f"natural lip movement, hand or head gesture matching the emotion of the line; {ref1}'s mouth stays "
        f"fully closed and motionless, reacting with a small continuous motion such as a nod or slight sway, no "
        f"lip movement.\n"
        f"audio: sequential dialogue — {ref1}'s line first (about {t1} seconds), then {ref2}'s "
        f"reply (about {t2} seconds); lip movement strictly synced to each speaker's own segment only.\n"
        f"camera: Static medium two-shot, both faces fully visible, no zoom or pan, matching the natural "
        f"pacing of the speech."
    )
