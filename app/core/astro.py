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


def rise_set(date: datetime, tz: float, lat: float, lon: float) -> tuple[datetime, datetime]:
    """Local sunrise & sunset via Swiss Ephemeris (Moshier, offline)."""
    midnight = date.replace(hour=0, minute=0, second=0, microsecond=0)
    jd0 = julian_day_utc(midnight, tz)
    geopos = (lon, lat, 0.0)
    out = []
    for rsmi in (swe.CALC_RISE, swe.CALC_SET):
        res = swe.rise_trans(jd0, swe.SUN, rsmi | swe.BIT_DISC_CENTER,
                             geopos, 0.0, 0.0, swe.FLG_MOSEPH)
        jd_evt = res[1][0]
        y, m, d, h = swe.revjul(jd_evt)
        out.append(datetime(y, m, d) + timedelta(hours=h + tz))
    return out[0], out[1]


def next_crossing(fn, target_deg: float, jd0: float,
                  max_days: float = 4.0) -> float | None:
    """First JD after jd0 where fn(jd) crosses target_deg (increasing)."""
    def d(jd: float) -> float:
        return ((fn(jd) - target_deg + 180.0) % 360.0) - 180.0
    step = 2.0 / 24.0
    jd = jd0
    if d(jd) >= 0:
        jd += step  # already past — look for the next cycle
    n = int(max_days / step) + 1
    for _ in range(n):
        jd2 = jd + step
        if d(jd) < 0 <= d(jd2):
            lo, hi = jd, jd2
            for _ in range(28):
                mid = (lo + hi) / 2
                if d(mid) >= 0:
                    hi = mid
                else:
                    lo = mid
            return hi
        jd = jd2
    return None


def jd_to_local(jd: float, tz: float) -> datetime:
    y, m, d, h = swe.revjul(jd)
    return datetime(y, m, d) + timedelta(hours=h + tz)


# ---- divisional charts -------------------------------------------------
def hora_sign(lon: float) -> int:
    """D2: odd signs 1st half -> Leo, 2nd -> Cancer; even signs reversed."""
    sign, first = int(lon // 30), (lon % 30) < 15
    odd = sign % 2 == 0            # Aries(0) is the 1st (odd) sign
    return 4 if (odd == first) else 3


def saptamsa_sign(lon: float) -> int:
    """D7: odd signs count from the sign itself, even from its 7th."""
    sign = int(lon // 30)
    part = int((lon % 30) / (30.0 / 7.0))
    start = sign if sign % 2 == 0 else (sign + 6) % 12
    return (start + part) % 12


def dasamsa_sign(lon: float) -> int:
    """D10: odd signs count from the sign itself, even from its 9th."""
    sign = int(lon // 30)
    part = int((lon % 30) / 3.0)
    start = sign if sign % 2 == 0 else (sign + 8) % 12
    return (start + part) % 12


# ---- simplified planetary strength (shadbala-inspired, 0-100) ----------
_FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"], "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"], "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"], "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
}
_ENEMIES = {
    "Sun": ["Venus", "Saturn"], "Moon": [], "Mars": ["Mercury"],
    "Mercury": ["Moon"], "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"], "Saturn": ["Sun", "Moon", "Mars"],
}
_NAISARGIKA = {"Sun": 10.0, "Moon": 8.6, "Venus": 7.1, "Jupiter": 5.7,
               "Mercury": 4.3, "Mars": 2.9, "Saturn": 1.4}
_DIG_HOUSE = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1,
              "Moon": 4, "Venus": 4, "Saturn": 7}
_POS_PTS = {1: 15, 4: 15, 7: 15, 10: 15, 5: 12, 9: 12,
            2: 8, 11: 8, 3: 6, 6: 6, 8: 3, 12: 3}


def strength_score(name: str, sign: int, house: int, dignity_: str,
                   retro: bool, nav_sign: int) -> dict | None:
    if name in ("Rahu", "Ketu"):
        return None
    if dignity_ == "exalted":
        pts = 30.0
    elif dignity_ == "own sign":
        pts = 25.0
    elif dignity_ == "debilitated":
        pts = 0.0
    else:
        lord = SIGN_LORDS[sign]
        if lord in _FRIENDS.get(name, []):
            pts = 15.0
        elif lord in _ENEMIES.get(name, []):
            pts = 5.0
        else:
            pts = 10.0
    dig = _DIG_HOUSE[name]
    if house == dig:
        pts += 15
    elif abs(house - dig) in (1, 11):
        pts += 7
    pts += _POS_PTS[house]
    pts += 10 if (retro and name not in ("Sun", "Moon")) else 5
    pts += _NAISARGIKA[name]
    if sign == nav_sign:
        pts += 10   # vargottama
    pct = min(100, round(pts / 90.0 * 100))
    label = "strong" if pct >= 65 else "moderate" if pct >= 42 else "weak"
    return {"percent": pct, "label": label}


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
        retro = p["retrograde"] and name not in ("Sun", "Moon")
        dig = dignity(name, sign)
        nav = navamsa_sign(plon)
        planets.append({
            "name": name,
            "longitude": round(plon, 4),
            "sign": sign,
            "sign_name": SIGNS[sign],
            "degree_in_sign": round(plon % 30, 2),
            # Whole-sign house counted from the lagna
            "house": (sign - asc_sign) % 12 + 1,
            "nakshatra": nakshatra_of(plon),
            "retrograde": retro,
            "dignity": dig,
            "navamsa_sign": nav,
            "navamsa_sign_name": SIGNS[nav],
            "d2_sign_name": SIGNS[hora_sign(plon)],
            "d7_sign_name": SIGNS[saptamsa_sign(plon)],
            "d10_sign_name": SIGNS[dasamsa_sign(plon)],
            "vargottama": sign == nav,
            "strength": strength_score(name, sign,
                                       (sign - asc_sign) % 12 + 1,
                                       dig, retro, nav),
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
