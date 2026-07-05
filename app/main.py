from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .services import auth, store

app = FastAPI(title="Kundli — Odisha Vedic Astrology",
              version="2.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"],
)

OPEN_PREFIXES = ("/auth/", "/icon.svg", "/manifest.webmanifest")
OPEN_PATHS = {"/api/health"}


def _base_url(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto",
                                request.url.scheme)
    host = request.headers.get("x-forwarded-host",
                               request.headers.get("host", request.url.netloc))
    return f"{proto}://{host}"


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not auth.enabled():
        request.state.user = "local"
        return await call_next(request)
    path = request.url.path
    if path in OPEN_PATHS or any(path.startswith(p) for p in OPEN_PREFIXES):
        request.state.user = None
        return await call_next(request)
    email = auth.read_session(request.cookies.get(auth.COOKIE_NAME))
    if email and auth.is_allowed(email):
        request.state.user = email
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"detail": "Not signed in"}, status_code=401)
    return RedirectResponse("/auth/login")


@app.get("/auth/login")
def login_page(request: Request, error: str = ""):
    from .config import get_settings
    err = f'<p class="err">{error}</p>' if error else ""
    html = auth.LOGIN_PAGE.format(
        client_id=get_settings().google_client_id,
        callback=_base_url(request) + "/auth/callback",
        error=err)
    return HTMLResponse(html)


@app.post("/auth/callback")
async def login_callback(request: Request, credential: str = Form(...),
                         g_csrf_token: str = Form("")):
    # Google double-submit CSRF check
    if g_csrf_token and request.cookies.get("g_csrf_token") != g_csrf_token:
        return RedirectResponse("/auth/login?error=CSRF+check+failed",
                                status_code=303)
    info = await auth.verify_google_credential(credential)
    if not info or not info.get("email"):
        return RedirectResponse("/auth/login?error=Sign-in+failed",
                                status_code=303)
    if not auth.is_allowed(info["email"]):
        store.log_login(info["email"], allowed=False)
        return RedirectResponse(
            "/auth/login?error=This+account+is+not+on+the+invite+list",
            status_code=303)
    store.log_login(info["email"], allowed=True)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(auth.COOKIE_NAME, auth.make_session(info["email"]),
                    max_age=auth.SESSION_DAYS * 86400, httponly=True,
                    samesite="lax",
                    secure=_base_url(request).startswith("https"))
    return resp


@app.get("/auth/logout")
def logout():
    resp = RedirectResponse("/auth/login", status_code=303)
    resp.delete_cookie(auth.COOKIE_NAME)
    return resp


@app.get("/auth/me")
def me(request: Request):
    return {"email": getattr(request.state, "user", None),
            "auth_enabled": auth.enabled()}


app.include_router(router)

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
