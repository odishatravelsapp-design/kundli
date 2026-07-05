"""Odia festival calendar for a year.

Months for tithi-festivals are true PURNIMANTA lunar months (the Odia panji
convention — e.g. Kartika masa begins the day after Kumar Purnima), computed
from actual new moons + the sankranti-naming rule. Sankranti festivals use
the exact solar-entry moment.
"""
from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, timedelta

from .astro import (compute_positions, jd_to_local, julian_day_utc,
                    next_crossing, rise_set)
from .panchanga import ODIA_MASA

# (purnimanta lunar masa index, tithi_abs, name, note)
# tithi_abs: shukla n = n (15 = Purnima), krishna n = 15 + n (30 = Amavasya)
RULES = [
    (0, 3, "Akshaya Tritiya", "New beginnings; sowing festival; Chandan Yatra begins in Puri."),
    (1, 30, "Savitri Amavasya (Sabitri Brata)", "Married women fast for their husbands' long life."),
    (1, 6, "Sitalsasthi", "Marriage of Shiva and Parvati (grand in Sambalpur)."),
    (1, 15, "Snana Purnima (Deba Snana)", "Ceremonial bathing of Lord Jagannath at Puri."),
    (2, 2, "Ratha Yatra", "The Car Festival of Lord Jagannath, Puri."),
    (2, 10, "Bahuda Yatra", "Return journey of the chariots to Srimandira."),
    (2, 15, "Guru Purnima", "Honouring gurus and teachers."),
    (3, 15, "Gamha Purnima / Raksha Bandhan", "Birthday of Lord Balabhadra; rakhi tying."),
    (4, 23, "Janmashtami", "Birth of Lord Krishna."),
    (4, 4, "Ganesh Puja", "Ganesh Chaturthi."),
    (4, 5, "Nuakhai", "Western Odisha's new-rice harvest festival."),
    (5, 30, "Mahalaya", "Ancestor offerings; Devi Paksha begins."),
    (5, 8, "Durga Ashtami (Maha Ashtami)", "Peak of Durga Puja."),
    (5, 10, "Vijayadashami (Dussehra)", "Victory of good over evil."),
    (5, 15, "Kumar Purnima", "Odisha's festival of unmarried girls; moon worship."),
    (6, 30, "Diwali / Kali Puja", "Festival of lights; Badabadua Daka in Odisha."),
    (6, 15, "Kartika Purnima (Boita Bandana)", "Odisha's maritime festival — floating of miniature boats."),
    (7, 23, "Prathamastami", "Odia festival for the first-born child's wellbeing."),
    (8, 15, "Pausa Purnima", "Winter full moon."),
    (9, 5, "Basanta Panchami (Saraswati Puja)", "Worship of Saraswati; start of spring."),
    (9, 7, "Magha Saptami (Chandrabhaga Mela)", "Sun worship at Konark/Chandrabhaga."),
    (10, 15, "Dola Purnima / Holi", "Swing festival of Radha-Krishna; colours."),
    (10, 29, "Maha Shivaratri (Jagara)", "Great night of Shiva; jagara vigil."),
    (11, 9, "Rama Navami", "Birth of Lord Rama."),
]

SANKRANTI_FEST = {
    0: ("Pana Sankranti (Maha Bishuba)", "Odia New Year — sweet pana drink offered."),
    2: ("Raja Sankranti", "2nd day of Raja Parba — festival of womanhood and Mother Earth."),
    8: ("Dhanu Sankranti", "Dhanu masa begins; Dhanu Yatra season (Bargarh)."),
    9: ("Makara Sankranti", "Harvest festival; Makara Chaula offering."),
}


def _elong(jd: float) -> float:
    p = compute_positions(jd)
    return (p["Moon"]["longitude"] - p["Sun"]["longitude"]) % 360.0


def _sun_lon(jd: float) -> float:
    return compute_positions(jd)["Sun"]["longitude"]


def _new_moons(jd_from: float, jd_to: float) -> list[float]:
    out, jd = [], jd_from
    while jd < jd_to:
        nm = next_crossing(_elong, 360.0, jd, max_days=32)
        if nm is None:
            break
        out.append(nm)
        jd = nm + 25.0
    return out


def _sankrantis(jd_from: float, jd_to: float) -> list[tuple[float, int]]:
    """[(jd, sign_entered), ...] over the window."""
    out, jd = [], jd_from
    while jd < jd_to:
        cur = int(_sun_lon(jd) // 30)
        target = ((cur + 1) % 12) * 30
        cross = next_crossing(_sun_lon, float(target), jd, max_days=35)
        if cross is None or cross > jd_to:
            break
        out.append((cross, (cur + 1) % 12))
        jd = cross + 5.0
    return out


def year_festivals(year: int, tz: float, lat: float, lon: float,
                   include_ekadashi: bool = False) -> list[dict]:
    jd_from = julian_day_utc(datetime(year - 1, 12, 1), tz)
    jd_to = julian_day_utc(datetime(year + 1, 2, 1), tz)
    nms = _new_moons(jd_from, jd_to)
    sks = _sankrantis(jd_from, jd_to)

    # amanta month name for each new-moon interval [nms[i], nms[i+1])
    amanta: list[int | None] = []
    for i in range(len(nms) - 1):
        inside = [s for t, s in sks if nms[i] <= t < nms[i + 1]]
        # month containing the Sun's entry into sign S is named S+11 (Chaitra
        # holds Mesha sankranti, Pausa holds Makara, ...)
        amanta.append((inside[0] + 11) % 12 if inside else None)  # None=adhika

    out: list[dict] = []

    # sankranti festivals: exact crossing date
    for t, sign in sks:
        local = jd_to_local(t, tz)
        if local.year != year or sign not in SANKRANTI_FEST:
            continue
        name, note = SANKRANTI_FEST[sign]
        out.append({"date": local.strftime("%Y-%m-%d"), "name": name,
                    "note": note, "type": "sankranti"})
        if sign == 2:
            out.append({"date": (local - timedelta(days=1)).strftime("%Y-%m-%d"),
                        "name": "Pahili Raja", "note": "First day of Raja Parba.",
                        "type": "sankranti"})
            out.append({"date": (local + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "name": "Basi Raja (Bhui Daana)",
                        "note": "Third day of Raja Parba.", "type": "sankranti"})

    # tithi festivals at sunrise, purnimanta lunar masa
    seen_yesterday: set[str] = set()
    day0 = datetime(year, 1, 1)
    ndays = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
    for i in range(ndays):
        date = day0 + timedelta(days=i)
        sunrise, _ = rise_set(date, tz, lat, lon)
        jd = julian_day_utc(sunrise, tz)
        pos = compute_positions(jd)
        sun, moon = pos["Sun"]["longitude"], pos["Moon"]["longitude"]
        tithi_abs = int(((moon - sun) % 360.0) // 12) + 1
        weekday = int(jd + 1.5) % 7

        k = bisect_right(nms, jd) - 1
        if k < 0 or k >= len(amanta) or amanta[k] is None:
            seen_yesterday = set()
            continue                       # adhika masa — festivals skip
        masa = amanta[k]
        if tithi_abs > 15:                 # Krishna paksha: purnimanta = next
            masa = (masa + 1) % 12

        matched_today: set[str] = set()
        for m, t, name, note in RULES:
            if m == masa and t == tithi_abs:
                if name not in seen_yesterday:
                    out.append({"date": date.strftime("%Y-%m-%d"),
                                "name": name, "note": note, "type": "parba"})
                matched_today.add(name)

        if masa == 7 and weekday == 4:
            out.append({"date": date.strftime("%Y-%m-%d"),
                        "name": "Manabasa Gurubara",
                        "note": "Weekly Lakshmi puja of Margasira masa.",
                        "type": "weekly"})

        if include_ekadashi and tithi_abs in (11, 26):
            nm_name = ("Shukla" if tithi_abs == 11 else "Krishna") + " Ekadashi"
            if nm_name not in seen_yesterday:
                out.append({"date": date.strftime("%Y-%m-%d"),
                            "name": f"{nm_name} ({ODIA_MASA[masa]})",
                            "note": "Fasting and Vishnu worship.",
                            "type": "ekadashi"})
            matched_today.add(nm_name)

        seen_yesterday = matched_today

    out.sort(key=lambda f: f["date"])
    return out
