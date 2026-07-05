"""Personalised 'what to do' suggestions from the kundli — rule-based, free.

Produces actionable cards: career direction, strengths to leverage, remedies
for weak grahas, current dasha guidance, and lucky essentials.
"""
from __future__ import annotations

from ..core.astro import SIGN_LORDS, SIGNS

PLANET_REMEDY = {
    "Sun": {"mantra": "Om Ghrinih Suryaya Namah / Aditya Hridaya", "day": "Sunday",
            "charity": "wheat, jaggery, copper; respect your father & elders",
            "practice": "offer water to the rising Sun (arghya)"},
    "Moon": {"mantra": "Om Som Somaya Namah / Shiva upasana", "day": "Monday",
             "charity": "rice, milk, white cloth; care for your mother",
             "practice": "keep Monday fasts; drink water from a silver vessel"},
    "Mars": {"mantra": "Hanuman Chalisa / Om Angarakaya Namah", "day": "Tuesday",
             "charity": "red lentils (masoor), sweets to brothers/soldiers",
             "practice": "physical discipline — exercise, control anger"},
    "Mercury": {"mantra": "Om Budhaya Namah / Vishnu Sahasranama", "day": "Wednesday",
                "charity": "green moong, books to students",
                "practice": "feed cows with green fodder; keep accounts honest"},
    "Jupiter": {"mantra": "Om Brihaspataye Namah / Guru stotra", "day": "Thursday",
                "charity": "chana dal, turmeric, yellow cloth; serve teachers",
                "practice": "respect gurus; study scriptures on Thursdays"},
    "Venus": {"mantra": "Om Shukraya Namah / Sri Suktam", "day": "Friday",
              "charity": "white sweets, curd, clothes to young women",
              "practice": "keep the home clean & beautiful; honour your spouse"},
    "Saturn": {"mantra": "Om Sham Shanicharaya Namah / Dasharatha Shani Stotra",
               "day": "Saturday",
               "charity": "black til, mustard oil, iron; feed crows & the poor",
               "practice": "serve workers and elders; Saturday oil-lamp at Shani shrine"},
    "Rahu": {"mantra": "Om Rahave Namah / Durga upasana", "day": "Saturday",
             "charity": "blue/black cloth, coconut; help outcasts & migrants",
             "practice": "avoid intoxants and shortcuts; keep routines grounded"},
    "Ketu": {"mantra": "Om Ketave Namah / Ganesha upasana", "day": "Tuesday",
             "charity": "blankets, multi-coloured cloth; feed stray dogs",
             "practice": "meditation and seva — detachment is Ketu's medicine"},
}

CAREER_BY_LORD = {
    "Sun": "government, administration, leadership roles, medicine, politics",
    "Moon": "public-facing work, hospitality, nursing, marine/liquids, psychology",
    "Mars": "engineering, defence/police, sports, real estate, surgery, machinery",
    "Mercury": "commerce, accounting, writing, IT & data, communication, trade",
    "Jupiter": "teaching, law, finance/banking, counselling, priesthood, management",
    "Venus": "arts & design, entertainment, fashion, vehicles, luxury goods, hotels",
    "Saturn": "industry, mining, agriculture, labour management, research, oil & iron",
    "Rahu": "technology, foreign trade, aviation, media, unconventional ventures",
    "Ketu": "research, spirituality, mathematics, forensics, alternative healing",
}

DASHA_DO = {
    "Sun": "Seek visibility: apply for promotions, government work, build authority. Keep the ego soft at home.",
    "Moon": "Nurture networks and family; property/home matters go well. Guard emotional health, keep sleep regular.",
    "Mars": "Act boldly — property deals, fitness, technical skills flourish. Avoid litigation and rash words.",
    "Mercury": "Best years for study, certifications, business expansion and trading. Write, publish, network.",
    "Jupiter": "Expand: higher education, marriage, children, investments and dharma. Be generous — it multiplies.",
    "Venus": "Marriage, arts, vehicles and comforts are favoured. Enjoy, but avoid overindulgence and drifting focus.",
    "Saturn": "Build slowly and honestly: career consolidation through sheer work. No shortcuts; health discipline pays.",
    "Rahu": "Unconventional and foreign opportunities rise fast — take them, but stay truthful and grounded.",
    "Ketu": "Simplify. Research, spirituality and specialised mastery deepen. Big material pushes feel unrewarding — let them wait.",
}


def career_analysis(chart: dict, dasha: dict) -> dict:
    """Career deep-dive: 10th house, obstacles with remedies, dasha outlook."""
    planets = {p["name"]: p for p in chart["planets"]}
    asc_sign = chart["ascendant"]["sign"]
    tenth_sign = (asc_sign + 9) % 12
    tenth_lord = SIGN_LORDS[tenth_sign]
    eleventh_lord = SIGN_LORDS[(asc_sign + 10) % 12]
    tl = planets[tenth_lord]
    occupants = [p for p in chart["planets"] if p["house"] == 10]

    overview = (
        f"Your 10th house of career is {SIGNS[tenth_sign]}, ruled by "
        f"{tenth_lord}. {tenth_lord} sits in your {tl['house']}th house in "
        f"{tl['sign_name']} ({tl['dignity']}). Natural fields: "
        f"{CAREER_BY_LORD[tenth_lord]}.")
    if occupants:
        overview += (" The 10th house itself holds "
                     + ", ".join(p["name"] for p in occupants)
                     + ", adding those significations to your public work.")

    obstacles = []

    def add(issue, effect, remedy):
        obstacles.append({"issue": issue, "effect": effect, "remedy": remedy})

    if tl["dignity"] == "debilitated":
        r = PLANET_REMEDY[tenth_lord]
        add(f"10th lord {tenth_lord} is debilitated",
            "Career growth feels harder-earned than for peers; recognition comes late.",
            f"Strengthen {tenth_lord}: {r['mantra']} on {r['day']}s; charity: {r['charity']}.")
    if tl["house"] in (6, 8, 12):
        where = {6: "6th (service/competition)", 8: "8th (transformation)",
                 12: "12th (foreign/behind-the-scenes)"}[tl["house"]]
        add(f"10th lord placed in the {where} house",
            {6: "Career comes through service, competition or litigation-heavy fields — expect rivals, and beat them on merit.",
             8: "Career sees sudden turns and re-inventions; research, insurance, occult or crisis-management fields absorb this energy well.",
             12: "Fulfilment may come abroad, in MNCs, hospitals, ashrams or remote/back-office work rather than local limelight."}[tl["house"]],
            "Choose fields matching this placement instead of fighting it; "
            "strengthen the lord on its weekday.")
    for name in ("Rahu", "Ketu"):
        if planets[name]["house"] == 10:
            add(f"{name} in the 10th house",
                "Ambition and unconventional rises (Rahu) or periodic detachment from status (Ketu); reputation can swing.",
                "Ground the career in ethics and routine; Durga/Ganesha upasana steadies the nodes.")
    if planets["Saturn"]["house"] == 10 and planets["Saturn"]["dignity"] not in ("own sign", "exalted"):
        add("Saturn in the 10th house",
            "Slow early career with heavy responsibility; big growth after mid-30s if honest.",
            "Never take shortcuts; serve seniors and juniors alike; Saturday Shani remedies.")
    sat_aspects = sorted((planets["Saturn"]["house"] - 1 + o - 1) % 12 + 1
                         for o in (3, 7, 10))
    if 10 in sat_aspects and planets["Saturn"]["house"] != 10:
        add("Saturn aspects your 10th house",
            "Delays and periodic pressure at work — but what is built survives.",
            "Patience and documentation are your armour; Shani remedies on Saturdays.")
    if planets["Sun"]["dignity"] == "debilitated":
        r = PLANET_REMEDY["Sun"]
        add("Sun (authority karaka) is debilitated",
            "Friction with bosses/government; self-doubt about leadership.",
            f"{r['practice']}; {r['mantra']} on {r['day']}s.")
    if not obstacles:
        obstacles.append({
            "issue": "No major structural affliction to the 10th house",
            "effect": "Career obstacles in your chart are period-driven (dasha), not permanent.",
            "remedy": "During difficult antardashas, support the period lord (see dasha guidance)."})

    # dasha-wise outlook: current + next few periods
    outlook = []
    now_found = False
    for md in dasha["mahadashas"]:
        if md.get("current"):
            now_found = True
        if not now_found or len(outlook) >= 4:
            continue
        lord = md["lord"]
        p = planets[lord]
        score = 0
        if lord in (tenth_lord, eleventh_lord):
            score += 2
        if p["house"] in (10, 11):
            score += 2
        if p["house"] in (1, 4, 5, 9):
            score += 1
        if p["dignity"] in ("exalted", "own sign"):
            score += 1
        if p["dignity"] == "debilitated":
            score -= 2
        if p["house"] in (6, 8, 12):
            score -= 1
        rating = ("strongly favourable" if score >= 3 else
                  "favourable" if score >= 1 else
                  "mixed — effort years" if score >= -1 else
                  "challenging — consolidate, don't gamble")
        outlook.append({
            "period": f"{lord} mahadasha ({md['start']} → {md['end']})",
            "current": bool(md.get("current")),
            "rating": rating,
            "advice": DASHA_DO[lord],
        })

    return {"overview": overview,
            "fields": CAREER_BY_LORD[tenth_lord],
            "obstacles": obstacles,
            "outlook": outlook}


def build_suggestions(chart: dict, dasha: dict, dosha: dict,
                      lucky: dict) -> list[dict]:
    planets = {p["name"]: p for p in chart["planets"]}
    asc_sign = chart["ascendant"]["sign"]
    out: list[dict] = []

    # 1. Career direction: 10th house lord + planets in the 10th
    tenth_sign = (asc_sign + 9) % 12
    tenth_lord = SIGN_LORDS[tenth_sign]
    occupants = [p["name"] for p in chart["planets"] if p["house"] == 10]
    career = CAREER_BY_LORD[tenth_lord]
    text = (f"Your 10th house (career) is {SIGNS[tenth_sign]}, ruled by "
            f"{tenth_lord} — fields that suit you: {career}.")
    if occupants:
        text += (" Planets in your 10th house ("
                 + ", ".join(occupants) + ") add: "
                 + "; ".join(CAREER_BY_LORD[o] for o in occupants[:2]) + ".")
    out.append({"category": "Career", "title": "Where your work shines", "text": text})

    # 2. Strengths to leverage
    strong = [p for p in chart["planets"]
              if p["dignity"] in ("exalted", "own sign")]
    if strong:
        s = strong[0]
        out.append({
            "category": "Strength",
            "title": f"Lean on your strong {s['name']}",
            "text": (", ".join(f"{p['name']} ({p['dignity']} in {p['sign_name']}, house {p['house']})"
                               for p in strong)
                     + " — these grahas deliver with ease. Choose work, timing "
                       "and even weekdays ruled by them for important moves."),
        })

    # 3. Remedies for weak planets
    weak = [p for p in chart["planets"] if p["dignity"] == "debilitated"]
    for p in weak:
        r = PLANET_REMEDY[p["name"]]
        out.append({
            "category": "Remedy",
            "title": f"Strengthen {p['name']} (debilitated in {p['sign_name']})",
            "text": (f"Mantra: {r['mantra']}. Day: {r['day']}. "
                     f"Charity: {r['charity']}. Practice: {r['practice']}."),
        })

    # 4. Mangal dosha
    if dosha.get("manglik"):
        r = PLANET_REMEDY["Mars"]
        out.append({
            "category": "Remedy",
            "title": "Mangal dosha present",
            "text": ("Hanuman upasana on Tuesdays, Hanuman Chalisa, red-lentil "
                     "charity; match with a fellow-manglik chart or take "
                     "traditional remedies before marriage. "
                     f"Practice: {r['practice']}."),
        })

    # 5. Current dasha guidance
    md = dasha.get("current_mahadasha")
    ad = dasha.get("current_antardasha")
    if md:
        r = PLANET_REMEDY[md]
        out.append({
            "category": "This period",
            "title": f"{md} mahadasha{f' · {ad} antardasha' if ad else ''} — what to do now",
            "text": (DASHA_DO[md] + f" Support the period lord: {r['mantra']} "
                     f"on {r['day']}s."),
        })
        if ad and ad != md:
            out.append({
                "category": "This period",
                "title": f"{ad} antardasha flavour",
                "text": DASHA_DO[ad],
            })

    # 6. Lucky essentials from janma rashi
    out.append({
        "category": "Lucky",
        "title": "Your essentials",
        "text": (f"Gemstone: {lucky['gem']} (wear only after an astrologer "
                 f"confirms the planet is favourable). Ishta-deva direction: "
                 f"{lucky['deity']}. Power day: {lucky['day']}. Janma rashi: "
                 f"{chart['moon_sign_name']}, lagna: "
                 f"{chart['ascendant']['sign_name']}."),
    })

    # 7. Moon-mind care from nakshatra gana temperament
    out.append({
        "category": "Mind",
        "title": f"Mind of {chart['moon_nakshatra']['name']}",
        "text": ("Your Moon nakshatra colours daily emotions — honour it: "
                 "keep its deity's blessing, and schedule demanding work on "
                 "days when the transit Moon is 1st/3rd/6th/7th/10th/11th "
                 "from your rashi (check the Muhurta tab's personal check)."),
    })
    return out
