"""Daily muhurta for activities: trading/stocks, new business, travel,
griha pravesh, general work.

For a given day & place it computes (all from the ephemeris, free/offline):
- sunrise/sunset, and from them the inauspicious kala windows
  (Rahu Kala, Gulika Kala, Yamaganda) and the Abhijit muhurta
- the 12 daytime planetary horas, scored per activity
  (e.g. Mercury/Jupiter/Moon horas favour trading and finance)
- a day-quality score from nakshatra/tithi/vaara/yoga rules per activity
- optional personalisation: tara bala & chandra bala from a birth chart

It can also scan the next N days and rank them for the activity.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import swisseph as swe

from .astro import (NAK_SPAN, NAKSHATRAS, compute_positions, julian_day_utc,
                    rise_set)
from .panchanga import VAARA, YOGA_NAMES, karana_name, TITHI_NAMES

# nakshatra index sets per activity (classical muhurta elections)
ACTIVITIES = {
    "trading": {
        "label": "Trading / stocks / investment",
        "nak": {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
        "good_vaara": {1, 3, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Mercury", "Jupiter", "Moon", "Venus"},
        "bad_horas": {"Saturn", "Mars"},
        "tip": ("Pushya, Hasta, Chitra, Swati, Shravana and Dhanishta days "
                "favour money matters; buy in Mercury/Jupiter horas, avoid "
                "fresh positions in Rahu Kala and Saturn/Mars horas."),
    },
    "business": {
        "label": "Starting a business / opening shop",
        "nak": {0, 3, 4, 6, 7, 9, 11, 12, 13, 14, 16, 20, 21, 22, 25, 26},
        "good_vaara": {3, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Mercury", "Jupiter", "Venus", "Sun"},
        "bad_horas": {"Saturn", "Mars"},
        "tip": "Thursday and Friday openings under Pushya or Hasta are classic.",
    },
    "travel": {
        "label": "Travel / journey start",
        "nak": {0, 4, 6, 7, 12, 16, 18, 21, 22, 26},
        "good_vaara": {1, 3, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Moon", "Mercury", "Jupiter", "Venus"},
        "bad_horas": {"Saturn", "Mars"},
        "tip": "Avoid starting journeys in Rahu Kala; Mula and Shravana favour travel.",
    },
    "grihapravesh": {
        "label": "Griha Pravesh / new home",
        "nak": {3, 4, 11, 12, 16, 20, 21, 22, 25, 26},
        "good_vaara": {1, 3, 4, 5}, "bad_vaara": {0, 2, 6},
        "good_horas": {"Jupiter", "Venus", "Moon"},
        "bad_horas": {"Saturn", "Mars", "Sun"},
        "tip": "Uttara nakshatras, Rohini and Revati are prescribed for entering a new home.",
    },
    "satyanarayan": {
        "label": "Satyanarayan Puja (baby blessing / gratitude vrata)",
        # Rohini, Punarvasu, Pushya, U.Phalguni, Hasta, Swati, Anuradha,
        # U.Ashadha, Shravana, U.Bhadrapada, Revati
        "nak": {3, 6, 7, 11, 12, 14, 16, 20, 21, 25, 26},
        "good_vaara": {1, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Jupiter", "Moon", "Venus"},
        "bad_horas": {"Saturn", "Mars", "Rahu"},
        "bonus_tithi": {15, 11, 26, 5},   # Purnima, both Ekadashis, Shukla Panchami
        "tip": ("Satyanarayan vrata is most auspicious on Purnima (full moon) "
                "evening, and also on Ekadashi and Sankranti days. Perform "
                "after sunset or in Jupiter/Moon hora; the whole family "
                "should take prasad. For a newborn, pair it with the "
                "Namakarana on a day whose star is friendly to the child's "
                "janma nakshatra (fill the birth details for the personal check)."),
    },
    "vehicle": {
        "label": "Vehicle purchase / first drive",
        # Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Hasta, Chitra,
        # Swati, Anuradha, Shravana, Dhanishta, Shatabhisha, Revati
        "nak": {0, 3, 4, 6, 7, 12, 13, 14, 16, 21, 22, 23, 26},
        "good_vaara": {1, 3, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Venus", "Mercury", "Jupiter", "Moon"},
        "bad_horas": {"Saturn", "Mars"},
        "tip": ("Venus rules vehicles — buy or take first delivery in a "
                "Venus hora on a Venus-friendly day (Friday best, then "
                "Wednesday/Thursday). Avoid Rahu Kala for the first drive, "
                "do a simple vahana puja, and offer sweets before use. "
                "Amavasya and rikta tithis are avoided for delivery."),
    },
    "general": {
        "label": "General auspicious work",
        "nak": {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
        "good_vaara": {1, 3, 4, 5}, "bad_vaara": {2, 6},
        "good_horas": {"Jupiter", "Venus", "Mercury", "Moon"},
        "bad_horas": {"Saturn", "Mars"},
        "tip": "Abhijit muhurta (around local noon) rescues most works when in doubt.",
    },
}

BAD_TITHI = {4, 9, 14, 19, 24, 29, 30}
BAD_YOGA = {1, 6, 9, 10, 13, 15, 17, 19, 27}

# segment (1..8 of daylight) per weekday, 0=Sunday
RAHU_SEG = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
GULIKA_SEG = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
YAMA_SEG = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}

HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
DAY_LORD = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter",
            5: "Venus", 6: "Saturn"}


_rise_set = rise_set


def _fmt(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def day_windows(date: datetime, tz: float, lat: float, lon: float) -> dict:
    sunrise, sunset = _rise_set(date, tz, lat, lon)
    daylen = sunset - sunrise
    seg8 = daylen / 8
    weekday = int(julian_day_utc(date.replace(hour=12), tz) + 1.5) % 7

    def seg_window(seg: int) -> dict:
        s = sunrise + seg8 * (seg - 1)
        return {"from": _fmt(s), "to": _fmt(s + seg8)}

    # Abhijit = the 8th of 15 muhurtas of daylight
    m15 = daylen / 15
    abhi_s = sunrise + m15 * 7

    horas = []
    hlen = daylen / 12
    start_idx = HORA_ORDER.index(DAY_LORD[weekday])
    for i in range(12):
        lord = HORA_ORDER[(start_idx + i) % 7]
        s = sunrise + hlen * i
        horas.append({"lord": lord, "from": _fmt(s), "to": _fmt(s + hlen)})

    return {
        "sunrise": _fmt(sunrise), "sunset": _fmt(sunset),
        "weekday": VAARA[weekday],
        "rahu_kala": seg_window(RAHU_SEG[weekday]),
        "gulika_kala": seg_window(GULIKA_SEG[weekday]),
        "yamaganda": seg_window(YAMA_SEG[weekday]),
        "abhijit": {"from": _fmt(abhi_s), "to": _fmt(abhi_s + m15)},
        "horas": horas,
    }


def score_day(date: datetime, tz: float, activity: str,
              birth_nak: int | None = None,
              birth_sign: int | None = None) -> dict:
    rules = ACTIVITIES.get(activity, ACTIVITIES["general"])
    jd = julian_day_utc(date.replace(hour=12), tz)
    pos = compute_positions(jd)
    sun, moon = pos["Sun"]["longitude"], pos["Moon"]["longitude"]

    day_nak = int(moon // NAK_SPAN) % 27
    elong = (moon - sun) % 360.0
    tithi_abs = int(elong // 12) + 1
    yoga_idx = int(((sun + moon) % 360.0) // NAK_SPAN) + 1
    weekday = int(jd + 1.5) % 7
    day_moon_sign = int(moon // 30)

    score, notes = 0.0, []
    if day_nak in rules["nak"]:
        score += 3
    else:
        notes.append(f"{NAKSHATRAS[day_nak]} is not an elected star for this work")
    if tithi_abs in BAD_TITHI:
        score -= 2; notes.append("rikta/amavasya tithi")
    elif tithi_abs in rules.get("bonus_tithi", set()):
        score += 2.5; notes.append("specially auspicious tithi for this vrata")
    else:
        score += 1
    if yoga_idx in BAD_YOGA:
        score -= 1.5; notes.append(f"{YOGA_NAMES[yoga_idx-1]} yoga")
    else:
        score += 0.5
    if weekday in rules["good_vaara"]:
        score += 1.5
    elif weekday in rules["bad_vaara"]:
        score -= 1; notes.append(f"{VAARA[weekday]} is weak for this activity")

    personal = None
    if birth_nak is not None and birth_sign is not None:
        tara = ((day_nak - birth_nak) % 27) % 9 + 1
        chandra = (day_moon_sign - birth_sign) % 12 + 1
        tara_ok = tara not in (3, 5, 7)
        chandra_ok = chandra not in (4, 8, 12)
        score += (1 if tara_ok else -2) + (1 if chandra_ok else -2)
        personal = {
            "tara": tara, "tara_ok": tara_ok,
            "chandra_position": chandra, "chandra_ok": chandra_ok,
            "note": ("Personally favourable day" if tara_ok and chandra_ok
                     else "Personally unfavourable — postpone big decisions"),
        }

    t = (tithi_abs - 1) % 15
    tithi_name = ("Purnima" if tithi_abs == 15 else
                  "Amavasya" if tithi_abs == 30 else TITHI_NAMES[t])
    return {
        "date": date.strftime("%Y-%m-%d"),
        "score": round(score, 2),
        "nakshatra": NAKSHATRAS[day_nak],
        "tithi": ("Shukla " if tithi_abs <= 15 else "Krishna ") + tithi_name,
        "vaara": VAARA[weekday],
        "yoga": YOGA_NAMES[yoga_idx - 1],
        "karana": karana_name(int(elong // 6)),
        "cautions": notes,
        "personal": personal,
    }


def activity_muhurta(date: datetime, tz: float, lat: float, lon: float,
                     activity: str, scan_days: int = 0,
                     birth_nak: int | None = None,
                     birth_sign: int | None = None) -> dict:
    rules = ACTIVITIES.get(activity, ACTIVITIES["general"])
    today = score_day(date, tz, activity, birth_nak, birth_sign)
    windows = day_windows(date, tz, lat, lon)
    for h in windows["horas"]:
        h["quality"] = ("good" if h["lord"] in rules["good_horas"]
                        else "avoid" if h["lord"] in rules["bad_horas"]
                        else "neutral")

    ranked = []
    if scan_days > 1:
        for i in range(scan_days):
            d = date + timedelta(days=i)
            ranked.append(score_day(d, tz, activity, birth_nak, birth_sign))
        ranked.sort(key=lambda r: (-r["score"], r["date"]))
        ranked = ranked[:10]

    return {"activity": rules["label"], "tip": rules["tip"],
            "day": today, "windows": windows, "best_days": ranked}
