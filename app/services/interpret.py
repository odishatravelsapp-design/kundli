"""Rule-based interpretation engine (free, offline) with optional LLM narrative."""
from __future__ import annotations

from ..core.astro import SIGNS
from . import llm, retrieval

HOUSE_THEMES = {
    1: "self, body, personality and life direction",
    2: "wealth, family, food and speech",
    3: "courage, siblings, communication and short journeys",
    4: "home, mother, land, vehicles and inner peace",
    5: "children, intellect, creativity and past-life merit",
    6: "health, service, debts, competition and enemies",
    7: "marriage, partnership and public dealings",
    8: "longevity, transformation, occult and inheritance",
    9: "fortune, dharma, father, guru and long journeys",
    10: "career, status, karma and public achievement",
    11: "gains, income, elder siblings and social circle",
    12: "expenditure, foreign lands, sleep and liberation (moksha)",
}

PLANET_NATURE = {
    "Sun": "soul, authority, father, vitality and government",
    "Moon": "mind, emotions, mother and popularity",
    "Mars": "energy, courage, land, brothers and technical skill",
    "Mercury": "intellect, speech, commerce and analysis",
    "Jupiter": "wisdom, wealth, children, dharma and teachers",
    "Venus": "love, comfort, arts, spouse and vehicles",
    "Saturn": "discipline, longevity, labour, delay and justice",
    "Rahu": "obsession, foreign influence, sudden rise and unconventional paths",
    "Ketu": "detachment, spirituality, research and liberation",
}

LAGNA_TEXT = {
    0: "Aries lagna gives a pioneering, energetic and direct nature; a born initiator who must guard against impatience.",
    1: "Taurus lagna gives a steady, patient and comfort-loving nature with strong practical and financial sense.",
    2: "Gemini lagna gives a curious, communicative and adaptable mind, skilled at many things at once.",
    3: "Cancer lagna gives a sensitive, nurturing and intuitive temperament deeply tied to home and family.",
    4: "Leo lagna gives dignity, generosity and natural leadership with a need for recognition.",
    5: "Virgo lagna gives an analytical, service-oriented and detail-perfect nature; health and routines matter.",
    6: "Libra lagna gives charm, diplomacy and a strong sense of fairness; partnerships shape the life.",
    7: "Scorpio lagna gives intensity, determination and penetrating insight; transformation is a life theme.",
    8: "Sagittarius lagna gives optimism, philosophical bent and love of freedom, teaching and travel.",
    9: "Capricorn lagna gives ambition, patience and organisational mastery; success builds slowly but surely.",
    10: "Aquarius lagna gives originality, humanitarian ideals and an independent, sometimes unconventional mind.",
    11: "Pisces lagna gives compassion, imagination and spiritual depth; boundaries need conscious care.",
}


def rule_based_report(chart: dict, dasha: dict, yogas: list,
                      dosha: dict) -> dict:
    asc = chart["ascendant"]
    lines = [LAGNA_TEXT[asc["sign"]]]
    lines.append(
        f"The Moon is in {chart['moon_sign_name']} in "
        f"{chart['moon_nakshatra']['name']} nakshatra (pada "
        f"{chart['moon_nakshatra']['pada']}), colouring the mind with the "
        f"qualities of that star.")

    placements = []
    for p in chart["planets"]:
        text = (f"{p['name']} in the {_ord(p['house'])} house "
                f"({p['sign_name']}) links {PLANET_NATURE[p['name']]} with "
                f"{HOUSE_THEMES[p['house']]}.")
        if p["dignity"] == "exalted":
            text += " Being exalted, it gives its best results."
        elif p["dignity"] == "debilitated":
            text += " Being debilitated, results come after struggle and maturity."
        elif p["dignity"] == "own sign":
            text += " In its own sign it is strong and self-reliant."
        if p["retrograde"]:
            text += " Retrograde motion internalises and intensifies its effects."
        placements.append(text)

    cur = dasha.get("current_mahadasha")
    dasha_line = None
    if cur:
        ad = dasha.get("current_antardasha")
        dasha_line = (f"Currently running {cur} mahadasha"
                      + (f" with {ad} antardasha" if ad else "")
                      + f" — the themes of {PLANET_NATURE.get(cur, cur)} "
                        "dominate this period of life.")

    return {
        "summary": lines,
        "placements": placements,
        "dasha_note": dasha_line,
        "yogas": yogas,
        "mangal_dosha": dosha,
    }


def _ord(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


async def ai_narrative(chart: dict, dasha: dict, yogas: list, dosha: dict,
                       panchanga: dict, name: str, language: str = "en") -> dict:
    """LLM narrative grounded with BM25-retrieved classical passages."""
    query = " ".join(
        [chart["ascendant"]["sign_name"] + " lagna",
         chart["moon_nakshatra"]["name"],
         dasha.get("current_mahadasha") or ""]
        + [f"{p['name']} {_ord(p['house'])} house" for p in chart["planets"]])
    passages = retrieval.retrieve(query, k=8)

    facts = {
        "name": name,
        "lagna": chart["ascendant"]["sign_name"],
        "moon": f"{chart['moon_sign_name']} / {chart['moon_nakshatra']['name']} pada {chart['moon_nakshatra']['pada']}",
        "placements": [
            f"{p['name']}: {p['sign_name']} (house {p['house']}, {p['dignity']}"
            + (", retrograde" if p["retrograde"] else "") + ")"
            for p in chart["planets"]],
        "current_dasha": f"{dasha.get('current_mahadasha')} MD / {dasha.get('current_antardasha')} AD",
        "yogas": [y["name"] for y in yogas],
        "manglik": dosha["manglik"],
        "panchanga": f"{panchanga['tithi']['paksha']} {panchanga['tithi']['name']}, "
                     f"{panchanga['vaara']['name']}, Odia masa {panchanga['odia_masa']['name']}",
    }
    lang_line = ("Respond in Odia (ଓଡ଼ିଆ) language." if language == "or"
                 else "Respond in English.")
    system = (
        "You are an experienced Vedic astrologer from Odisha, India, versed "
        "in Parashari jyotisha and Odia traditions (Jagannath culture, Odia "
        "panchanga). Write a warm, specific, non-fatalistic reading. Never "
        "predict death or disaster; frame challenges with remedies. "
        + lang_line)
    prompt = (
        "Chart facts (already computed, treat as ground truth):\n"
        f"{facts}\n\n"
        "Relevant classical passages:\n"
        + "\n".join(f"- {p['text']}" for p in passages)
        + "\n\nWrite a structured reading: (1) personality, (2) career & "
          "wealth, (3) relationships & family, (4) health, (5) current dasha "
          "period — what the past few years brought and what the coming "
          "years favour, (6) simple traditional remedies. Keep it under 600 words.")
    text = await llm.generate(prompt, system=system)
    return {"ai": text is not None, "narrative": text,
            "retrieved_passages": passages}
