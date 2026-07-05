"""Saved birth profiles — SQLite (std-lib, free, persisted via docker volume)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "userdata"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "profiles.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT DEFAULT 'any',
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        place TEXT NOT NULL,
        created TEXT DEFAULT CURRENT_TIMESTAMP)""")
    return con


def list_profiles() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT id,name,gender,date,time,place FROM profiles "
            "ORDER BY name").fetchall()
    return [{"id": r[0], "name": r[1], "gender": r[2], "date": r[3],
             "time": r[4], "place": r[5]} for r in rows]


def save_profile(name: str, gender: str, date: str, time: str,
                 place: str) -> dict:
    with _conn() as con:
        # upsert by name
        row = con.execute("SELECT id FROM profiles WHERE name=?",
                          (name,)).fetchone()
        if row:
            con.execute("UPDATE profiles SET gender=?,date=?,time=?,place=? "
                        "WHERE id=?", (gender, date, time, place, row[0]))
            pid = row[0]
        else:
            cur = con.execute(
                "INSERT INTO profiles(name,gender,date,time,place) "
                "VALUES(?,?,?,?,?)", (name, gender, date, time, place))
            pid = cur.lastrowid
    return {"id": pid, "name": name}


def delete_profile(pid: int) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM profiles WHERE id=?", (pid,))
    return cur.rowcount > 0
