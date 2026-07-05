"""Palmistry (Hasta Samudrika Shastra) service.

Two modes, both free by default:
- AI vision mode: if a vision-capable LLM key is configured (Anthropic /
  OpenAI / Gemini), the captured palm photo is analysed directly.
- Guided mode (always available, zero cost): the user answers a short
  questionnaire about their visible lines and a rule-based Samudrika
  reading is composed.
"""
from __future__ import annotations

from . import llm

PALM_SYSTEM = (
    "You are a traditional Indian palmist (Hasta Samudrika Shastra) from "
    "Odisha. Look at the palm image and describe: heart line, head line, "
    "life line, fate line if visible, mounts, and hand shape. Give a warm, "
    "constructive reading covering emotions, intellect, vitality, career "
    "and relationships. Be honest if the image is unclear and say what "
    "would help (lighting, angle). Never predict death, illness or "
    "disasters. End with one practical piece of advice.")

QUESTIONS = [
    {"id": "heart", "q": "How does your heart line (topmost major line, under the fingers) look?",
     "options": {"long_curved": "long and curved, reaching towards the index finger",
                 "straight": "fairly straight, ending under the middle finger",
                 "short": "short or faint",
                 "chained": "chained / broken in places"}},
    {"id": "head", "q": "How does your head line (middle major line) look?",
     "options": {"long_straight": "long and straight across the palm",
                 "sloping": "sloping down towards the wrist",
                 "short": "short, ending under the middle finger",
                 "deep": "deep and clearly marked"}},
    {"id": "life", "q": "How does your life line (curving around the thumb) look?",
     "options": {"long_deep": "long, deep, sweeping wide around the thumb",
                 "close_thumb": "hugging close to the thumb",
                 "broken": "with breaks or islands",
                 "double": "doubled / with a parallel sister line"}},
    {"id": "fate", "q": "Is there a fate line (vertical line up the centre of the palm)?",
     "options": {"strong": "yes, clear from wrist to middle finger",
                 "starts_middle": "yes, but starting midway up the palm",
                 "faint": "faint or fragmented",
                 "none": "no visible fate line"}},
]

READINGS = {
    "heart": {
        "long_curved": "A long, curved heart line shows a warm, expressive and openly affectionate nature; you love wholeheartedly.",
        "straight": "A straighter heart line shows measured, loyal affection — you express love through actions more than words.",
        "short": "A short heart line points to a private emotional life; you open up to very few, but deeply.",
        "chained": "A chained heart line shows sensitivity and emotional ups and downs in youth that mature into empathy.",
    },
    "head": {
        "long_straight": "A long straight head line shows logical, structured thinking — good for administration, law, engineering and commerce.",
        "sloping": "A sloping head line shows imagination and creativity — arts, writing, design and research suit you.",
        "short": "A short head line shows quick, decisive practical thinking; you act rather than overanalyse.",
        "deep": "A deep clear head line shows excellent concentration and memory.",
    },
    "life": {
        "long_deep": "A long, wide-sweeping life line shows strong vitality, enthusiasm and an adventurous approach to life.",
        "close_thumb": "A life line close to the thumb suggests you conserve energy — build stamina with regular routine, yoga and rest.",
        "broken": "Breaks in the life line mark major life changes and relocations rather than danger — each break is a new chapter.",
        "double": "A sister line beside the life line is a classical mark of protection and strong recuperative power.",
    },
    "fate": {
        "strong": "A clear fate line from the wrist shows an early sense of direction and a steadily building career.",
        "starts_middle": "A fate line starting mid-palm shows success established by your own efforts after the late twenties.",
        "faint": "A faint fate line means a self-made, flexible path — freedom to change direction is your strength.",
        "none": "Absence of a fate line is common and simply means your path is written by choices, not fixed tracks.",
    },
}


async def read_palm_image(image_jpeg_b64: str, extra_context: str = "",
                          language: str = "en") -> dict:
    lang = "Respond in Odia (ଓଡ଼ିଆ)." if language == "or" else "Respond in English."
    text = await llm.generate(
        "Read this palm photograph. " + extra_context,
        system=PALM_SYSTEM + " " + lang,
        image_jpeg_b64=image_jpeg_b64,
    )
    if text is None:
        return {"ai": False, "narrative": None,
                "message": ("No vision AI configured. Use guided mode "
                            "(answer the line questions) or add an API key "
                            "in .env to enable photo analysis."),
                "questions": QUESTIONS}
    return {"ai": True, "narrative": text}


def read_palm_guided(answers: dict) -> dict:
    parts = []
    for key, choice in answers.items():
        r = READINGS.get(key, {}).get(choice)
        if r:
            parts.append(r)
    if not parts:
        return {"reading": [], "questions": QUESTIONS,
                "message": "Answer the questions to receive a reading."}
    parts.append(
        "Samudrika Shastra reminds us the palm changes with our karma — "
        "lines record tendencies, and conscious effort rewrites them.")
    return {"reading": parts}
