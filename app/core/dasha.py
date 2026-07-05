"""Vimshottari dasha calculation from the Moon's nakshatra."""
from __future__ import annotations

from datetime import datetime, timedelta

from .astro import NAK_SPAN

DASHA_SEQUENCE = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
]
YEAR_DAYS = 365.25


def vimshottari(moon_longitude: float, birth_dt: datetime,
                antardashas_for_current: bool = True) -> dict:
    nak_idx = int(moon_longitude // NAK_SPAN) % 27
    frac_elapsed = (moon_longitude % NAK_SPAN) / NAK_SPAN
    start_lord_idx = nak_idx % 9
    start_lord, start_years = DASHA_SEQUENCE[start_lord_idx]

    balance_years = start_years * (1.0 - frac_elapsed)
    periods = []
    cursor = birth_dt
    now = datetime.now()

    # First (partial) mahadasha, then full cycle up to 120 years of life.
    idx = start_lord_idx
    years = balance_years
    total = 0.0
    while total < 120.0:
        lord, full_years = DASHA_SEQUENCE[idx % 9]
        span = years if len(periods) == 0 else float(full_years)
        end = cursor + timedelta(days=span * YEAR_DAYS)
        period = {
            "lord": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": round(span, 2),
            "current": cursor <= now < end,
        }
        period["antardashas"] = _antardashas(lord, cursor, span, now)
        periods.append(period)
        total += span
        cursor = end
        idx += 1
        years = 0.0

    current = next((p for p in periods if p["current"]), None)
    return {
        "balance_at_birth": {"lord": start_lord,
                             "years": round(balance_years, 2)},
        "mahadashas": periods,
        "current_mahadasha": current["lord"] if current else None,
        "current_antardasha": next(
            (a["lord"] for a in (current or {}).get("antardashas", [])
             if a["current"]), None),
    }


def _antardashas(md_lord: str, md_start: datetime, md_span_years: float,
                 now: datetime) -> list:
    # For a partial first mahadasha this is an approximation (antardasha
    # sequence is taken proportionally over the remaining span).
    start_idx = next(i for i, (l, _) in enumerate(DASHA_SEQUENCE)
                     if l == md_lord)
    out = []
    cursor = md_start
    for i in range(9):
        lord, yrs = DASHA_SEQUENCE[(start_idx + i) % 9]
        span = md_span_years * yrs / 120.0
        end = cursor + timedelta(days=span * YEAR_DAYS)
        out.append({
            "lord": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "current": cursor <= now < end,
        })
        cursor = end
    return out
