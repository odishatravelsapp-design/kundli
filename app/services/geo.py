"""Offline place lookup: India/Odisha database + major world cities.

World cities carry IANA timezone names so the birth-time UTC offset is
computed correctly for the actual date (handles DST historically via
zoneinfo — still fully offline and free).
"""
from __future__ import annotations

import csv
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def _load() -> list[dict]:
    rows: list[dict] = []
    with open(DATA_DIR / "cities_india.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"city": r["city"], "state": r["state"],
                         "country": "India",
                         "lat": float(r["lat"]), "lon": float(r["lon"]),
                         "tzname": "Asia/Kolkata"})
    with open(DATA_DIR / "cities_world.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"city": r["city"], "state": r["country"],
                         "country": r["country"],
                         "lat": float(r["lat"]), "lon": float(r["lon"]),
                         "tzname": r["tzname"]})
    return rows


def tz_offset_for(tzname: str, dt: datetime) -> float:
    """UTC offset in hours for a naive local datetime (DST-aware)."""
    off = dt.replace(tzinfo=ZoneInfo(tzname)).utcoffset()
    return off.total_seconds() / 3600.0 if off is not None else 5.5


def search(q: str, limit: int = 12) -> list[dict]:
    q = q.strip().lower()
    if not q:
        return []
    rows = _load()
    starts = [r for r in rows if r["city"].lower().startswith(q)]
    contains = [r for r in rows if q in r["city"].lower() and r not in starts]
    # Odisha first, then rest of India, then abroad
    key = lambda r: (r["state"] != "Odisha", r["country"] != "India",
                     r["city"])
    return sorted(starts, key=key)[:limit] + \
        sorted(contains, key=key)[:max(0, limit - len(starts))]


def resolve(place: str) -> dict | None:
    place = place.split(",")[0].strip().lower()
    for r in _load():
        if r["city"].lower() == place:
            return r
    hits = search(place, 1)
    return hits[0] if hits else None
