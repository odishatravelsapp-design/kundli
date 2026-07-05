from __future__ import annotations

from pydantic import BaseModel, Field


class BirthDetails(BaseModel):
    name: str = ""
    gender: str = "any"           # male | female | any
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field("06:00", description="HH:MM (24h local)")
    place: str | None = None      # looked up in offline DB
    lat: float | None = None      # or give coordinates directly
    lon: float | None = None
    tz_offset: float = 5.5
    language: str = "en"          # en | or


class MatchRequest(BaseModel):
    boy: BirthDetails
    girl: BirthDetails


class MuhurtaRequest(BaseModel):
    boy: BirthDetails
    girl: BirthDetails
    from_date: str = ""            # YYYY-MM-DD, default today
    months: int = Field(6, ge=1, le=24)
    venue: str = ""                # wedding place; defaults to girl's place


class DayMuhurtaRequest(BaseModel):
    activity: str = "trading"     # trading|business|travel|grihapravesh|general
    date: str = ""                # YYYY-MM-DD, default today
    place: str = "Bhubaneswar"
    scan_days: int = Field(0, ge=0, le=90)
    birth: BirthDetails | None = None   # optional personalisation


class VarshaphalRequest(BaseModel):
    birth: BirthDetails
    year: int


class ChatRequest(BaseModel):
    birth: BirthDetails
    question: str
    history: list[dict] = []      # [{role: "user"|"assistant", text: str}]
    language: str = "en"


class ProfileIn(BaseModel):
    name: str
    gender: str = "any"
    date: str
    time: str = "06:00"
    place: str


class PalmGuidedRequest(BaseModel):
    answers: dict[str, str]


class PalmImageRequest(BaseModel):
    image_base64: str             # JPEG, base64 (no data: prefix)
    context: str = ""
    language: str = "en"
