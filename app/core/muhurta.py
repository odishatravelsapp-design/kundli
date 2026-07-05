"""Vivaha (marriage) muhurta finder.

Scans a date window and scores each day against classical muhurta rules,
personalised to BOTH charts (tara bala and chandra bala are checked from the
bride's and groom's janma nakshatra/rashi). For the best dates it computes
real ascendant windows so an auspicious wedding lagna can be chosen.

Rules implemented (standard Parashari/muhurta practice as followed in
Odisha; simplified where traditions differ):
- Vivaha nakshatras: Rohini, Mrigashira, Magha, U.Phalguni, Hasta, Swati,
  Anuradha, Mula, U.Ashadha, U.Bhadrapada, Revati
- Avoid rikta tithis (4/9/14), pratipada, amavasya
- Good vaaras: Mon/Wed/Thu/Fri (Sun neutral); avoid Tue/Sat
- Avoid 9 inauspicious yogas (Vishkambha, Atiganda, Shula, Ganda,
  Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti)
- Avoid Vishti (Bhadra) karana
- Tara bala: day star must not be vipat/pratyak/naidhana (3/5/7) from
  either janma nakshatra
- Chandra bala: day Moon must not be 8th (nor ideally 6th/12th) from
  either janma rashi
- Skip Kharamasa (Sun in Dhanu or Mina) and days when Jupiter or Venus
  is combust (guru/shukra asta)
- Wedding lagna: prefer fixed (sthira) signs, then dual; never the 8th
  rashi from either partner's janma rashi; avoid the 8th lagna from the
  day's Moon too.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .astro import (NAK_SPAN, SIGNS, compute_ascendant, compute_positions,
                    julian_day_utc, nakshatra_of)
from .panchanga import (KARANA_MOVABLE, TITHI_NAMES, VAARA, YOGA_NAMES,
                        karana_name)

GOOD_NAK = {3, 4, 9, 11, 12, 14, 16, 18, 20, 25, 26}
BAD_TITHI = {1, 4, 9, 14, 16, 19, 24, 29, 30}          # 1-based absolute
BAD_YOGA = {1, 6, 9, 10, 13, 15, 17, 19, 27}           # 1-based
GOOD_VAARA = {1, 3, 4, 5}                               # Mon Wed Thu Fri
BAD_VAARA = {2, 6}                                      # Tue Sat
KHARA_SUN_SIGNS = {8, 11}                               # Dhanu, Mina

FIXED_SIGNS = {1, 4, 7, 10}      # Taurus Leo Scorpio Aquarius
DUAL_SIGNS = {2, 5, 8, 11}       # Gemini Virgo Sagittarius Pisces


def _ang(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _tara_bad(janma_nak: int, day_nak: int) -> bool:
    return ((day_nak - janma_nak) % 27) % 9 + 1 in (3, 5, 7)


def evaluate_day(dt: datetime, tz: float, boy_nak: int, girl_nak: int,
                 boy_sign: int, girl_sign: int) -> dict | None:
    """Score one candidate day (evaluated at the given local time)."""
    jd = julian_day_utc(dt, tz)
    pos = compute_positions(jd)
    sun, moon = pos["Sun"]["longitude"], pos["Moon"]["longitude"]

    sun_sign = int(sun // 30)
    if sun_sign in KHARA_SUN_SIGNS:
        return None                                    # Kharamasa: no vivaha

    day_nak = int(moon // NAK_SPAN) % 27
    if day_nak not in GOOD_NAK:
        return None                                    # nakshatra is mandatory

    elong = (moon - sun) % 360.0
    tithi_abs = int(elong // 12) + 1
    if tithi_abs in BAD_TITHI:
        return None

    yoga_idx = int(((sun + moon) % 360.0) // NAK_SPAN) + 1
    karana_idx = int(elong // 6)
    kar = karana_name(karana_idx)
    weekday = int(jd + 1.5) % 7
    day_moon_sign = int(moon // 30)

    if _tara_bad(boy_nak, day_nak) or _tara_bad(girl_nak, day_nak):
        return None
    if (day_moon_sign - boy_sign) % 12 + 1 == 8 or \
       (day_moon_sign - girl_sign) % 12 + 1 == 8:
        return None                                    # 8th chandra — reject

    score, notes = 3.0, []                             # nakshatra passed = 3
    if yoga_idx in BAD_YOGA:
        score -= 2.0; notes.append(f"inauspicious yoga ({YOGA_NAMES[yoga_idx-1]})")
    else:
        score += 1.0
    if kar == "Vishti":
        score -= 2.0; notes.append("Vishti (Bhadra) karana")
    else:
        score += 0.5
    if weekday in GOOD_VAARA:
        score += 1.0
    elif weekday in BAD_VAARA:
        score -= 1.0; notes.append(f"{VAARA[weekday]} is avoided for vivaha")
    else:
        score += 0.25
    for m_sign, who in ((boy_sign, "groom"), (girl_sign, "bride")):
        rel = (day_moon_sign - m_sign) % 12 + 1
        if rel in (6, 12):
            score -= 0.5; notes.append(f"Moon {rel}th from {who}'s rashi")
        else:
            score += 0.25
    if _ang(pos["Venus"]["longitude"], sun) < 10.0:
        score -= 1.5; notes.append("Shukra asta (Venus combust)")
    if _ang(pos["Jupiter"]["longitude"], sun) < 11.0:
        score -= 1.5; notes.append("Guru asta (Jupiter combust)")

    t = (tithi_abs - 1) % 15
    tithi_name = ("Purnima" if tithi_abs == 15 else
                  "Amavasya" if tithi_abs == 30 else TITHI_NAMES[t])
    from .astro import NAKSHATRAS
    return {
        "score": round(score, 2),
        "nakshatra": NAKSHATRAS[day_nak],
        "tithi": ("Shukla " if tithi_abs <= 15 else "Krishna ") + tithi_name,
        "vaara": VAARA[weekday],
        "yoga": YOGA_NAMES[yoga_idx - 1],
        "karana": kar,
        "day_moon_sign": day_moon_sign,
        "cautions": notes,
    }


def lagna_windows(date: datetime, tz: float, lat: float, lon: float,
                  boy_sign: int, girl_sign: int, day_moon_sign: int,
                  start_h: int = 6, end_h: int = 22) -> list[dict]:
    """Rising-sign windows for the day, keeping only auspicious lagnas."""
    banned = {(boy_sign + 7) % 12, (girl_sign + 7) % 12,
              (day_moon_sign + 7) % 12}
    windows, cur_sign, cur_start = [], None, None
    t = date.replace(hour=start_h, minute=0, second=0)
    end = date.replace(hour=end_h, minute=0, second=0)
    step = timedelta(minutes=5)
    while t <= end:
        sign = int(compute_ascendant(julian_day_utc(t, tz), lat, lon) // 30)
        if sign != cur_sign:
            if cur_sign is not None:
                windows.append((cur_sign, cur_start, t))
            cur_sign, cur_start = sign, t
        t += step
    windows.append((cur_sign, cur_start, end))

    out = []
    for sign, s, e in windows:
        if sign in banned:
            continue
        if sign in FIXED_SIGNS:
            quality, rank = "excellent (sthira lagna)", 0
        elif sign in DUAL_SIGNS:
            quality, rank = "good (dwiswabhava lagna)", 1
        else:
            continue                       # movable lagnas skipped for vivaha
        out.append({
            "lagna": SIGNS[sign],
            "from": s.strftime("%H:%M"), "to": e.strftime("%H:%M"),
            "quality": quality, "_rank": rank,
        })
    out.sort(key=lambda w: (w["_rank"], w["from"]))
    for w in out:
        w.pop("_rank")
    return out


def find_marriage_dates(boy_nak: int, girl_nak: int, boy_sign: int,
                        girl_sign: int, start: datetime, days: int,
                        tz: float, lat: float, lon: float,
                        eval_hour: int = 19, top: int = 10) -> list[dict]:
    results = []
    for i in range(days):
        day = (start + timedelta(days=i)).replace(hour=eval_hour, minute=0,
                                                  second=0, microsecond=0)
        r = evaluate_day(day, tz, boy_nak, girl_nak, boy_sign, girl_sign)
        if r is not None:
            r["date"] = day.strftime("%Y-%m-%d")
            results.append(r)
    results.sort(key=lambda r: (-r["score"], r["date"]))
    best = results[:top]
    for r in best:
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        r["lagna_windows"] = lagna_windows(
            d, tz, lat, lon, boy_sign, girl_sign, r["day_moon_sign"])
        r.pop("day_moon_sign", None)
    best.sort(key=lambda r: r["date"])
    return best
