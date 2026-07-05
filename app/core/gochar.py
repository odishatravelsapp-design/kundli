"""Gochar (current transits) relative to the janma rashi + Sade Sati.

Classical moon-relative transit results: each graha gives good results in
certain houses counted from the natal Moon sign. Sade Sati is Saturn's
transit through the 12th, 1st and 2nd from the janma rashi (with the
smaller dhaiya in the 4th and 8th).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .astro import SIGNS, compute_positions, julian_day_utc

TRANSIT_GOOD = {
    "Sun": {3, 6, 10, 11}, "Moon": {1, 3, 6, 7, 10, 11},
    "Mars": {3, 6, 11}, "Mercury": {2, 4, 6, 8, 10, 11},
    "Jupiter": {2, 5, 7, 9, 11}, "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "Saturn": {3, 6, 11}, "Rahu": {3, 6, 11}, "Ketu": {3, 6, 11},
}

GOOD_TEXT = {
    "Sun": "energy, recognition and official favour",
    "Moon": "emotional ease and social flow",
    "Mars": "winning drive, courage and property gains",
    "Mercury": "sharp business sense, study and communication wins",
    "Jupiter": "growth, blessings, wealth and family happiness",
    "Venus": "comfort, romance and pleasant gains",
    "Saturn": "steady, earned progress and elimination of rivals",
    "Rahu": "bold unconventional gains",
    "Ketu": "quiet spiritual clarity",
}
HARD_TEXT = {
    "Sun": "friction with authority — stay humble, avoid ego clashes",
    "Moon": "moody days — rest more, decide less",
    "Mars": "disputes and haste — cool the temper, avoid risky moves",
    "Mercury": "miscommunication — double-check documents",
    "Jupiter": "over-optimism or expenses — verify before expanding",
    "Venus": "relationship friction or overspending — moderation",
    "Saturn": "pressure and delays — persist honestly, avoid shortcuts",
    "Rahu": "confusion and temptation — no shortcuts, stay grounded",
    "Ketu": "detachment and drift — finish what is started",
}

SATURN_DEG_PER_YEAR = 12.2   # mean motion


def gochar_report(moon_sign: int, tz_offset: float = 5.5) -> dict:
    now = datetime.now()
    jd = julian_day_utc(now, tz_offset)
    pos = compute_positions(jd)

    transits = []
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                 "Saturn", "Rahu", "Ketu"):
        lon = pos[name]["longitude"]
        sign = int(lon // 30)
        house = (sign - moon_sign) % 12 + 1
        good = house in TRANSIT_GOOD[name]
        transits.append({
            "planet": name, "sign": SIGNS[sign],
            "house_from_moon": house,
            "favourable": good,
            "effect": GOOD_TEXT[name] if good else HARD_TEXT[name],
        })

    # --- Sade Sati / dhaiya ---
    sat_lon = pos["Saturn"]["longitude"]
    sat_sign = int(sat_lon // 30)
    sat_house = (sat_sign - moon_sign) % 12 + 1
    sade = None
    if sat_house in (12, 1, 2):
        phase = {12: ("Rising (first) phase",
                      "Expenses and preparation rise; foundations are tested."),
                 1: ("Peak (second) phase",
                     "Maximum pressure on health, mind and status — also maximum growth if faced honestly."),
                 2: ("Setting (final) phase",
                     "Financial and family responsibilities peak, then lift — the lessons consolidate.")}[sat_house]
        # degrees until Saturn exits the 2nd sign from the moon sign
        end_lon = (((moon_sign + 2) % 12) + 1) * 30 % 360
        deg_left = (end_lon - sat_lon) % 360
        years_left = deg_left / SATURN_DEG_PER_YEAR
        end_est = now + timedelta(days=years_left * 365.25)
        sade = {
            "active": True, "type": "Sade Sati",
            "phase": phase[0], "meaning": phase[1],
            "ends_approx": end_est.strftime("%Y-%m"),
            "remedy": ("Saturday Shani remedies: til-oil lamp, service to "
                       "elders and workers, Hanuman Chalisa, honest hard "
                       "work. Avoid shortcuts and new debts."),
        }
    elif sat_house in (4, 8):
        sade = {
            "active": True, "type": "Shani Dhaiya (small panoti)",
            "phase": f"Saturn transiting the {sat_house}th from your rashi",
            "meaning": ("A ~2.5 year spell of extra responsibility "
                        + ("at home and within" if sat_house == 4
                           else "through sudden changes and health care")),
            "ends_approx": (now + timedelta(days=(((30 - sat_lon % 30)
                            / SATURN_DEG_PER_YEAR) * 365.25))).strftime("%Y-%m"),
            "remedy": "Same Shani remedies as Sade Sati; keep routines steady.",
        }
    else:
        sade = {"active": False, "type": "None",
                "phase": f"Saturn is in your {sat_house}th house from the Moon",
                "meaning": "No Sade Sati or dhaiya running now.",
                "remedy": None, "ends_approx": None}

    # Jupiter blessing note
    jup = next(t for t in transits if t["planet"] == "Jupiter")
    highlight = (f"Jupiter transits your {jup['house_from_moon']}th house — "
                 + ("a supportive phase: use it for growth moves."
                    if jup["favourable"] else
                    "keep expectations measured this Jupiter year."))

    return {"as_of": now.strftime("%Y-%m-%d"),
            "transits": transits, "sade_sati": sade,
            "highlight": highlight}
