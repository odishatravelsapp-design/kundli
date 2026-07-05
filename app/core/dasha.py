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
    now = datetime.now()

    # The opening mahadasha began before birth (elapsed portion of the
    # nakshatra) — antardashas are computed over the FULL span from that
    # notional start, then clipped at birth (classical method).
    md_full_start = birth_dt - timedelta(
        days=start_years * frac_elapsed * YEAR_DAYS)
    idx = start_lord_idx
    total = 0.0
    first = True
    while total < 120.0:
        lord, full_years = DASHA_SEQUENCE[idx % 9]
        end = md_full_start + timedelta(days=full_years * YEAR_DAYS)
        start_visible = birth_dt if first else md_full_start
        span = (end - start_visible).days / YEAR_DAYS
        period = {
            "lord": lord,
            "start": start_visible.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": round(span, 2),
            "current": start_visible <= now < end,
        }
        ads = _antardashas(lord, md_full_start, float(full_years), now)
        if first:
            kept = []
            for a in ads:
                if a["end"] <= birth_dt.strftime("%Y-%m-%d"):
                    continue                      # finished before birth
                if a["start"] < birth_dt.strftime("%Y-%m-%d"):
                    a["start"] = birth_dt.strftime("%Y-%m-%d")
                kept.append(a)
            ads = kept
        period["antardashas"] = ads
        periods.append(period)
        total += span
        md_full_start = end
        idx += 1
        first = False

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
