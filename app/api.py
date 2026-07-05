from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from fastapi.responses import Response

from .core import (daymuhurta, festivals as festivals_mod,
                   gochar as gochar_mod, muhurta as muhurta_mod, naming,
                   varshaphal as varshaphal_mod, yogas as yogas_mod)
from .core.astro import SIGN_LORDS, SIGNS, compute_chart
from .core.matching import (GANA, NADI, NAK_GANA, NAK_NADI_PATTERN, NAK_YONI,
                            SIGN_VARNA, VARNA_ORDER, YONI_ANIMALS)
from .services.suggestions import build_suggestions, career_analysis
from .core.dasha import vimshottari
from .core.matching import ashtakoota, mangal_dosha
from .core.panchanga import compute_panchanga
from .schemas import (BirthDetails, ChatRequest, DayMuhurtaRequest,
                      MatchRequest, MuhurtaRequest, PalmGuidedRequest,
                      PalmImageRequest, ProfileIn, VarshaphalRequest)
from .services import auth as auth_svc
from .services import geo, interpret, palm, retrieval, store, timeline
from .services import llm as llm_svc


def _user(request: Request) -> str:
    return getattr(request.state, "user", None) or "local"


def _check_ai_quota(request: Request):
    """Per-user daily cap on AI calls — only enforced when auth is on."""
    if not auth_svc.enabled():
        return
    from .config import get_settings
    if not store.ai_quota_ok(_user(request), get_settings().ai_daily_limit):
        raise HTTPException(429, "Daily AI limit reached — try again "
                                 "tomorrow.")
from .services.llm import provider_status

router = APIRouter(prefix="/api")

_DATA = Path(__file__).resolve().parent / "data"
ODIA_LABELS = json.loads((_DATA / "odia_labels.json").read_text(encoding="utf-8"))
NAK_INFO = json.loads((_DATA / "nakshatra_info.json").read_text(encoding="utf-8"))

SPECIAL_ASPECTS = {"Mars": [4, 8], "Jupiter": [5, 9], "Saturn": [3, 10],
                   "Rahu": [5, 9], "Ketu": [5, 9]}


def _houses_and_aspects(chart: dict) -> tuple[list, list]:
    asc_sign = chart["ascendant"]["sign"]
    by_house: dict[int, list] = {}
    placed: dict[str, int] = {}
    for p in chart["planets"]:
        by_house.setdefault(p["house"], []).append(p["name"])
        placed[p["name"]] = p["house"]
    houses = []
    for h in range(1, 13):
        sign = (asc_sign + h - 1) % 12
        lord = SIGN_LORDS[sign]
        houses.append({
            "house": h, "sign": sign, "sign_name": SIGNS[sign],
            "lord": lord, "lord_in_house": placed[lord],
            "occupants": by_house.get(h, []),
        })
    aspects = []
    for p in chart["planets"]:
        offs = [7] + SPECIAL_ASPECTS.get(p["name"], [])
        aspects.append({
            "planet": p["name"], "from_house": p["house"],
            "aspects_houses": sorted((p["house"] - 1 + o - 1) % 12 + 1
                                     for o in offs),
        })
    return houses, aspects


def _avakahada(chart: dict) -> dict:
    """Traditional Avakahada Chakra details from the janma rashi/nakshatra."""
    ms, nk = chart["moon_sign"], chart["moon_nakshatra"]["index"]
    return {
        "varna": VARNA_ORDER[SIGN_VARNA[ms]],
        "yoni": YONI_ANIMALS[NAK_YONI[nk]],
        "gana": GANA[NAK_GANA[nk]].capitalize(),
        "nadi": NADI[NAK_NADI_PATTERN[nk % 9]],
        "rashi_lord": SIGN_LORDS[ms],
        "nakshatra_lord": ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                           "Jupiter", "Saturn", "Mercury"][nk % 9],
        "paya": _paya(next(p["house"] for p in chart["planets"]
                           if p["name"] == "Moon")),
    }


def _paya(moon_house: int) -> str:
    if moon_house in (1, 6, 11):
        return "Gold (Swarna)"
    if moon_house in (2, 5, 9):
        return "Silver (Rajata)"
    if moon_house in (3, 7, 10):
        return "Copper (Tamra)"
    return "Iron (Lauha)"


def _resolve_location(b: BirthDetails,
                      dt: datetime | None = None) -> tuple[float, float, float, str]:
    """Returns (lat, lon, tz_offset, label). The offset is DST-aware for the
    given datetime when the place comes from the database (world cities)."""
    if b.lat is not None and b.lon is not None:
        return b.lat, b.lon, b.tz_offset, b.place or "custom"
    if b.place:
        hit = geo.resolve(b.place)
        if hit:
            tz = geo.tz_offset_for(hit["tzname"], dt or datetime.now())
            return hit["lat"], hit["lon"], tz, \
                f"{hit['city']}, {hit['state']}"
    raise HTTPException(400, "Place not found — pick one from /api/places "
                             "or supply lat/lon.")


def _parse_dt(b: BirthDetails) -> datetime:
    try:
        return datetime.strptime(f"{b.date} {b.time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(400, "date must be YYYY-MM-DD and time HH:MM")


def _full_kundli(b: BirthDetails) -> dict:
    dt = _parse_dt(b)
    lat, lon, tz, place_label = _resolve_location(b, dt)
    chart = compute_chart(dt, tz, lat, lon)
    pancha = compute_panchanga(dt, tz, lat, lon)
    dashas = vimshottari(
        next(p for p in chart["planets"] if p["name"] == "Moon")["longitude"],
        dt)
    ys = yogas_mod.detect_yogas(chart)
    dosha = mangal_dosha(chart)
    report = interpret.rule_based_report(chart, dashas, ys, dosha)
    names = naming.suggest_names(chart["moon_nakshatra"]["index"],
                                 chart["moon_nakshatra"]["pada"], b.gender)
    life = timeline.build_timeline(dashas, dt.year)
    houses, aspects = _houses_and_aspects(chart)
    lucky = naming.RASHI_LUCKY[chart["moon_sign"]]
    return {
        "houses": houses,
        "aspects": aspects,
        "avakahada": _avakahada(chart),
        "nakshatra_info": {
            "moon": {"name": chart["moon_nakshatra"]["name"],
                     **NAK_INFO[chart["moon_nakshatra"]["name"]]},
            "lagna": {"name": chart["ascendant"]["nakshatra"]["name"],
                      **NAK_INFO[chart["ascendant"]["nakshatra"]["name"]]},
        },
        "lucky": lucky,
        "suggestions": build_suggestions(chart, dashas, dosha, lucky),
        "career": career_analysis(chart, dashas),
        "gochar": gochar_mod.gochar_report(chart["moon_sign"], tz),
        "input": {"name": b.name, "date": b.date, "time": b.time,
                  "place": place_label, "lat": lat, "lon": lon,
                  "tz_offset": tz},
        "chart": chart,
        "panchanga": pancha,
        "dasha": dashas,
        "yogas": ys,
        "mangal_dosha": dosha,
        "report": report,
        "name_suggestions": names,
        "timeline": life,
        "odia_labels": ODIA_LABELS,
        "llm": provider_status(),
    }


@router.get("/health")
def health():
    return {"status": "ok", **provider_status()}


@router.get("/places")
def places(q: str = Query("", min_length=0)):
    return geo.search(q)


@router.post("/kundli")
def kundli(b: BirthDetails):
    return _full_kundli(b)


@router.post("/kundli/pdf")
def kundli_pdf(b: BirthDetails):
    from .services.pdf_report import build_pdf
    data = _full_kundli(b)
    pdf = build_pdf(data)
    fname = (b.name or "kundli").replace(" ", "_") + "_report.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'attachment; filename="{fname}"'})


@router.post("/kundli/ai")
async def kundli_ai(b: BirthDetails, request: Request):
    _check_ai_quota(request)
    data = _full_kundli(b)
    narrative = await interpret.ai_narrative(
        data["chart"], data["dasha"], data["yogas"], data["mangal_dosha"],
        data["panchanga"], b.name, b.language)
    return narrative


@router.post("/match")
def match(req: MatchRequest):
    out = {}
    charts = {}
    for label, b in (("boy", req.boy), ("girl", req.girl)):
        dt = _parse_dt(b)
        lat, lon, tz, _ = _resolve_location(b, dt)
        chart = compute_chart(dt, tz, lat, lon)
        charts[label] = chart
        out[label] = {
            "name": b.name,
            "rashi": chart["moon_sign_name"],
            "nakshatra": chart["moon_nakshatra"],
            "mangal_dosha": mangal_dosha(chart),
        }
    result = ashtakoota(
        {"moon_sign": charts["boy"]["moon_sign"],
         "moon_nak": charts["boy"]["moon_nakshatra"]["index"]},
        {"moon_sign": charts["girl"]["moon_sign"],
         "moon_nak": charts["girl"]["moon_nakshatra"]["index"]})
    both_manglik = (out["boy"]["mangal_dosha"]["manglik"]
                    == out["girl"]["mangal_dosha"]["manglik"])
    result["mangal_note"] = (
        "Mangal dosha status matches between the charts."
        if both_manglik else
        "One chart carries Mangal dosha and the other does not — "
        "traditionally this asks for remedies or deeper analysis.")
    return {"partners": out, "ashtakoota": result}


@router.post("/muhurta")
def muhurta(req: MuhurtaRequest):
    """Best marriage dates + auspicious lagna windows for a couple."""
    charts = {}
    for label, b in (("boy", req.boy), ("girl", req.girl)):
        dt = _parse_dt(b)
        lat, lon, tz, _ = _resolve_location(b, dt)
        charts[label] = compute_chart(dt, tz, lat, lon)

    venue_place = req.venue or req.girl.place or "Bhubaneswar"
    venue = geo.resolve(venue_place)
    if not venue:
        raise HTTPException(400, f"Venue '{venue_place}' not found.")

    start = (datetime.strptime(req.from_date, "%Y-%m-%d")
             if req.from_date else datetime.now())
    venue = {**venue, "tz_offset": geo.tz_offset_for(venue["tzname"], start)}
    dates = muhurta_mod.find_marriage_dates(
        boy_nak=charts["boy"]["moon_nakshatra"]["index"],
        girl_nak=charts["girl"]["moon_nakshatra"]["index"],
        boy_sign=charts["boy"]["moon_sign"],
        girl_sign=charts["girl"]["moon_sign"],
        start=start, days=req.months * 30,
        tz=venue["tz_offset"], lat=venue["lat"], lon=venue["lon"])
    return {
        "venue": f"{venue['city']}, {venue['state']}",
        "window": f"{start.strftime('%Y-%m-%d')} + {req.months} months",
        "boy": {"rashi": charts["boy"]["moon_sign_name"],
                "nakshatra": charts["boy"]["moon_nakshatra"]["name"]},
        "girl": {"rashi": charts["girl"]["moon_sign_name"],
                 "nakshatra": charts["girl"]["moon_nakshatra"]["name"]},
        "dates": dates,
        "note": ("Dates pass vivaha-nakshatra, tithi, tara bala and chandra "
                 "bala checks for both charts; higher score = cleaner "
                 "muhurta. Lagna windows show local times when auspicious "
                 "signs rise at the venue — confirm the final muhurta with "
                 "your family purohita."),
    }


@router.post("/daymuhurta")
def day_muhurta(req: DayMuhurtaRequest):
    """Activity muhurta (trading, business, travel...) for a day + ranking."""
    date = (datetime.strptime(req.date, "%Y-%m-%d")
            if req.date else datetime.now())
    hit = geo.resolve(req.place)
    if not hit:
        raise HTTPException(400, f"Place '{req.place}' not found.")
    tz = geo.tz_offset_for(hit["tzname"], date)

    birth_nak = birth_sign = None
    if req.birth and req.birth.date and req.birth.place:
        bdt = _parse_dt(req.birth)
        blat, blon, btz, _ = _resolve_location(req.birth, bdt)
        bchart = compute_chart(bdt, btz, blat, blon)
        birth_nak = bchart["moon_nakshatra"]["index"]
        birth_sign = bchart["moon_sign"]

    out = daymuhurta.activity_muhurta(
        date.replace(hour=12, minute=0, second=0, microsecond=0),
        tz, hit["lat"], hit["lon"], req.activity, req.scan_days,
        birth_nak, birth_sign)
    out["place"] = f"{hit['city']}, {hit['state']}"
    out["personalised"] = birth_nak is not None
    return out


@router.get("/panchanga")
def panchanga(date: str, time: str = "06:00", place: str = "Bhubaneswar"):
    b = BirthDetails(date=date, time=time, place=place)
    dt = _parse_dt(b)
    lat, lon, tz, label = _resolve_location(b, dt)
    pancha = compute_panchanga(dt, tz, lat, lon)
    windows = daymuhurta.day_windows(dt, tz, lat, lon)
    moon_sign = int(pancha["moon_longitude"] // 30)
    return {"place": label,
            "panchanga": pancha,
            "windows": windows,
            "moon_rashi": SIGNS[moon_sign],
            "nakshatra_info": NAK_INFO.get(pancha["nakshatra"]["name"]),
            "odia_labels": ODIA_LABELS}


@router.post("/names")
def names(b: BirthDetails):
    dt = _parse_dt(b)
    lat, lon, tz, _ = _resolve_location(b, dt)
    chart = compute_chart(dt, tz, lat, lon)
    nk = chart["moon_nakshatra"]
    return {
        "janma_nakshatra": nk,
        "rashi": chart["moon_sign_name"],
        "lucky": naming.RASHI_LUCKY[chart["moon_sign"]],
        "nakshatra_info": NAK_INFO.get(nk["name"]),
        "suggestions": naming.suggest_names(nk["index"], nk["pada"], b.gender),
    }


@router.get("/festivals")
def festivals(year: int, place: str = "Bhubaneswar",
              ekadashi: bool = False):
    hit = geo.resolve(place)
    if not hit:
        raise HTTPException(400, f"Place '{place}' not found.")
    tz = geo.tz_offset_for(hit["tzname"], datetime(year, 6, 1))
    fests = festivals_mod.year_festivals(year, tz, hit["lat"], hit["lon"],
                                         include_ekadashi=ekadashi)
    return {"year": year, "place": f"{hit['city']}, {hit['state']}",
            "festivals": fests}


@router.post("/varshaphal")
def varshaphal(req: VarshaphalRequest):
    dt = _parse_dt(req.birth)
    lat, lon, tz, _ = _resolve_location(req.birth, dt)
    natal = compute_chart(dt, tz, lat, lon)
    sun_lon = next(p for p in natal["planets"]
                   if p["name"] == "Sun")["longitude"]
    try:
        return varshaphal_mod.varshaphal(sun_lon, dt, req.year, tz, lat, lon)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---- saved profiles (per signed-in user) ----
@router.get("/profiles")
def profiles(request: Request):
    return store.list_profiles(_user(request))


@router.post("/profiles")
def save_profile(p: ProfileIn, request: Request):
    if not p.name.strip():
        raise HTTPException(400, "Profile needs a name.")
    return store.save_profile(_user(request), p.name.strip(), p.gender,
                              p.date, p.time, p.place)


@router.delete("/profiles/{pid}")
def delete_profile(pid: int, request: Request):
    if not store.delete_profile(_user(request), pid):
        raise HTTPException(404, "Profile not found.")
    return {"deleted": pid}


@router.post("/feedback")
def feedback(request: Request, body: dict):
    msg = (body.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "Empty feedback.")
    store.save_feedback(_user(request), msg)
    return {"ok": True}


# ---- chat astrologer ----
@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    _check_ai_quota(request)
    data = _full_kundli(req.birth)
    c = data["chart"]
    facts = (
        f"Native: {req.birth.name or 'the native'}; lagna "
        f"{c['ascendant']['sign_name']}; rashi {c['moon_sign_name']}; "
        f"janma nakshatra {c['moon_nakshatra']['name']} pada "
        f"{c['moon_nakshatra']['pada']}. Placements: "
        + "; ".join(f"{p['name']} in {p['sign_name']} (house {p['house']}, "
                    f"{p['dignity']})" for p in c["planets"])
        + f". Current dasha: {data['dasha']['current_mahadasha']} MD / "
          f"{data['dasha']['current_antardasha']} AD. Yogas: "
        + (", ".join(y["name"] for y in data["yogas"]) or "none")
        + f". Manglik: {data['mangal_dosha']['manglik']}. Sade Sati: "
          f"{data['gochar']['sade_sati']['type']}.")
    passages = retrieval.retrieve(req.question + " " + facts, k=5)

    convo = "\n".join(f"{'Q' if h.get('role') == 'user' else 'A'}: {h.get('text','')}"
                      for h in req.history[-6:])
    lang = "Answer in Odia (ଓଡ଼ିଆ)." if req.language == "or" else "Answer in English."
    prompt = (
        f"Chart facts (ground truth, already computed):\n{facts}\n\n"
        f"Classical passages that may help:\n"
        + "\n".join("- " + p["text"] for p in passages)
        + (f"\n\nConversation so far:\n{convo}" if convo else "")
        + f"\n\nQuestion: {req.question}\n\nAnswer specifically from THIS "
          "chart in under 200 words. Be warm, concrete and non-fatalistic; "
          "suggest a simple remedy when relevant.")
    system = ("You are an experienced, kind Vedic astrologer from Odisha. "
              "Never predict death or disaster. " + lang)
    answer = await llm_svc.generate(prompt, system=system)
    if answer is None:
        return {"ai": False,
                "answer": ("(No AI key configured — showing the computed "
                           "facts and matching classical passages.)\n\n"
                           + facts + "\n\n"
                           + "\n".join("📜 " + p["text"] for p in passages)),
                }
    return {"ai": True, "answer": answer}


@router.get("/palm/questions")
def palm_questions():
    return {"questions": palm.QUESTIONS}


@router.post("/palm/guided")
def palm_guided(req: PalmGuidedRequest):
    return palm.read_palm_guided(req.answers)


@router.post("/palm/image")
async def palm_image(req: PalmImageRequest, request: Request):
    _check_ai_quota(request)
    b64 = req.image_base64
    if "," in b64[:64]:  # strip data: URI prefix if present
        b64 = b64.split(",", 1)[1]
    return await palm.read_palm_image(b64, req.context, req.language)
