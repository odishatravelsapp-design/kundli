"""Varshaphal — annual solar-return chart (Tajika-inspired, simplified).

The solar return is the exact moment each year when the Sun comes back to
its natal sidereal longitude. The chart cast for that moment (at the birth
place, or current residence) colours the year ahead.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .astro import (SIGNS, compute_chart, compute_positions, jd_to_local,
                    julian_day_utc, next_crossing)

DAY_LORD = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter",
            5: "Venus", 6: "Saturn"}

YEAR_LORD_THEME = {
    "Sun": "a year of visibility, authority and self-assertion — lead, but stay humble",
    "Moon": "a year of home, feelings and public connection — nurture relationships",
    "Mars": "an action year — property, competition and fitness; guard the temper",
    "Mercury": "a learning and business year — study, trade, write, network",
    "Jupiter": "a growth year — wealth, family, wisdom and blessings expand",
    "Venus": "a comfort year — love, marriage, vehicles and the arts flourish",
    "Saturn": "a karma year — discipline and honest work pay; shortcuts punish",
}


def _sun_lon(jd: float) -> float:
    return compute_positions(jd)["Sun"]["longitude"]


def varshaphal(natal_sun_lon: float, birth_dt: datetime, year: int,
               tz: float, lat: float, lon: float) -> dict:
    approx = birth_dt.replace(year=year) - timedelta(days=4)
    jd0 = julian_day_utc(approx, tz)
    jd_sr = next_crossing(_sun_lon, natal_sun_lon, jd0, max_days=10)
    if jd_sr is None:
        raise ValueError("solar return not found")
    moment = jd_to_local(jd_sr, tz)

    chart = compute_chart(moment, tz, lat, lon)
    weekday = int(jd_sr + tz / 24.0 + 1.5) % 7
    year_lord = DAY_LORD[weekday]

    kendra = [p["name"] for p in chart["planets"] if p["house"] in (1, 4, 7, 10)]
    scored = [p for p in chart["planets"] if p.get("strength")]
    strongest = max(scored, key=lambda p: p["strength"]["percent"])

    notes = [
        f"The solar return falls on {moment.strftime('%Y-%m-%d at %H:%M')} "
        f"local time; the varsha lagna is {chart['ascendant']['sign_name']}.",
        f"Year lord (lord of the weekday): {year_lord} — "
        f"{YEAR_LORD_THEME[year_lord]}.",
        f"Strongest planet of the year: {strongest['name']} "
        f"({strongest['strength']['percent']}% strength in "
        f"{strongest['sign_name']}, house {strongest['house']}) — its "
        f"significations dominate the year.",
    ]
    if kendra:
        notes.append("Planets in kendras of the varsha chart ("
                     + ", ".join(kendra) + ") act strongly all year.")
    manglik_axis = next((p for p in chart["planets"]
                         if p["name"] == "Saturn" and p["house"] in (1, 8)), None)
    if manglik_axis:
        notes.append("Saturn on the 1st/8th axis of the year chart asks for "
                     "patience with health and finances this year.")

    return {
        "year": year,
        "solar_return": moment.strftime("%Y-%m-%d %H:%M"),
        "varsha_lagna": chart["ascendant"]["sign_name"],
        "year_lord": year_lord,
        "chart": chart,
        "notes": notes,
    }
