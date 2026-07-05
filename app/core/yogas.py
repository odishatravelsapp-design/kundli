"""Detection of classical yogas in the birth chart."""
from __future__ import annotations

KENDRA = {1, 4, 7, 10}

MAHAPURUSHA = {  # planet -> yoga name
    "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
    "Venus": "Malavya", "Saturn": "Sasa",
}


def detect_yogas(chart: dict) -> list[dict]:
    planets = {p["name"]: p for p in chart["planets"]}
    asc_sign = chart["ascendant"]["sign"]
    moon_sign = chart["moon_sign"]
    yogas = []

    def house_from(sign: int, ref: int) -> int:
        return (sign - ref) % 12 + 1

    # Gajakesari: Jupiter in a kendra from the Moon
    if house_from(planets["Jupiter"]["sign"], moon_sign) in KENDRA:
        yogas.append({
            "name": "Gajakesari Yoga",
            "text": "Jupiter in a kendra from the Moon — intelligence, "
                    "reputation, lasting prosperity and respect from elders.",
        })

    # Budhaditya: Sun + Mercury in same sign
    if planets["Sun"]["sign"] == planets["Mercury"]["sign"]:
        yogas.append({
            "name": "Budhaditya Yoga",
            "text": "Sun and Mercury conjunct — sharp intellect, skill in "
                    "communication, administrative ability.",
        })

    # Chandra-Mangala: Moon + Mars together or in mutual aspect (7th)
    hm = house_from(planets["Mars"]["sign"], moon_sign)
    if hm in (1, 7):
        yogas.append({
            "name": "Chandra-Mangala Yoga",
            "text": "Moon and Mars combination — drive to earn, "
                    "entrepreneurial energy; keep the temper in check.",
        })

    # Pancha Mahapurusha yogas
    for planet, yname in MAHAPURUSHA.items():
        p = planets[planet]
        if p["dignity"] in ("own sign", "exalted") and p["house"] in KENDRA:
            yogas.append({
                "name": f"{yname} Yoga (Pancha Mahapurusha)",
                "text": f"{planet} strong in a kendra — marked "
                        f"{'courage and leadership' if planet == 'Mars' else ''}"
                        f"{'intellect and wit' if planet == 'Mercury' else ''}"
                        f"{'wisdom and righteousness' if planet == 'Jupiter' else ''}"
                        f"{'refinement, comfort and artistic sense' if planet == 'Venus' else ''}"
                        f"{'discipline, authority and endurance' if planet == 'Saturn' else ''}.",
            })

    # Neecha Bhanga hint (debilitated planet whose dispositor is strong)
    for name, p in planets.items():
        if p["dignity"] == "debilitated":
            yogas.append({
                "name": f"{name} debilitated",
                "text": f"{name} is debilitated in {p['sign_name']} — its "
                        "significations need conscious effort; check for "
                        "Neecha Bhanga (cancellation) with an astrologer.",
            })

    # Kemadruma check: no planet (excl. Sun/nodes) in 2nd/12th from Moon
    others = [p for n, p in planets.items()
              if n not in ("Moon", "Sun", "Rahu", "Ketu")]
    second = (moon_sign + 1) % 12
    twelfth = (moon_sign - 1) % 12
    if not any(p["sign"] in (second, twelfth) for p in others):
        yogas.append({
            "name": "Kemadruma Yoga",
            "text": "No planets flank the Moon — phases of loneliness or "
                    "fluctuating fortunes; mitigated if the Moon is aspected "
                    "by benefics or in a kendra.",
        })

    return yogas
