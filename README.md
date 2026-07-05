---
title: Jyotisha Odisha
emoji: ☸️
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 8000
pinned: false
---

# Jyotisha Odisha — Free Kundli · Panchanga · Match · Palm PWA

A **zero-cost, fully offline** Vedic astrology application built for India with
Odisha-first features. Runs locally in Docker Desktop; ready to expand to other
regional traditions.

## Features

| Feature | How it works | Cost |
|---|---|---|
| Kundli (birth chart) | Swiss Ephemeris (built-in Moshier mode — no data downloads), Lahiri ayanamsa, whole-sign houses, navamsa (D9) | Free |
| Chart styles | **East Indian (Odisha/Prachya)**, North Indian, South Indian — SVG rendered | Free |
| Panchanga | Tithi, nakshatra, yoga, karana, vaara + **Odia solar masa & Sankranti** (Pana Sankranti new year) | Free |
| Vimshottari dasha | Mahadasha + antardasha, with a **past/present/future life timeline** | Free |
| Guna Milan | Full ashtakoota 36-point matching + Mangal dosha | Free |
| Marriage muhurta | Scans months of dates against vivaha nakshatra/tithi/vaara/yoga/Bhadra rules, tara & chandra bala for **both** charts, Guru/Shukra combustion, Kharamasa — then computes auspicious **lagna windows** at the venue | Free |
| Baby names | Namakarana syllable by janma-nakshatra pada + Odia name bank + lucky gem/deity/day | Free |
| Palm reading | PWA **camera capture** → AI vision reading (needs a key) **or** free guided Samudrika reading | Free / key |
| Interpretation | Rule engine + pure-Python **BM25 retrieval** over a classical-jyotisha knowledge base (the "ML" layer — no heavy deps) | Free |
| AI narratives | Pluggable LLM adapter: Anthropic / OpenAI / Gemini / **local Ollama** — drop a key in `.env`, no code changes | Optional |
| Odia language | ଓଡ଼ିଆ labels for rashi, graha, nakshatra, masa, vaara; AI narratives in Odia | Free |
| PWA | Installable, offline app shell, camera access | Free |

## Run it (Docker Desktop)

```bash
docker compose up --build -d
# open http://localhost:8090
```

API docs: http://localhost:8090/docs

### Enable AI (optional, still works fine without)

```bash
copy .env.example .env      # then paste ONE key, e.g. ANTHROPIC_API_KEY=...
docker compose up -d --force-recreate
```

100% free AI option: uncomment the `ollama` service in `docker-compose.yml`,
set `OLLAMA_BASE_URL=http://ollama:11434` in `.env`, and pull a model:
`docker exec -it ollama ollama pull llama3.1` (text narratives; palm photo
reading needs a vision provider — Anthropic/OpenAI/Gemini).

## Architecture

```
frontend/  (static PWA — no build step)
  index.html · app.js (charts SVG, camera, Odia toggle) · sw.js · manifest
app/
  main.py            FastAPI + static mount
  api.py             /api/kundli /api/match /api/panchanga /api/names /api/palm/*
  core/              pure computation (deterministic, testable)
    astro.py         swisseph: sidereal positions, lagna, nakshatra, navamsa
    panchanga.py     tithi/yoga/karana/vaara + Odia solar masa
    dasha.py         Vimshottari MD/AD
    matching.py      ashtakoota 36 guna + mangal dosha
    yogas.py         Gajakesari, Budhaditya, Mahapurusha, Kemadruma ...
    naming.py        nakshatra-pada syllables + Odia name bank
  services/
    geo.py           offline city DB (all Odisha districts + major India)
    retrieval.py     dependency-free BM25 over data/knowledge.json (RAG)
    interpret.py     rule engine + optional LLM narrative
    palm.py          AI vision palmistry / guided Samudrika questionnaire
    timeline.py      dasha -> life history & future chapters
    llm.py           provider adapter (anthropic/openai/gemini/ollama)
  data/              cities_india.csv · knowledge.json · odia_labels.json
```

**Zero-cost principles**
- No paid API is required for any core feature; keys only *add* narratives.
- No external data downloads: Moshier ephemeris is built into pyswisseph.
- No database: bundled CSV/JSON; the whole app is one small container.

## API quick reference

```bash
curl -X POST localhost:8090/api/kundli -H "Content-Type: application/json" \
  -d '{"name":"Test","date":"1995-06-15","time":"04:30","place":"Puri"}'

curl -X POST localhost:8090/api/match -H "Content-Type: application/json" \
  -d '{"boy":{"date":"1993-01-10","time":"10:00","place":"Cuttack"},
       "girl":{"date":"1995-06-15","time":"04:30","place":"Puri"}}'

curl "localhost:8090/api/panchanga?date=2026-07-04&place=Bhubaneswar"
```

## Free-tier hosting (later)

| Option | Notes |
|---|---|
| **Hugging Face Spaces (Docker)** | Easiest: push this repo with the Dockerfile, free CPU tier, public URL, HTTPS (needed for PWA camera). Change port to 7860 or set `app_port`. |
| **Render.com free web service** | Direct Docker deploy; sleeps when idle (fine for a POC). |
| **Fly.io / Railway** | Small free allowances; `fly launch` reads the Dockerfile. |
| **Oracle Cloud Always-Free VM** | Real always-on VM (ARM); `docker compose up -d` there, add Caddy for HTTPS. Most generous truly-free option. |

The app is stateless, so any of these work without changes beyond the port.

## Roadmap / expansion ideas

- More divisional charts (D10 career, D7 children), sunrise-based tithi & festival calendar
- Regional presets: Bengali (almost same East Indian chart), Tamil/Kerala (South style already included)
- Train a small on-device model on annotated palm datasets to segment lines before AI reading
- Persist charts (SQLite) + user accounts when hosting

> Traditional guidance for cultural and educational use — not medical, legal or financial advice.
