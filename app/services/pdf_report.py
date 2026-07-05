"""Printable PDF kundli report (fpdf2 — free, offline). English text."""
from __future__ import annotations

from fpdf import FPDF

MAROON = (122, 31, 31)
SAFF = (232, 147, 12)
INK = (43, 33, 24)

ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra",
        "Ketu": "Ke"}


def _clean(s: str) -> str:
    return (s or "").encode("latin-1", "replace").decode("latin-1")


class Report(FPDF):
    def header(self):
        self.set_fill_color(*MAROON)
        self.rect(0, 0, 210, 16, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 13)
        self.set_y(4)
        self.cell(0, 8, "Jyotisha Odisha - Kundli Report", align="C")
        self.set_y(20)
        self.set_text_color(*INK)

    def sec(self, title: str):
        self.ln(3)
        self.set_font("helvetica", "B", 12)
        self.set_text_color(*MAROON)
        self.cell(0, 8, _clean(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*SAFF)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_text_color(*INK)
        self.set_font("helvetica", "", 9)

    def para(self, text: str):
        self.set_font("helvetica", "", 9)
        self.multi_cell(0, 4.6, _clean(text))
        self.ln(1)

    def table(self, headers: list[str], rows: list[list], widths=None):
        widths = widths or [190 / len(headers)] * len(headers)
        self.set_font("helvetica", "B", 8.5)
        self.set_fill_color(247, 234, 208)
        for h, w in zip(headers, widths):
            self.cell(w, 6, _clean(str(h)), border=1, fill=True)
        self.ln()
        self.set_font("helvetica", "", 8.5)
        for row in rows:
            if self.get_y() > 270:
                self.add_page()
            for v, w in zip(row, widths):
                self.cell(w, 5.5, _clean(str(v)), border=1)
            self.ln()
        self.ln(1)


def _east_chart(pdf: Report, chart: dict, x: float, y: float, u: float,
                title: str, use_navamsa: bool = False):
    pdf.set_draw_color(*MAROON)
    pdf.set_line_width(0.4)
    pdf.rect(x, y, 3 * u, 3 * u)
    for i in (1, 2):
        pdf.line(x + i * u, y, x + i * u, y + 3 * u)
        pdf.line(x, y + i * u, x + 3 * u, y + i * u)
    pdf.line(x, y, x + u, y + u)
    pdf.line(x + 3 * u, y, x + 2 * u, y + u)
    pdf.line(x, y + 3 * u, x + u, y + 2 * u)
    pdf.line(x + 3 * u, y + 3 * u, x + 2 * u, y + 2 * u)

    if use_navamsa:
        asc = chart["ascendant"]["navamsa_sign"]
        houses: dict[int, list] = {}
        for p in chart["planets"]:
            h = (p["navamsa_sign"] - asc) % 12 + 1
            houses.setdefault(h, []).append(ABBR[p["name"]])
    else:
        asc = chart["ascendant"]["sign"]
        houses = {}
        for p in chart["planets"]:
            houses.setdefault(p["house"], []).append(
                ABBR[p["name"]] + ("*" if p["retrograde"] else ""))

    centers = {1: (1.5, .5), 2: (.6, .3), 3: (.28, .68), 4: (.5, 1.5),
               5: (.28, 2.3), 6: (.65, 2.72), 7: (1.5, 2.5),
               8: (2.32, 2.72), 9: (2.72, 2.35), 10: (2.5, 1.5),
               11: (2.72, .68), 12: (2.35, .3)}
    pdf.set_font("helvetica", "", 6.5)
    for h, (cx, cy) in centers.items():
        sign = (asc + h - 1) % 12 + 1
        pdf.set_text_color(176, 142, 85)
        pdf.text(x + cx * u - 1.5, y + cy * u - 2.5, str(sign))
        pdf.set_text_color(*MAROON)
        items = houses.get(h, [])
        for i in range(0, len(items), 2):
            pdf.text(x + cx * u - 4, y + cy * u + 1 + (i // 2) * 3,
                     " ".join(items[i:i + 2]))
    pdf.set_text_color(*INK)
    pdf.set_font("helvetica", "B", 8)
    pdf.text(x + 1.5 * u - len(title), y + 3 * u + 4, title)


def build_pdf(d: dict) -> bytes:
    pdf = Report()
    pdf.set_auto_page_break(True, margin=14)
    pdf.add_page()

    inp, c = d["input"], d["chart"]
    pdf.sec("Birth Details")
    pdf.table(["Name", "Date", "Time", "Place", "TZ"],
              [[inp.get("name") or "-", inp["date"], inp["time"],
                inp["place"], f"UTC{inp['tz_offset']:+g}"]])

    y0 = pdf.get_y() + 2
    _east_chart(pdf, c, 15, y0, 26, "Rasi (D1)")
    _east_chart(pdf, c, 115, y0, 26, "Navamsa (D9)", use_navamsa=True)
    pdf.set_y(y0 + 3 * 26 + 8)

    pdf.sec("Key Points")
    a = d["avakahada"]
    pdf.table(["Lagna", "Rashi", "Nakshatra", "Varna", "Gana", "Nadi", "Paya"],
              [[c["ascendant"]["sign_name"], c["moon_sign_name"],
                f"{c['moon_nakshatra']['name']} p{c['moon_nakshatra']['pada']}",
                a["varna"], a["gana"], a["nadi"], a["paya"]]])

    pdf.sec("Graha Positions")
    pdf.table(["Graha", "Rashi", "Deg", "House", "Nakshatra", "Dignity"],
              [[p["name"] + (" (R)" if p["retrograde"] else ""),
                p["sign_name"], f"{p['degree_in_sign']:.2f}", p["house"],
                f"{p['nakshatra']['name']} p{p['nakshatra']['pada']}",
                p["dignity"]] for p in c["planets"]],
              widths=[28, 30, 18, 18, 60, 36])

    pdf.sec("Panchanga at Birth")
    pan = d["panchanga"]
    pdf.table(["Tithi", "Nakshatra", "Yoga", "Karana", "Vaara", "Odia Masa"],
              [[f"{pan['tithi']['paksha']} {pan['tithi']['name']}",
                pan["nakshatra"]["name"], pan["yoga"]["name"],
                pan["karana"]["name"], pan["vaara"]["name"],
                pan["odia_masa"]["name"]]])

    pdf.sec("Vimshottari Dasha")
    pdf.table(["Mahadasha", "From", "To", "Years"],
              [[("> " if m.get("current") else "") + m["lord"],
                m["start"], m["end"], m["years"]]
               for m in d["dasha"]["mahadashas"][:9]])

    if d.get("yogas"):
        pdf.sec("Yogas & Doshas")
        for yg in d["yogas"]:
            pdf.para(f"- {yg['name']}: {yg['text']}")
        md = d["mangal_dosha"]
        pdf.para(f"Mangal Dosha: {'YES' if md['manglik'] else 'No'} "
                 f"(Mars {md['from_lagna_house']} from lagna, "
                 f"{md['from_moon_house']} from Moon)")

    if d.get("suggestions"):
        pdf.sec("What To Do - Personal Suggestions")
        for s in d["suggestions"]:
            pdf.para(f"[{s['category']}] {s['title']}: {s['text']}")

    car = d.get("career")
    if car:
        pdf.sec("Career - Future & Obstacles")
        pdf.para(car["overview"])
        for o in car["obstacles"]:
            pdf.para(f"Obstacle: {o['issue']} - {o['effect']} "
                     f"Remedy: {o['remedy']}")
        for o in car["outlook"]:
            pdf.para(f"{o['period']}: {o['rating'].upper()} - {o['advice']}")

    g = d.get("gochar")
    if g:
        pdf.sec(f"Current Transits (Gochar) as of {g['as_of']}")
        if g["sade_sati"]["active"]:
            ss = g["sade_sati"]
            pdf.para(f"{ss['type']} ACTIVE - {ss['phase']}. {ss['meaning']} "
                     f"Ends approx {ss['ends_approx']}. Remedy: {ss['remedy']}")
        else:
            pdf.para(g["sade_sati"]["meaning"])
        pdf.table(["Planet", "Now in", "House from Moon", "Effect"],
                  [[t["planet"], t["sign"], t["house_from_moon"],
                    ("+ " if t["favourable"] else "- ") + t["effect"]]
                   for t in g["transits"]],
                  widths=[24, 28, 32, 106])

    pdf.ln(4)
    pdf.set_font("helvetica", "I", 7.5)
    pdf.para("Generated by Jyotisha Odisha (Swiss Ephemeris, Lahiri ayanamsa, "
             "whole-sign houses). Traditional guidance for cultural use - "
             "not medical, legal or financial advice.")
    return bytes(pdf.output())
