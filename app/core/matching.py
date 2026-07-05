"""Ashtakoota (36 guna) marriage matching + Mangal dosha check.

Standard north/east-Indian ashtakoota as used in Odisha. A few koota
sub-tables (yoni, vashya) use the common published matrices; sources vary
slightly between traditions.
"""
from __future__ import annotations

from .astro import SIGN_LORDS, SIGNS

# --- per-nakshatra attribute tables (index 0 = Ashwini) -------------------
YONI_ANIMALS = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat",
                "Cow", "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose",
                "Lion"]
NAK_YONI = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11,
            12, 11, 13, 0, 13, 7, 1]

YONI_MATRIX = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]

GANA = ["deva", "manushya", "rakshasa"]
NAK_GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1,
            0, 2, 2, 1, 1, 0]
GANA_SCORE = {  # (boy, girl)
    (0, 0): 6, (0, 1): 6, (0, 2): 1,
    (1, 0): 5, (1, 1): 6, (1, 2): 0,
    (2, 0): 1, (2, 1): 0, (2, 2): 6,
}

NADI = ["Adi", "Madhya", "Antya"]
NAK_NADI_PATTERN = [0, 1, 2, 2, 1, 0, 0, 1, 2]  # repeats over the 27

VARNA_ORDER = ["Brahmin", "Kshatriya", "Vaishya", "Shudra"]
SIGN_VARNA = [1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0]  # by rashi index

# Vashya groups by rashi (simplified whole-sign version):
# 0 quadruped, 1 human, 2 water, 3 wild(vana), 4 keeta
SIGN_VASHYA = [0, 0, 1, 2, 3, 1, 1, 4, 1, 0, 1, 2]
VASHYA_MATRIX = [
    [2.0, 1.0, 1.0, 0.0, 1.0],
    [1.0, 2.0, 0.5, 0.0, 1.0],
    [1.0, 0.5, 2.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 2.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 2.0],
]

FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"], "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"], "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"], "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
}
ENEMIES = {
    "Sun": ["Venus", "Saturn"], "Moon": [], "Mars": ["Mercury"],
    "Mercury": ["Moon"], "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"], "Saturn": ["Sun", "Moon", "Mars"],
}


def _relation(a: str, b: str) -> str:
    if b in FRIENDS.get(a, []):
        return "friend"
    if b in ENEMIES.get(a, []):
        return "enemy"
    return "neutral"


def _maitri_score(lord_b: str, lord_g: str) -> float:
    r1, r2 = _relation(lord_b, lord_g), _relation(lord_g, lord_b)
    pair = {r1, r2}
    if lord_b == lord_g or pair == {"friend"}:
        return 5.0
    if pair == {"friend", "neutral"}:
        return 4.0
    if pair == {"neutral"}:
        return 3.0
    if pair == {"friend", "enemy"}:
        return 1.0
    if pair == {"neutral", "enemy"}:
        return 0.5
    return 0.0


def _tara_score(nak_b: int, nak_g: int) -> float:
    def bad(frm: int, to: int) -> bool:
        count = ((to - frm) % 27) % 9 + 1
        return count in (3, 5, 7)
    b1, b2 = bad(nak_g, nak_b), bad(nak_b, nak_g)
    if not b1 and not b2:
        return 3.0
    if b1 != b2:
        return 1.5
    return 0.0


def ashtakoota(boy: dict, girl: dict) -> dict:
    """boy/girl: {'moon_sign': int, 'moon_nak': int} (nak index 0-based)."""
    sb, sg = boy["moon_sign"], girl["moon_sign"]
    nb, ng = boy["moon_nak"], girl["moon_nak"]

    varna = 1.0 if SIGN_VARNA[sb] <= SIGN_VARNA[sg] else 0.0
    vashya = VASHYA_MATRIX[SIGN_VASHYA[sb]][SIGN_VASHYA[sg]]
    tara = _tara_score(nb, ng)
    yoni = float(YONI_MATRIX[NAK_YONI[nb]][NAK_YONI[ng]])
    maitri = _maitri_score(SIGN_LORDS[sb], SIGN_LORDS[sg])
    gana = float(GANA_SCORE[(NAK_GANA[nb], NAK_GANA[ng])])

    dist = (sg - sb) % 12 + 1
    dist_rev = (sb - sg) % 12 + 1
    bad_bhakoot = {dist, dist_rev} in ({2, 12}, {5, 9}, {6, 8})
    bhakoot = 0.0 if bad_bhakoot else 7.0

    nadi_b = NAK_NADI_PATTERN[nb % 9]
    nadi_g = NAK_NADI_PATTERN[ng % 9]
    nadi = 0.0 if nadi_b == nadi_g else 8.0

    meanings = {
        "Varna": "spiritual compatibility and ego balance between the couple",
        "Vashya": "mutual attraction, influence and power balance",
        "Tara": "health, wellbeing and fortune the partners bring each other",
        "Yoni": "physical and instinctive compatibility",
        "Graha Maitri": "mental friendship — how the two minds get along daily",
        "Gana": "temperament match (sattvic/rajasic/tamasic natures)",
        "Bhakoot": "prosperity, family growth and emotional stability after marriage",
        "Nadi": "progeny, genes and long-term health compatibility (heaviest weight)",
    }
    kootas = [
        {"name": "Varna", "score": varna, "max": 1,
         "detail": f"{VARNA_ORDER[SIGN_VARNA[sb]]} / {VARNA_ORDER[SIGN_VARNA[sg]]}"},
        {"name": "Vashya", "score": vashya, "max": 2, "detail": ""},
        {"name": "Tara", "score": tara, "max": 3, "detail": ""},
        {"name": "Yoni", "score": yoni, "max": 4,
         "detail": f"{YONI_ANIMALS[NAK_YONI[nb]]} / {YONI_ANIMALS[NAK_YONI[ng]]}"},
        {"name": "Graha Maitri", "score": maitri, "max": 5,
         "detail": f"{SIGN_LORDS[sb]} / {SIGN_LORDS[sg]}"},
        {"name": "Gana", "score": gana, "max": 6,
         "detail": f"{GANA[NAK_GANA[nb]]} / {GANA[NAK_GANA[ng]]}"},
        {"name": "Bhakoot", "score": bhakoot, "max": 7,
         "detail": f"rashi positions {dist}/{dist_rev}"},
        {"name": "Nadi", "score": nadi, "max": 8,
         "detail": f"{NADI[nadi_b]} / {NADI[nadi_g]}"},
    ]
    for k in kootas:
        k["meaning"] = meanings[k["name"]]
    total = sum(k["score"] for k in kootas)
    if total >= 32:
        verdict = "Excellent match"
    elif total >= 24:
        verdict = "Very good match"
    elif total >= 18:
        verdict = "Acceptable match"
    else:
        verdict = "Below the traditional threshold (18); remedies or deeper analysis advised"

    return {"kootas": kootas, "total": round(total, 1), "max": 36,
            "verdict": verdict,
            "nadi_dosha": nadi == 0.0, "bhakoot_dosha": bad_bhakoot,
            "boy_rashi": SIGNS[sb], "girl_rashi": SIGNS[sg]}


def mangal_dosha(chart: dict) -> dict:
    """Mars in 1,2,4,7,8,12 from lagna or from Moon."""
    mars = next(p for p in chart["planets"] if p["name"] == "Mars")
    asc_sign = chart["ascendant"]["sign"]
    moon_sign = chart["moon_sign"]
    dosha_houses = {1, 2, 4, 7, 8, 12}

    from_lagna = (mars["sign"] - asc_sign) % 12 + 1
    from_moon = (mars["sign"] - moon_sign) % 12 + 1
    has_lagna = from_lagna in dosha_houses
    has_moon = from_moon in dosha_houses

    # classical cancellations (a few common ones)
    cancelled = mars["dignity"] in ("own sign", "exalted")
    return {
        "manglik": (has_lagna or has_moon) and not cancelled,
        "from_lagna_house": from_lagna,
        "from_moon_house": from_moon,
        "cancellation": "Mars in own/exalted sign weakens the dosha"
        if cancelled and (has_lagna or has_moon) else None,
    }
