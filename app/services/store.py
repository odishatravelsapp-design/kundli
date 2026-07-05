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
        owner TEXT DEFAULT 'local',
        created TEXT DEFAULT CURRENT_TIMESTAMP)""")
    try:  # migrate pre-auth databases
        con.execute("ALTER TABLE profiles ADD COLUMN owner TEXT DEFAULT 'local'")
    except sqlite3.OperationalError:
        pass
    con.execute("""CREATE TABLE IF NOT EXISTS logins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, allowed INTEGER,
        created TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, message TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS ai_usage (
        email TEXT, day TEXT, count INTEGER DEFAULT 0,
        PRIMARY KEY (email, day))""")
    return con


def list_profiles(owner: str) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT id,name,gender,date,time,place FROM profiles "
            "WHERE owner=? ORDER BY name", (owner,)).fetchall()
    return [{"id": r[0], "name": r[1], "gender": r[2], "date": r[3],
             "time": r[4], "place": r[5]} for r in rows]


def save_profile(owner: str, name: str, gender: str, date: str, time: str,
                 place: str) -> dict:
    with _conn() as con:
        row = con.execute("SELECT id FROM profiles WHERE name=? AND owner=?",
                          (name, owner)).fetchone()
        if row:
            con.execute("UPDATE profiles SET gender=?,date=?,time=?,place=? "
                        "WHERE id=?", (gender, date, time, place, row[0]))
            pid = row[0]
        else:
            cur = con.execute(
                "INSERT INTO profiles(name,gender,date,time,place,owner) "
                "VALUES(?,?,?,?,?,?)", (name, gender, date, time, place,
                                        owner))
            pid = cur.lastrowid
    return {"id": pid, "name": name}


def delete_profile(owner: str, pid: int) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM profiles WHERE id=? AND owner=?",
                          (pid, owner))
    return cur.rowcount > 0


def log_login(email: str, allowed: bool) -> None:
    with _conn() as con:
        con.execute("INSERT INTO logins(email, allowed) VALUES(?,?)",
                    (email, 1 if allowed else 0))


def save_feedback(email: str, message: str) -> None:
    with _conn() as con:
        con.execute("INSERT INTO feedback(email, message) VALUES(?,?)",
                    (email, message[:2000]))


def ai_quota_ok(email: str, limit: int) -> bool:
    """Increment today's AI-call counter; False when over the limit."""
    from datetime import date
    day = date.today().isoformat()
    with _conn() as con:
        con.execute("INSERT INTO ai_usage(email, day, count) VALUES(?,?,0) "
                    "ON CONFLICT(email, day) DO NOTHING", (email, day))
        row = con.execute("SELECT count FROM ai_usage WHERE email=? AND day=?",
                          (email, day)).fetchone()
        if row[0] >= limit:
            return False
        con.execute("UPDATE ai_usage SET count=count+1 "
                    "WHERE email=? AND day=?", (email, day))
    return True
