"""Panchanga (tithi, nakshatra, yoga, karana, vaara) with Odisha specifics.

Odisha follows a solar calendar for months (masa determined by the Sun's
sidereal sign — Mesha Sankranti / Pana Sankranti begins the Odia new year)
alongside the lunar tithi system. Both are reported here.
"""
from __future__ import annotations

from datetime import datetime

from .astro import (CALC_FLAGS, NAK_SPAN, SIGNS, compute_positions,
                    julian_day_utc, nakshatra_of)

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi",
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra",
    "Vaidhriti",
]

KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija",
                  "Vishti"]
KARANA_FIXED = ["Shakuni", "Chatushpada", "Naga"]

VAARA = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday"]
VAARA_ODIA = ["Rabibara", "Somabara", "Mangalabara", "Budhabara",
              "Gurubara", "Sukrabara", "Sanibara"]

# Odia solar months: the masa is fixed by the Sun's sidereal rashi.
# Mesha -> Baisakha (begins with Pana Sankranti, the Odia new year).
ODIA_MASA = [
    "Baisakha", "Jyestha", "Asadha", "Srabana", "Bhadraba", "Aswina",
    "Kartika", "Margasira", "Pausa", "Magha", "Phalguna", "Chaitra",
]

SANKRANTI_NOTES = {
    0: "Pana Sankranti (Maha Bishuba Sankranti) — Odia New Year falls when the Sun enters Mesha.",
    7: "Sun in Vrischika — month of Margasira approaches; Manabasa Gurubara Lakshmi puja season.",
    8: "Dhanu Sankranti — Dhanu Yatra season (Bargarh hosts the world's largest open-air theatre).",
    9: "Makara Sankranti — major harvest festival across Odisha.",
    3: "Karkata Sankranti; Srabana purnima brings Gamha Purnima (Baladeva's birthday).",
}


def karana_name(k: int) -> str:
    """k is the half-tithi index 0..59."""
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return KARANA_FIXED[k - 57]
    return KARANA_MOVABLE[(k - 1) % 7]


def compute_panchanga(dt_local: datetime, tz_offset: float) -> dict:
    jd = julian_day_utc(dt_local, tz_offset)
    pos = compute_positions(jd)
    sun = pos["Sun"]["longitude"]
    moon = pos["Moon"]["longitude"]

    elong = (moon - sun) % 360.0
    tithi_idx = int(elong // 12)          # 0..29
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    t = tithi_idx % 15
    if tithi_idx == 14:
        tithi = "Purnima"
    elif tithi_idx == 29:
        tithi = "Amavasya"
    else:
        tithi = TITHI_NAMES[t]

    yoga_idx = int(((sun + moon) % 360.0) // NAK_SPAN)
    karana_idx = int(elong // 6)          # 0..59
    weekday = int(jd + 1.5) % 7           # 0 = Sunday

    sun_sign = int(sun // 30)
    masa_idx = sun_sign  # Mesha -> Baisakha

    return {
        "tithi": {"index": tithi_idx + 1, "name": tithi, "paksha": paksha},
        "nakshatra": nakshatra_of(moon),
        "yoga": {"index": yoga_idx + 1, "name": YOGA_NAMES[yoga_idx]},
        "karana": {"index": karana_idx + 1, "name": karana_name(karana_idx)},
        "vaara": {"index": weekday, "name": VAARA[weekday],
                  "odia": VAARA_ODIA[weekday]},
        "odia_masa": {"index": masa_idx + 1, "name": ODIA_MASA[masa_idx],
                      "sun_rashi": SIGNS[sun_sign]},
        "sankranti_note": SANKRANTI_NOTES.get(sun_sign),
        "sun_longitude": round(sun, 4),
        "moon_longitude": round(moon, 4),
    }
