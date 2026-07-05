"""Life timeline (history + future) composed from Vimshottari dasha periods."""
from __future__ import annotations

from datetime import datetime

DASHA_THEMES = {
    "Sun": ("authority, recognition, dealings with government or father; "
            "confidence grows but ego needs watching"),
    "Moon": ("emotional growth, home matters, popularity, mother's "
             "influence; a socially rich, changeable phase"),
    "Mars": ("action, property, competition and courage; energy is high — "
             "channel it, avoid disputes and haste"),
    "Mercury": ("study, business, writing, trade and networking; excellent "
                "for skills, exams and commerce"),
    "Jupiter": ("expansion, wisdom, children, wealth and blessings of "
                "teachers; traditionally the most benevolent period"),
    "Venus": ("love, marriage, comfort, vehicles and the arts; prosperity "
              "through relationships and refinement"),
    "Saturn": ("hard work, responsibility, slow but durable achievement; "
               "discipline is rewarded, shortcuts are punished"),
    "Rahu": ("sudden opportunities, foreign connections, ambition and "
             "unconventional paths; gains come with restlessness"),
    "Ketu": ("introspection, spirituality, research and detachment; "
             "material matters loosen so the inner life can deepen"),
}


def build_timeline(dasha: dict, birth_year: int) -> dict:
    now = datetime.now()
    past, present, future = [], None, []
    for md in dasha["mahadashas"]:
        start = datetime.strptime(md["start"], "%Y-%m-%d")
        end = datetime.strptime(md["end"], "%Y-%m-%d")
        if start.year - birth_year > 100:
            break
        entry = {
            "lord": md["lord"],
            "from": md["start"], "to": md["end"],
            "age": f"{max(0, start.year - birth_year)}–{end.year - birth_year}",
            "theme": DASHA_THEMES[md["lord"]],
        }
        if md.get("current"):
            entry["antardashas"] = md.get("antardashas", [])
            present = entry
        elif end < now:
            past.append(entry)
        else:
            future.append(entry)
    return {"past": past, "present": present, "future": future[:4],
            "note": ("Each mahadasha colours a whole chapter of life with "
                     "its lord's significations; antardashas fine-tune the "
                     "story within it.")}
