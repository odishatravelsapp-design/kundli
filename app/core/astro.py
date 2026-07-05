"""Sidereal (Vedic) chart calculations using Swiss Ephemeris.

Uses the built-in Moshier semi-analytical ephemeris (FLG_MOSEPH) so no
ephemeris data files are required — fully offline and free, accurate to a
fraction of an arc-second for astrological purposes. Ayanamsa: Lahiri.
Houses: whole-sign (the classical Vedic system).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import swisseph as swe

swe.set_sid_mode(swe.SIDM_LAHIRI)

CALC_FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

PLANET_IDS = [
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN), ("Rahu", swe.MEAN_NODE),
]

SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

EXALTATION = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
              "Jupiter": 3, "Venus": 11, "Saturn": 6}
OWN_SIGNS = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
             "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
             "Rahu": [], "Ketu": []}

NAK_SPAN = 360.0 / 27.0


def julian_day_utc(dt_local: datetime, tz_offset_hours: float) -> float:
    """Convert local civil time to Julian Day (UT)."""
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def nakshatra_of(lon: float) -> dict:
    idx = int(lon // NAK_SPAN) % 27
    pada = int((lon % NAK_SPAN) // (NAK_SPAN / 4)) + 1
    return {"index": idx, "name": NAKSHATRAS[idx], "pada": pada}


def navamsa_sign(lon: float) -> int:
    return int(lon // (30.0 / 9.0)) % 12


def dignity(planet: str, sign: int) -> str:
    if planet in EXALTATION:
        if sign == EXALTATION[planet]:
            return "exalted"
        if sign == (EXALTATION[planet] + 6) % 12:
            return "debilitated"
    if sign in OWN_SIGNS.get(planet, []):
        return "own sign"
    return "neutral"


def compute_positions(jd_ut: float) -> dict:
    """Sidereal longitudes for the 9 grahas."""
    planets = {}
    for name, pid in PLANET_IDS:
        res = swe.calc_ut(jd_ut, pid, CALC_FLAGS)
        lon, speed = res[0][0] % 360.0, res[0][3]
        planets[name] = {"longitude": lon, "retrograde": speed < 0}
    # Ketu is always opposite Rahu
    planets["Ketu"] = {
        "longitude": (planets["Rahu"]["longitude"] + 180.0) % 360.0,
        "retrograde": True,
    }
    planets["Rahu"]["retrograde"] = True
    return planets


def compute_ascendant(jd_ut: float, lat: float, lon: float) -> float:
    _, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


def compute_chart(dt_local: datetime, tz_offset: float, lat: float, lon: float) -> dict:
    jd = julian_day_utc(dt_local, tz_offset)
    asc = compute_ascendant(jd, lat, lon)
    asc_sign = int(asc // 30)

    positions = compute_positions(jd)
    planets = []
    for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                 "Saturn", "Rahu", "Ketu"]:
        p = positions[name]
        plon = p["longitude"]
        sign = int(plon // 30)
        planets.append({
            "name": name,
            "longitude": round(plon, 4),
            "sign": sign,
            "sign_name": SIGNS[sign],
            "degree_in_sign": round(plon % 30, 2),
            # Whole-sign house counted from the lagna
            "house": (sign - asc_sign) % 12 + 1,
            "nakshatra": nakshatra_of(plon),
            "retrograde": p["retrograde"] and name not in ("Sun", "Moon"),
            "dignity": dignity(name, sign),
            "navamsa_sign": navamsa_sign(plon),
            "navamsa_sign_name": SIGNS[navamsa_sign(plon)],
        })

    moon = next(p for p in planets if p["name"] == "Moon")
    return {
        "julian_day_ut": jd,
        "ayanamsa": round(swe.get_ayanamsa_ut(jd), 4),
        "ascendant": {
            "longitude": round(asc, 4),
            "sign": asc_sign,
            "sign_name": SIGNS[asc_sign],
            "degree_in_sign": round(asc % 30, 2),
            "nakshatra": nakshatra_of(asc),
            "navamsa_sign": navamsa_sign(asc),
        },
        "planets": planets,
        "moon_sign": moon["sign"],
        "moon_sign_name": SIGNS[moon["sign"]],
        "moon_nakshatra": moon["nakshatra"],
    }
