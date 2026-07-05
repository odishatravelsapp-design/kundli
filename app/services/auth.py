"""Google Sign-In auth with an email allowlist.

Auth is OFF unless GOOGLE_CLIENT_ID is set (so local Docker stays open).
Sessions are stdlib HMAC-signed cookies — no extra dependencies. Google ID
tokens are verified server-side via Google's tokeninfo endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import time

import httpx

from ..config import get_settings

COOKIE_NAME = "ksession"
SESSION_DAYS = 7


def enabled() -> bool:
    return bool(get_settings().google_client_id)


def allowed_emails() -> set[str]:
    return {e.strip().lower()
            for e in get_settings().allowed_emails.split(",") if e.strip()}


def is_allowed(email: str) -> bool:
    allow = allowed_emails()
    return (not allow) or email.lower() in allow


def _sign(msg: str) -> str:
    key = get_settings().session_secret.encode()
    return hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()


def make_session(email: str) -> str:
    exp = int(time.time()) + SESSION_DAYS * 86400
    msg = f"{email}|{exp}"
    b = base64.urlsafe_b64encode(msg.encode()).decode()
    return f"{b}.{_sign(msg)}"


def read_session(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    b, sig = token.rsplit(".", 1)
    try:
        msg = base64.urlsafe_b64decode(b.encode()).decode()
    except Exception:
        return None
    if not hmac.compare_digest(_sign(msg), sig):
        return None
    email, _, exp = msg.partition("|")
    if not exp.isdigit() or int(exp) < time.time():
        return None
    return email


async def verify_google_credential(credential: str) -> dict | None:
    """Verify a Google ID token; returns {email, name} or None."""
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get("https://oauth2.googleapis.com/tokeninfo",
                        params={"id_token": credential})
    if r.status_code != 200:
        return None
    info = r.json()
    if info.get("aud") != get_settings().google_client_id:
        return None
    if info.get("email_verified") not in ("true", True):
        return None
    return {"email": info.get("email", "").lower(),
            "name": info.get("name", "")}


LOGIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — Jyotisha Odisha</title>
<style>
 body{{font-family:Georgia,serif;background:#fdf6e9;color:#2b2118;display:flex;
   align-items:center;justify-content:center;min-height:100vh;margin:0}}
 .box{{background:#fffdf7;border:1px solid #e5d5b8;border-radius:12px;
   padding:2.2rem;text-align:center;box-shadow:0 2px 10px #0002;max-width:360px}}
 h1{{color:#7a1f1f;font-size:1.3rem;margin:.2rem 0 .4rem}}
 p{{font-size:.9rem;color:#5a4a35}}
 .err{{color:#b3261e;font-weight:bold}}
</style>
<script src="https://accounts.google.com/gsi/client" async></script></head>
<body><div class="box">
 <div style="font-size:2.4rem;color:#e8930c">☸</div>
 <h1>Jyotisha Odisha</h1>
 <p>Private preview — sign in with an invited Google account.</p>
 {error}
 <div id="g_id_onload" data-client_id="{client_id}"
      data-login_uri="{callback}" data-auto_prompt="false"></div>
 <div class="g_id_signin" data-type="standard" data-theme="outline"
      data-size="large" data-text="signin_with" data-shape="pill"></div>
 <p style="font-size:.75rem;margin-top:1.4rem">Access is limited to invited
 testers. Contact the administrator if you need access.</p>
</div></body></html>"""
