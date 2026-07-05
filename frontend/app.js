/* Jyotisha Odisha — frontend */
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

let LANG = "en";
let LABELS = null;           // odia_labels from API
let LAST_KUNDLI = null;

const SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra",
  "Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"];
const PL_ABBR = {Sun:"Su",Moon:"Mo",Mars:"Ma",Mercury:"Me",Jupiter:"Ju",
  Venus:"Ve",Saturn:"Sa",Rahu:"Ra",Ketu:"Ke"};
const PL_ABBR_OR = {Sun:"ର",Moon:"ଚ",Mars:"ମ",Mercury:"ବୁ",Jupiter:"ବୃ",
  Venus:"ଶୁ",Saturn:"ଶ",Rahu:"ରା",Ketu:"କେ"};

const HOUSE_THEMES = {1:"self, body, personality and life direction",
  2:"wealth, family, food and speech",3:"courage, siblings, communication",
  4:"home, mother, land, vehicles, inner peace",5:"children, intellect, creativity",
  6:"health, service, debts, competition",7:"marriage, partnership, public dealings",
  8:"longevity, transformation, occult, inheritance",9:"fortune, dharma, father, guru",
  10:"career, status, karma, achievement",11:"gains, income, social circle",
  12:"expenditure, foreign lands, sleep, moksha"};
const PLANET_NATURE = {Sun:"soul, authority, father, vitality",
  Moon:"mind, emotions, mother",Mars:"energy, courage, land, technical skill",
  Mercury:"intellect, speech, commerce",Jupiter:"wisdom, wealth, children, dharma",
  Venus:"love, comfort, arts, spouse",Saturn:"discipline, longevity, labour",
  Rahu:"obsession, foreign influence, sudden rise",Ketu:"detachment, spirituality, research"};

const signName = s => (LANG === "or" && LABELS) ? LABELS.signs[s] || s : s;
const plName = p => (LANG === "or" && LABELS) ? LABELS.planets[p] || p : p;
const nakName = n => (LANG === "or" && LABELS) ? LABELS.nakshatras[n] || n : n;
const plAbbr = p => LANG === "or" ? PL_ABBR_OR[p] : PL_ABBR[p];

/* ---------- plumbing ---------- */
function loading(on) {
  const l = $("#loader");
  l.hidden = !on;
  l.style.display = on ? "flex" : "none";   // wins even over stale CSS
}
async function api(path, opts) {
  loading(true);
  try {
    const r = await fetch(path, opts);
    const j = await r.json();
    if (!r.ok) throw new Error(j.detail || r.statusText);
    return j;
  } finally { loading(false); }
}
function err(el, msg) { el.innerHTML = `<div class="err">⚠ ${msg}</div>`; }

/* tabs */
$$("#tabs button").forEach(b => b.onclick = () => {
  $$("#tabs button").forEach(x => x.classList.remove("active"));
  $$(".tab").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  $("#tab-" + b.dataset.tab).classList.add("active");
});

/* language toggle */
$$(".lang-toggle button").forEach(b => b.onclick = () => {
  $$(".lang-toggle button").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  LANG = b.dataset.lang;
  if (LAST_KUNDLI) renderKundli(LAST_KUNDLI);
});

/* place autocomplete */
let placeTimer;
document.addEventListener("input", e => {
  if (!e.target.matches('input[list="places"]')) return;
  clearTimeout(placeTimer);
  const q = e.target.value;
  placeTimer = setTimeout(async () => {
    if (q.length < 2) return;
    const hits = await fetch("/api/places?q=" + encodeURIComponent(q)).then(r => r.json());
    $("#places").innerHTML = hits.map(h =>
      `<option value="${h.city}">${h.city}, ${h.state}</option>`).join("");
  }, 200);
});

/* ---------- chart drawing ---------- */
function chartSVG(chart, style) {
  const ascSign = chart.ascendant.sign;
  const byHouse = {};                       // house -> [abbr,…]
  chart.planets.forEach(p => {
    (byHouse[p.house] = byHouse[p.house] || []).push(
      plAbbr(p.name) + (p.retrograde ? "*" : ""));
  });
  if (style === "south") return southChart(ascSign, byHouse);
  if (style === "north") return northChart(ascSign, byHouse);
  return eastChart(ascSign, byHouse);
}
function clickTarget(x, y, house) {
  return `<circle cx="${x}" cy="${y}" r="30" fill="transparent"
    style="cursor:pointer" data-house="${house}"><title>House ${house} — tap for meaning</title></circle>`;
}

function textLines(x, y, items, cls) {
  const rows = [];
  for (let i = 0; i < items.length; i += 3) rows.push(items.slice(i, i + 3).join(" "));
  return rows.map((r, i) =>
    `<text class="${cls}" x="${x}" y="${y + i * 14}" text-anchor="middle">${r}</text>`).join("");
}

function northChart(ascSign, byHouse) {
  const C = [[200,95],[100,45],[48,100],[100,200],[48,300],[100,352],
             [200,300],[300,352],[352,300],[300,200],[352,100],[300,45]];
  let s = `<svg class="chart" viewBox="0 0 400 400">
    <rect class="frame" x="2" y="2" width="396" height="396"/>
    <path class="ln" d="M2,2 L398,398 M398,2 L2,398 M200,2 L398,200 L200,398 L2,200 Z"/>`;
  C.forEach(([x, y], i) => {
    const h = i + 1, sign = (ascSign + i) % 12;
    s += `<text class="hnum" x="${x}" y="${y - 18}" text-anchor="middle">${sign + 1}</text>`;
    if (h === 1) s += `<text class="asc" x="${x}" y="${y - 32}" text-anchor="middle">Lagna</text>`;
    s += textLines(x, y, byHouse[h] || [], "pl");
    s += clickTarget(x, y, h);
  });
  return s + "</svg>";
}

function southChart(ascSign, byHouse) {
  const POS = {0:[1,0],1:[2,0],2:[3,0],3:[3,1],4:[3,2],5:[3,3],
               6:[2,3],7:[1,3],8:[0,3],9:[0,2],10:[0,1],11:[0,0]};
  const cell = 100;
  let s = `<svg class="chart" viewBox="0 0 400 400">
    <rect class="frame" x="2" y="2" width="396" height="396"/>`;
  for (let i = 1; i < 4; i++) {
    s += `<path class="ln" d="M${i*100},0 V400 M0,${i*100} H400"/>`;
  }
  s += `<rect x="102" y="102" width="196" height="196" fill="#fffaf0" stroke="none"/>
    <text class="asc" x="200" y="195" text-anchor="middle">Rasi</text>
    <text class="hnum" x="200" y="215" text-anchor="middle">South Indian</text>`;
  for (let sign = 0; sign < 12; sign++) {
    const [c, r] = POS[sign];
    const x = c * cell + 50, y = r * cell + 28;
    const house = ((sign - ascSign) % 12 + 12) % 12 + 1;
    s += `<text class="hnum" x="${x}" y="${y}" text-anchor="middle">${signName(SIGNS[sign])}</text>`;
    if (sign === ascSign)
      s += `<path class="ln" d="M${c*cell+4},${r*cell+22} L${c*cell+30},${r*cell+4}"/>`;
    s += textLines(x, y + 22, byHouse[house] || [], "pl");
    s += clickTarget(x, y + 20, house);
  }
  return s + "</svg>";
}

/* East Indian (Odisha/Prachya) — houses counted anticlockwise from top-middle */
function eastChart(ascSign, byHouse) {
  const u = 130; // cell
  const P = (pts) => pts.map(p => p.join(",")).join(" ");
  const regions = [
    {h:1,  poly:[[u,0],[2*u,0],[2*u,u],[u,u]],          t:[1.5*u, .5*u]},
    {h:2,  poly:[[0,0],[u,0],[u,u]],                    t:[.62*u, .32*u]},
    {h:3,  poly:[[0,0],[u,u],[0,u]],                    t:[.3*u, .68*u]},
    {h:4,  poly:[[0,u],[u,u],[u,2*u],[0,2*u]],          t:[.5*u, 1.5*u]},
    {h:5,  poly:[[0,2*u],[u,2*u],[0,3*u]],              t:[.3*u, 2.34*u]},
    {h:6,  poly:[[u,2*u],[u,3*u],[0,3*u]],              t:[.66*u, 2.72*u]},
    {h:7,  poly:[[u,2*u],[2*u,2*u],[2*u,3*u],[u,3*u]],  t:[1.5*u, 2.5*u]},
    {h:8,  poly:[[2*u,2*u],[3*u,3*u],[2*u,3*u]],        t:[2.34*u, 2.72*u]},
    {h:9,  poly:[[2*u,2*u],[3*u,2*u],[3*u,3*u]],        t:[2.7*u, 2.36*u]},
    {h:10, poly:[[2*u,u],[3*u,u],[3*u,2*u],[2*u,2*u]],  t:[2.5*u, 1.5*u]},
    {h:11, poly:[[3*u,0],[3*u,u],[2*u,u]],              t:[2.7*u, .68*u]},
    {h:12, poly:[[2*u,0],[3*u,0],[2*u,u]],              t:[2.36*u, .3*u]},
  ];
  let s = `<svg class="chart" viewBox="0 0 390 390">
    <rect class="frame" x="2" y="2" width="386" height="386"/>`;
  regions.forEach(r => { s += `<polygon class="ln" points="${P(r.poly)}"/>`; });
  s += `<rect x="${u+2}" y="${u+2}" width="${u-4}" height="${u-4}" fill="#fdf0d8" stroke="none"/>
    <text class="asc" x="${1.5*u}" y="${1.42*u}" text-anchor="middle">Lagna</text>
    <text class="hnum" x="${1.5*u}" y="${1.62*u}" text-anchor="middle">${signName(SIGNS[ascSign])}</text>`;
  regions.forEach(r => {
    const sign = (ascSign + r.h - 1) % 12;
    s += `<text class="hnum" x="${r.t[0]}" y="${r.t[1] - 12}" text-anchor="middle">${sign + 1}</text>`;
    s += textLines(r.t[0], r.t[1] + 4, byHouse[r.h] || [], "pl");
    s += clickTarget(r.t[0], r.t[1], r.h);
  });
  return s + "</svg>";
}

/* ---------- KUNDLI ---------- */
$("#kundli-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const data = await api("/api/kundli", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name: f.get("name"), gender: f.get("gender"), date: f.get("date"),
        time: f.get("time"), place: f.get("place"), language: LANG,
      }),
    });
    data._style = f.get("style");
    LAST_KUNDLI = data; LABELS = data.odia_labels;
    renderKundli(data);
  } catch (ex) { err($("#kundli-result"), ex.message); }
};

function panchaCard(p) {
  const cells = [
    ["Tithi", `${p.tithi.paksha} ${p.tithi.name}`,
     p.tithi.ends ? `till ${p.tithi.ends.slice(11)} (${p.tithi.ends.slice(5, 10)})` : ""],
    ["Nakshatra", nakName(p.nakshatra.name),
     (p.nakshatra.ends ? `till ${p.nakshatra.ends.slice(11)} · ` : "") + `pada ${p.nakshatra.pada}`],
    ["Yoga", p.yoga.name, ""],
    ["Karana", p.karana.name, ""],
    ["Vaara", p.vaara.name, LABELS ? LABELS.vaara[p.vaara.name] : p.vaara.odia],
    ["Odia Masa", p.odia_masa.name, LABELS ? LABELS.masa[p.odia_masa.name] : ""],
  ];
  return `<div class="pancha-grid">` + cells.map(([k, v, o]) =>
    `<div class="cell"><div class="k">${k}</div><div class="v">${v}</div><div class="o">${o}</div></div>`
  ).join("") + `</div>` +
  (p.sankranti_note ? `<p class="hint">✦ ${p.sankranti_note}</p>` : "");
}

function navamsaOf(chart) {
  // pseudo-chart in D9: houses counted from the navamsa lagna
  const nAsc = chart.ascendant.navamsa_sign;
  return {
    ascendant: {sign: nAsc, sign_name: SIGNS[nAsc]},
    planets: chart.planets.map(p => ({
      name: p.name, retrograde: p.retrograde,
      house: ((p.navamsa_sign - nAsc) % 12 + 12) % 12 + 1,
    })),
  };
}

function renderKundli(d) {
  const c = d.chart, out = $("#kundli-result");
  const planetsRows = c.planets.map(p => `<tr>
    <td>${plName(p.name)}${p.retrograde ? " (R)" : ""}${p.vargottama ? " ✦" : ""}</td>
    <td>${signName(p.sign_name)}</td>
    <td>${p.degree_in_sign.toFixed(2)}°</td>
    <td>${p.house}</td>
    <td>${nakName(p.nakshatra.name)} (${p.nakshatra.pada})</td>
    <td>${p.dignity}</td>
    <td>${signName(p.navamsa_sign_name)}</td>
    <td>${p.strength ? `<b>${p.strength.percent}%</b> ${p.strength.label}` : "—"}</td></tr>`).join("");

  const divRows = c.planets.map(p => `<tr>
    <td>${plName(p.name)}</td><td>${signName(p.sign_name)}</td>
    <td>${signName(p.d2_sign_name || "")}</td>
    <td>${signName(p.d7_sign_name || "")}</td>
    <td>${signName(p.navamsa_sign_name)}</td>
    <td>${signName(p.d10_sign_name || "")}</td></tr>`).join("");

  const md = d.dasha.mahadashas.filter(m => m.years > 0.01).slice(0, 12);
  const dashaRows = md.map(m => `<tr class="${m.current ? "current" : ""}">
    <td>${plName(m.lord)}</td><td>${m.start}</td><td>${m.end}</td><td>${m.years}</td>
    <td>${(m.antardashas || []).map(a =>
      `<span class="badge ${a.current ? "green" : ""}" title="${a.start} → ${a.end}">${plAbbr(a.lord)}</span>`).join("")}</td></tr>`).join("");
  const cur = d.dasha.mahadashas.find(m => m.current);
  const adRows = cur && cur.antardashas ? cur.antardashas.map(a =>
    `<tr class="${a.current ? "current" : ""}"><td>${plName(cur.lord)}–${plName(a.lord)}</td>
     <td>${a.start}</td><td>${a.end}</td></tr>`).join("") : "";

  const housesRows = (d.houses || []).map(h => `<tr>
    <td>${h.house}</td><td>${signName(h.sign_name)}</td>
    <td>${plName(h.lord)}</td><td>${h.lord_in_house}</td>
    <td>${h.occupants.map(plName).join(", ") || "—"}</td></tr>`).join("");

  const aspectRows = (d.aspects || []).map(a =>
    `<tr><td>${plName(a.planet)}</td><td>${a.from_house}</td>
     <td>${a.aspects_houses.join(", ")}</td></tr>`).join("");

  const av = d.avakahada || {};
  const avCells = [["Varna", av.varna], ["Yoni", av.yoni], ["Gana", av.gana],
    ["Nadi", av.nadi], ["Rashi Lord", plName(av.rashi_lord || "")],
    ["Nakshatra Lord", plName(av.nakshatra_lord || "")], ["Paya", av.paya],
    ["Gem", (d.lucky || {}).gem], ["Deity", (d.lucky || {}).deity],
    ["Power Day", (d.lucky || {}).day]].map(([k, v]) =>
    `<div class="cell"><div class="k">${k}</div><div class="v">${v || "—"}</div></div>`).join("");

  const nakInfo = d.nakshatra_info ? `
    <p><b>🌙 ${nakName(d.nakshatra_info.moon.name)} (Moon):</b>
       deity ${d.nakshatra_info.moon.deity}; symbol: ${d.nakshatra_info.moon.symbol}.
       ${d.nakshatra_info.moon.traits}</p>
    <p><b>⬆ ${nakName(d.nakshatra_info.lagna.name)} (Lagna):</b>
       ${d.nakshatra_info.lagna.traits}</p>` : "";

  const sugg = (d.suggestions || []).map(s => `
    <div class="card"><p><span class="badge">${s.category}</span> <b>${s.title}</b></p>
    <p>${s.text}</p></div>`).join("");

  const tl = d.timeline;
  const tlHTML = ["past", "present", "future"].map(k => {
    const items = k === "present" ? (tl.present ? [tl.present] : []) : tl[k];
    return items.map(it => `<div class="tl-item ${k === "present" ? "now" : ""}">
      <div class="tl-when">${it.from} → ${it.to} · age ${it.age} ${k === "present" ? "· NOW" : ""}</div>
      <b>${plName(it.lord)} Mahadasha</b> — ${it.theme}</div>`).join("");
  }).join("");

  out.innerHTML = `
    <h2 class="sec">Birth Chart — ${d.input.name || "(no name — see suggested names below)"} · ${d.input.place}</h2>
    <div class="card">
      <div class="two-col">
        <div><p style="text-align:center"><b>Rasi (D1)</b></p>${chartSVG(c, d._style || "east")}</div>
        <div><p style="text-align:center"><b>Navamsa (D9)</b></p>${chartSVG(navamsaOf(c), d._style || "east")}</div>
      </div>
      <p style="text-align:center">
        <span class="badge">Lagna: ${signName(c.ascendant.sign_name)} ${c.ascendant.degree_in_sign}°</span>
        <span class="badge">Rashi: ${signName(c.moon_sign_name)}</span>
        <span class="badge">Nakshatra: ${nakName(c.moon_nakshatra.name)} pada ${c.moon_nakshatra.pada}</span>
        <span class="badge">Ayanamsa ${c.ayanamsa}° (Lahiri)</span>
        <span class="badge">Birth TZ: UTC${d.input.tz_offset >= 0 ? "+" : ""}${d.input.tz_offset}</span>
      </p>
      ${nakInfo}
      <div id="house-info" class="hint" style="border:1px dashed var(--line);border-radius:6px;padding:.5rem;margin-top:.5rem">
        👆 Tap any house in the chart to see its meaning.</div>
    </div>
    <h2 class="sec">Avakahada Chakra — Traditional Details</h2>
    <div class="card"><div class="pancha-grid">${avCells}</div></div>
    <h2 class="sec">💡 What To Do — Personal Suggestions</h2>
    ${sugg}
    ${d.career ? `
    <h2 class="sec">💼 Career — Future &amp; Obstacles</h2>
    <div class="card">
      <p>${d.career.overview}</p>
      <p><b>Best-suited fields:</b> ${d.career.fields}</p>
    </div>
    <div class="card">
      <p><b>Obstacles &amp; what to do about them:</b></p>
      ${d.career.obstacles.map(o => `
        <p>⚠ <b>${o.issue}</b><br>${o.effect}<br>
        <span class="badge green">Remedy</span> ${o.remedy}</p>`).join("")}
    </div>
    <div class="card">
      <p><b>Career outlook by dasha period:</b></p>
      <div class="timeline">
      ${d.career.outlook.map(o => `
        <div class="tl-item ${o.current ? "now" : ""}">
          <div class="tl-when">${o.period}${o.current ? " · NOW" : ""}</div>
          <b>${o.rating.toUpperCase()}</b> — ${o.advice}</div>`).join("")}
      </div>
    </div>` : ""}
    ${d.gochar ? `
    <h2 class="sec">🪐 Gochar — Transits Today (${d.gochar.as_of})</h2>
    <div class="card">
      ${d.gochar.sade_sati.active ? `
        <p><span class="badge red">${d.gochar.sade_sati.type} ACTIVE</span>
           <b>${d.gochar.sade_sati.phase}</b> — ${d.gochar.sade_sati.meaning}
           Ends approx <b>${d.gochar.sade_sati.ends_approx}</b>.</p>
        <p><span class="badge green">Remedy</span> ${d.gochar.sade_sati.remedy}</p>`
        : `<p><span class="badge green">No Sade Sati</span> ${d.gochar.sade_sati.meaning}</p>`}
      <p>✦ ${d.gochar.highlight}</p>
      <div style="overflow-x:auto"><table>
        <tr><th>Graha now</th><th>In sign</th><th>House from your Moon</th><th>Effect for you</th></tr>
        ${d.gochar.transits.map(t => `<tr>
          <td>${plName(t.planet)}</td><td>${signName(t.sign)}</td>
          <td>${t.house_from_moon} ${t.favourable ? "✅" : "⚠"}</td>
          <td>${t.effect}</td></tr>`).join("")}
      </table></div>
    </div>` : ""}
    <h2 class="sec">Panchanga at Birth</h2>
    <div class="card">${panchaCard(d.panchanga)}</div>
    <h2 class="sec">Graha Positions &amp; Strength</h2>
    <div class="card" style="overflow-x:auto"><table>
      <tr><th>Graha</th><th>Rashi</th><th>Degree</th><th>House</th><th>Nakshatra</th><th>Dignity</th><th>Navamsa</th><th>Strength</th></tr>
      ${planetsRows}</table>
      <p class="hint">✦ = vargottama (same sign in D1 &amp; D9 — extra firm results). Strength is a simplified shadbala score.</p>
      <details><summary><b>Divisional charts (D2 wealth · D7 children · D9 marriage · D10 career)</b></summary>
        <table><tr><th>Graha</th><th>D1</th><th>D2</th><th>D7</th><th>D9</th><th>D10</th></tr>${divRows}</table>
      </details>
    </div>
    <h2 class="sec">Houses (Bhavas) &amp; Lords</h2>
    <div class="card" style="overflow-x:auto"><table>
      <tr><th>House</th><th>Sign</th><th>Lord</th><th>Lord sits in</th><th>Occupants</th></tr>
      ${housesRows}</table>
      <details><summary><b>Planetary aspects (drishti)</b></summary>
        <table><tr><th>Graha</th><th>From house</th><th>Aspects houses</th></tr>${aspectRows}</table>
      </details>
    </div>
    <h2 class="sec">Yogas &amp; Doshas</h2>
    <div class="card">
      ${d.yogas.map(y => `<p><b>✦ ${y.name}:</b> ${y.text}</p>`).join("") || "<p>No major classical yogas detected.</p>"}
      <p><b>Mangal Dosha:</b>
        <span class="badge ${d.mangal_dosha.manglik ? "red" : "green"}">
        ${d.mangal_dosha.manglik ? "Manglik" : "Not Manglik"}</span>
        (Mars: house ${d.mangal_dosha.from_lagna_house} from lagna, ${d.mangal_dosha.from_moon_house} from Moon)
        ${d.mangal_dosha.cancellation ? "— " + d.mangal_dosha.cancellation : ""}</p>
    </div>
    <h2 class="sec">Vimshottari Dasha</h2>
    <div class="card" style="overflow-x:auto">
      <p>Balance at birth: <b>${plName(d.dasha.balance_at_birth.lord)}</b> ${d.dasha.balance_at_birth.years} yrs</p>
      <table><tr><th>Mahadasha</th><th>From</th><th>To</th><th>Years</th><th>Antardashas (hover for dates)</th></tr>${dashaRows}</table>
      ${adRows ? `<h3>Current Antardashas</h3><table><tr><th>Period</th><th>From</th><th>To</th></tr>${adRows}</table>` : ""}
    </div>
    <h2 class="sec">Life Timeline — Past · Present · Future</h2>
    <div class="card"><div class="timeline">${tlHTML}</div><p class="hint">${tl.note}</p></div>
    <h2 class="sec">Reading</h2>
    <div class="card">
      ${d.report.summary.map(s => `<p>${s}</p>`).join("")}
      ${d.report.dasha_note ? `<p><b>${d.report.dasha_note}</b></p>` : ""}
      <details><summary><b>House-by-house placements</b></summary>
        ${d.report.placements.map(p => `<p>• ${p}</p>`).join("")}</details>
    </div>
    <h2 class="sec">Auspicious Name Syllable (Namakarana)</h2>
    <div class="card">
      <p>Janma nakshatra <b>${nakName(c.moon_nakshatra.name)}</b> pada ${c.moon_nakshatra.pada}
        → name should begin with <span class="badge">${d.name_suggestions.syllable}</span></p>
      ${(d.name_suggestions.boy_names || []).length ? `<p><b>Boys:</b> ${d.name_suggestions.boy_names.join(", ")}</p>` : ""}
      ${(d.name_suggestions.girl_names || []).length ? `<p><b>Girls:</b> ${d.name_suggestions.girl_names.join(", ")}</p>` : ""}
    </div>
    <div id="ai-out"></div>`;
  out.scrollIntoView({behavior: "smooth"});
}

/* chart house click-through */
document.addEventListener("click", e => {
  const t = e.target.closest("circle[data-house]");
  if (!t || !LAST_KUNDLI) return;
  const h = +t.dataset.house;
  const info = $("#house-info");
  if (!info) return;
  const hd = (LAST_KUNDLI.houses || []).find(x => x.house === h) || {};
  const occ = (hd.occupants || []).map(p =>
    `<b>${plName(p)}</b> (${PLANET_NATURE[p]})`).join("; ");
  info.innerHTML = `<b>House ${h} — ${signName(hd.sign_name || "")}</b>: ${HOUSE_THEMES[h]}.<br>
    Lord: <b>${plName(hd.lord || "")}</b> sitting in house ${hd.lord_in_house}.
    ${occ ? "<br>Occupants: " + occ : "<br>No planets here — results flow from the lord's placement."}`;
});

/* ---------- saved profiles ---------- */
async function loadProfiles() {
  try {
    const list = await fetch("/api/profiles").then(r => r.json());
    const opts = `<option value="">— pick a saved profile —</option>` +
      list.map(p => `<option value='${JSON.stringify(p).replace(/'/g, "&#39;")}'>${p.name} (${p.date})</option>`).join("");
    const pick = $("#profile-picker");
    if (pick) pick.innerHTML = opts;
  } catch (e) { /* offline */ }
}
loadProfiles();

const pick = $("#profile-picker");
if (pick) pick.onchange = () => {
  if (!pick.value) return;
  const p = JSON.parse(pick.value);
  const f = $("#kundli-form");
  f.name.value = p.name; f.gender.value = p.gender || "any";
  f.date.value = p.date; f.time.value = p.time; f.place.value = p.place;
};

$("#btn-save-profile").onclick = async () => {
  const f = new FormData($("#kundli-form"));
  if (!f.get("name") || !f.get("date") || !f.get("place"))
    return alert("Fill name, date and place first.");
  await api("/api/profiles", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name: f.get("name"), gender: f.get("gender"),
      date: f.get("date"), time: f.get("time"), place: f.get("place")}),
  });
  await loadProfiles();
  alert("Profile saved ✔");
};

/* ---------- varshaphal ---------- */
$("#btn-varshaphal").onclick = async () => {
  const f = new FormData($("#kundli-form"));
  const year = +$("#vf-year").value || new Date().getFullYear();
  if (!f.get("date") || !f.get("place")) return alert("Fill the birth details first.");
  try {
    const d = await api("/api/varshaphal", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({year, birth: {name: f.get("name"),
        date: f.get("date"), time: f.get("time"), place: f.get("place")}}),
    });
    const target = $("#kundli-result");
    const box = document.createElement("div");
    box.innerHTML = `<h2 class="sec">🎂 Varshaphal ${d.year} — Year Chart</h2>
      <div class="card">
        ${chartSVG(d.chart, "east")}
        <p style="text-align:center">
          <span class="badge">Solar return: ${d.solar_return}</span>
          <span class="badge">Varsha lagna: ${signName(d.varsha_lagna)}</span>
          <span class="badge">Year lord: ${plName(d.year_lord)}</span></p>
        ${d.notes.map(n => `<p>✦ ${n}</p>`).join("")}
      </div>`;
    target.prepend(box);
    box.scrollIntoView({behavior: "smooth"});
  } catch (ex) { alert("Varshaphal failed: " + ex.message); }
};

$("#btn-pdf").onclick = async () => {
  const f = new FormData($("#kundli-form"));
  if (!f.get("date") || !f.get("place")) return alert("Fill the birth details first.");
  loading(true);
  try {
    const r = await fetch("/api/kundli/pdf", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name: f.get("name"), gender: f.get("gender"), date: f.get("date"),
        time: f.get("time"), place: f.get("place"),
      }),
    });
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    const blob = await r.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (f.get("name") || "kundli").replace(/\s+/g, "_") + "_report.pdf";
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (ex) { alert("PDF failed: " + ex.message); }
  finally { loading(false); }
};

$("#btn-ai").onclick = async () => {
  const f = new FormData($("#kundli-form"));
  if (!f.get("date") || !f.get("place")) return alert("Fill the birth details first.");
  try {
    const data = await api("/api/kundli/ai", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name: f.get("name"), gender: f.get("gender"), date: f.get("date"),
        time: f.get("time"), place: f.get("place"), language: LANG,
      }),
    });
    const box = $("#ai-out") || $("#kundli-result");
    box.innerHTML = `<h2 class="sec">AI Narrative</h2><div class="card">` +
      (data.ai ? `<div class="narrative">${data.narrative}</div>`
        : `<p>No AI key configured — showing classical passages the rule engine matched:</p>` +
          data.retrieved_passages.map(p => `<p>📜 ${p.text}</p>`).join("")) + `</div>`;
  } catch (ex) { err($("#ai-out") || $("#kundli-result"), ex.message); }
};

/* ---------- MATCH ---------- */
$("#match-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const mk = p => ({name: f.get(p + "_name"), date: f.get(p + "_date"),
                    time: f.get(p + "_time"), place: f.get(p + "_place")});
  try {
    const d = await api("/api/match", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({boy: mk("b"), girl: mk("g")}),
    });
    const a = d.ashtakoota;
    $("#match-result").innerHTML = `
      <div class="card">
        <div class="score-big">${a.total} / 36</div>
        <div class="verdict">${a.verdict}</div>
        <p style="text-align:center">
          <span class="badge">♂ ${d.partners.boy.name || "Boy"}: ${a.boy_rashi} · ${d.partners.boy.nakshatra.name}</span>
          <span class="badge">♀ ${d.partners.girl.name || "Girl"}: ${a.girl_rashi} · ${d.partners.girl.nakshatra.name}</span>
        </p>
        <table><tr><th>Koota</th><th>Score</th><th>Max</th><th>Detail</th></tr>
        ${a.kootas.map(k => `<tr><td><b>${k.name}</b><br><span class="hint">${k.meaning || ""}</span></td>
          <td>${k.score}</td><td>${k.max}</td><td>${k.detail}</td></tr>`).join("")}
        </table>
        <p>${a.nadi_dosha ? '<span class="badge red">Nadi Dosha</span>' : '<span class="badge green">No Nadi Dosha</span>'}
           ${a.bhakoot_dosha ? '<span class="badge red">Bhakoot Dosha</span>' : '<span class="badge green">No Bhakoot Dosha</span>'}
           <span class="badge ${d.partners.boy.mangal_dosha.manglik ? "red" : "green"}">♂ ${d.partners.boy.mangal_dosha.manglik ? "Manglik" : "Not Manglik"}</span>
           <span class="badge ${d.partners.girl.mangal_dosha.manglik ? "red" : "green"}">♀ ${d.partners.girl.mangal_dosha.manglik ? "Manglik" : "Not Manglik"}</span></p>
        <p class="hint">${a.mangal_note}</p>
      </div>`;
  } catch (ex) { err($("#match-result"), ex.message); }
};

/* ---------- MUHURTA ---------- */
$("#muhurta-form").onsubmit = async e => {
  e.preventDefault();
  const mf = new FormData(e.target);
  const f = new FormData($("#match-form"));
  if (!f.get("b_date") || !f.get("g_date") || !f.get("b_place") || !f.get("g_place"))
    return alert("Fill the Boy and Girl birth details above first.");
  const mk = p => ({name: f.get(p + "_name"), date: f.get(p + "_date"),
                    time: f.get(p + "_time"), place: f.get(p + "_place")});
  try {
    const d = await api("/api/muhurta", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({boy: mk("b"), girl: mk("g"),
        from_date: mf.get("from_date") || "", months: +mf.get("months"),
        venue: mf.get("venue") || ""}),
    });
    const rows = d.dates.map(r => `
      <div class="card">
        <p><b>📅 ${r.date} (${r.vaara})</b>
           <span class="badge ${r.score >= 5 ? "green" : ""}">score ${r.score}</span></p>
        <p><span class="badge">${r.nakshatra}</span>
           <span class="badge">${r.tithi}</span>
           <span class="badge">Yoga: ${r.yoga}</span>
           <span class="badge">Karana: ${r.karana}</span></p>
        ${r.cautions.length ? `<p class="hint">⚠ ${r.cautions.join("; ")}</p>` : ""}
        <p><b>Auspicious lagna windows (venue local time):</b></p>
        ${r.lagna_windows.map(w =>
          `<span class="badge green">${w.from}–${w.to} · ${signName(w.lagna)} — ${w.quality}</span>`).join(" ")
          || "<span class='hint'>no fixed/dual lagna clears the 8th-house rule this day</span>"}
      </div>`).join("");
    $("#muhurta-result").innerHTML = `
      <h2 class="sec">Marriage Muhurta — ${d.venue}</h2>
      <p class="hint card">♂ ${d.boy.rashi} / ${d.boy.nakshatra} · ♀ ${d.girl.rashi} / ${d.girl.nakshatra}
        · window: ${d.window}</p>
      ${rows || '<div class="err">No dates cleared all the classical filters in this window — widen the search.</div>'}
      <p class="hint card">${d.note}</p>`;
    $("#muhurta-result").scrollIntoView({behavior: "smooth"});
  } catch (ex) { err($("#muhurta-result"), ex.message); }
};

/* ---------- PANCHANGA ---------- */
$("#panchanga-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const d = await api(`/api/panchanga?date=${f.get("date")}&time=${f.get("time")}&place=${encodeURIComponent(f.get("place"))}`);
    LABELS = LABELS || d.odia_labels;
    const w = d.windows || {};
    const extra = w.sunrise ? `<div class="pancha-grid" style="margin-top:.6rem">
      <div class="cell"><div class="k">Sunrise</div><div class="v">${w.sunrise}</div></div>
      <div class="cell"><div class="k">Sunset</div><div class="v">${w.sunset}</div></div>
      <div class="cell"><div class="k">Rahu Kala ⛔</div><div class="v">${w.rahu_kala.from}–${w.rahu_kala.to}</div></div>
      <div class="cell"><div class="k">Gulika ⛔</div><div class="v">${w.gulika_kala.from}–${w.gulika_kala.to}</div></div>
      <div class="cell"><div class="k">Yamaganda ⛔</div><div class="v">${w.yamaganda.from}–${w.yamaganda.to}</div></div>
      <div class="cell"><div class="k">Abhijit ✅</div><div class="v">${w.abhijit.from}–${w.abhijit.to}</div></div>
      <div class="cell"><div class="k">Moon Rashi</div><div class="v">${signName(d.moon_rashi)}</div></div>
    </div>` : "";
    const nk = d.nakshatra_info ? `<p class="hint">🌙 <b>${nakName(d.panchanga.nakshatra.name)}</b>:
      deity ${d.nakshatra_info.deity}; symbol ${d.nakshatra_info.symbol}. ${d.nakshatra_info.traits}</p>` : "";
    $("#panchanga-result").innerHTML =
      `<h2 class="sec">Panchanga — ${d.place}</h2><div class="card">${panchaCard(d.panchanga)}${extra}${nk}</div>`;
  } catch (ex) { err($("#panchanga-result"), ex.message); }
};

/* ---------- DAY MUHURTA (trading etc.) ---------- */
$("#daymuhurta-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const body = {activity: f.get("activity"), date: f.get("date") || "",
                place: f.get("place"), scan_days: +f.get("scan_days")};
  if (f.get("b_date") && f.get("b_place"))
    body.birth = {date: f.get("b_date"), time: f.get("b_time") || "06:00",
                  place: f.get("b_place")};
  try {
    const d = await api("/api/daymuhurta", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    const w = d.windows, day = d.day;
    const horas = w.horas.map(h =>
      `<span class="badge ${h.quality === "good" ? "green" : h.quality === "avoid" ? "red" : ""}">
        ${h.from}–${h.to} ${plName(h.lord)}</span>`).join(" ");
    const best = (d.best_days || []).map(r => `<tr class="${r.date === day.date ? "current" : ""}">
      <td>${r.date}</td><td>${r.vaara}</td><td>${r.score}</td>
      <td>${r.nakshatra}</td><td>${r.tithi}</td>
      <td>${r.personal ? (r.personal.tara_ok && r.personal.chandra_ok ? "✅" : "⚠") : "—"}</td>
      <td>${r.cautions.join("; ")}</td></tr>`).join("");
    $("#daymuhurta-result").innerHTML = `
      <h2 class="sec">${d.activity} — ${d.place}</h2>
      <div class="card">
        <p><b>📅 ${day.date} (${day.vaara})</b>
          <span class="badge ${day.score >= 4 ? "green" : day.score < 1 ? "red" : ""}">day score ${day.score}</span>
          <span class="badge">${day.nakshatra}</span>
          <span class="badge">${day.tithi}</span>
          <span class="badge">Yoga: ${day.yoga}</span></p>
        ${day.cautions.length ? `<p class="hint">⚠ ${day.cautions.join("; ")}</p>` : ""}
        ${day.personal ? `<p><b>Personal:</b> ${day.personal.note}
          (tara ${day.personal.tara}${day.personal.tara_ok ? " ✅" : " ⚠"},
           Moon ${day.personal.chandra_position} from your rashi${day.personal.chandra_ok ? " ✅" : " ⚠"})</p>` : ""}
        <div class="pancha-grid">
          <div class="cell"><div class="k">Sunrise</div><div class="v">${w.sunrise}</div></div>
          <div class="cell"><div class="k">Sunset</div><div class="v">${w.sunset}</div></div>
          <div class="cell"><div class="k">Rahu Kala ⛔</div><div class="v">${w.rahu_kala.from}–${w.rahu_kala.to}</div></div>
          <div class="cell"><div class="k">Gulika Kala ⛔</div><div class="v">${w.gulika_kala.from}–${w.gulika_kala.to}</div></div>
          <div class="cell"><div class="k">Yamaganda ⛔</div><div class="v">${w.yamaganda.from}–${w.yamaganda.to}</div></div>
          <div class="cell"><div class="k">Abhijit ✅</div><div class="v">${w.abhijit.from}–${w.abhijit.to}</div></div>
        </div>
        <p><b>Planetary horas (green = favourable for this activity):</b></p>
        <p>${horas}</p>
        <p class="hint">✦ ${d.tip}</p>
      </div>
      ${best ? `<h2 class="sec">Best Upcoming Days</h2>
        <div class="card" style="overflow-x:auto"><table>
        <tr><th>Date</th><th>Day</th><th>Score</th><th>Nakshatra</th><th>Tithi</th><th>Personal</th><th>Cautions</th></tr>
        ${best}</table></div>` : ""}`;
    $("#daymuhurta-result").scrollIntoView({behavior: "smooth"});
  } catch (ex) { err($("#daymuhurta-result"), ex.message); }
};

/* ---------- FESTIVALS ---------- */
$("#festivals-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const d = await api(`/api/festivals?year=${f.get("year")}&place=${encodeURIComponent(f.get("place"))}&ekadashi=${f.get("ekadashi") ? "true" : "false"}`);
    const months = {};
    d.festivals.forEach(x => {
      const m = x.date.slice(0, 7);
      (months[m] = months[m] || []).push(x);
    });
    const monthName = m => new Date(m + "-02").toLocaleString("en", {month: "long"});
    $("#festivals-result").innerHTML =
      `<h2 class="sec">Odia Parba Panji ${d.year} — ${d.place}</h2>` +
      Object.entries(months).map(([m, list]) => `
        <div class="card"><h3 style="margin:.2rem 0;color:var(--maroon)">${monthName(m)} ${m.slice(0, 4)}</h3>
        ${list.map(x => `<p><b>${x.date.slice(8)} ${monthName(m).slice(0, 3)}</b> —
          <span class="badge ${x.type === "ekadashi" ? "" : "green"}">${x.name}</span>
          <span class="hint">${x.note}</span></p>`).join("")}</div>`).join("");
    $("#festivals-result").scrollIntoView({behavior: "smooth"});
  } catch (ex) { err($("#festivals-result"), ex.message); }
};

/* ---------- CHAT ASTROLOGER ---------- */
let CHAT_HISTORY = [];
function chatBubble(role, text) {
  const div = document.createElement("div");
  div.style.cssText = `margin:.4rem 0;padding:.6rem .8rem;border-radius:10px;white-space:pre-wrap;max-width:85%;` +
    (role === "user"
      ? "background:#f7ead0;margin-left:auto;text-align:right"
      : "background:#fff;border:1px solid var(--line)");
  div.textContent = text;
  $("#chat-messages").appendChild(div);
  $("#chat-messages").scrollTop = 1e9;
}

$("#btn-chat").onclick = async () => {
  const q = $("#chat-input").value.trim();
  if (!q) return;
  const f = new FormData($("#chat-birth"));
  if (!f.get("date") || !f.get("place"))
    return alert("Fill the birth details (DOB + place) first.");
  chatBubble("user", q);
  $("#chat-input").value = "";
  try {
    const d = await api("/api/chat", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question: q, history: CHAT_HISTORY, language: LANG,
        birth: {name: f.get("name"), date: f.get("date"),
                time: f.get("time"), place: f.get("place")},
      }),
    });
    chatBubble("assistant", d.answer);
    CHAT_HISTORY.push({role: "user", text: q},
                      {role: "assistant", text: d.answer});
    CHAT_HISTORY = CHAT_HISTORY.slice(-10);
  } catch (ex) { chatBubble("assistant", "⚠ " + ex.message); }
};
$("#chat-input").addEventListener("keydown", e => {
  if (e.key === "Enter") { e.preventDefault(); $("#btn-chat").click(); }
});

/* ---------- NAMES ---------- */
$("#names-form").onsubmit = async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const d = await api("/api/names", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({gender: f.get("gender"), date: f.get("date"),
                            time: f.get("time"), place: f.get("place")}),
    });
    const s = d.suggestions;
    $("#names-result").innerHTML = `<div class="card">
      <p>Janma Nakshatra: <b>${d.janma_nakshatra.name}</b> pada ${d.janma_nakshatra.pada} ·
         Rashi: <b>${d.rashi}</b></p>
      <p>Auspicious starting syllable: <span class="badge">${s.syllable}</span>
         (pada syllables: ${s.all_pada_syllables.join(", ")})</p>
      ${(s.boy_names || []).length ? `<p><b>Boy names:</b> ${s.boy_names.join(", ")}</p>` : ""}
      ${(s.girl_names || []).length ? `<p><b>Girl names:</b> ${s.girl_names.join(", ")}</p>` : ""}
      <p><b>Lucky:</b> gem ${d.lucky.gem} · deity ${d.lucky.deity} · day ${d.lucky.day}</p>
      ${d.nakshatra_info ? `<p>🌙 <b>${d.janma_nakshatra.name}</b>: deity ${d.nakshatra_info.deity};
        symbol ${d.nakshatra_info.symbol}. <i>${d.nakshatra_info.traits}</i></p>` : ""}
      <p class="hint">${s.note}</p></div>`;
  } catch (ex) { err($("#names-result"), ex.message); }
};

/* ---------- PALM ---------- */
let camStream = null, palmB64 = null;

$("#btn-cam-start").onclick = async () => {
  try {
    camStream = await navigator.mediaDevices.getUserMedia({
      video: {facingMode: "environment", width: {ideal: 1280}}, audio: false});
    const v = $("#cam");
    v.srcObject = camStream; v.classList.add("on");
    $("#palm-preview").hidden = true;
    $("#btn-cam-shot").hidden = false;
    $("#btn-cam-start").hidden = true;
  } catch (ex) { alert("Camera unavailable: " + ex.message + "\nYou can upload a photo instead."); }
};

$("#btn-cam-shot").onclick = () => {
  const v = $("#cam"), cv = $("#cam-canvas");
  cv.width = v.videoWidth; cv.height = v.videoHeight;
  cv.getContext("2d").drawImage(v, 0, 0);
  finishCapture(cv.toDataURL("image/jpeg", 0.85));
};

$("#palm-file").onchange = e => {
  const file = e.target.files[0];
  if (!file) return;
  const rd = new FileReader();
  rd.onload = () => finishCapture(rd.result);
  rd.readAsDataURL(file);
};

function finishCapture(dataUrl) {
  palmB64 = dataUrl;
  if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; }
  $("#cam").classList.remove("on");
  const img = $("#palm-preview");
  img.src = dataUrl; img.hidden = false;
  $("#btn-cam-shot").hidden = true;
  $("#btn-cam-retake").hidden = false;
  $("#btn-palm-send").hidden = false;
  $("#btn-cam-start").hidden = true;
}

$("#btn-cam-retake").onclick = () => {
  palmB64 = null;
  $("#palm-preview").hidden = true;
  $("#btn-cam-retake").hidden = true;
  $("#btn-palm-send").hidden = true;
  $("#btn-cam-start").hidden = false;
  $("#btn-cam-start").click();
};

$("#btn-palm-send").onclick = async () => {
  if (!palmB64) return;
  try {
    const d = await api("/api/palm/image", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image_base64: palmB64, language: LANG}),
    });
    $("#palm-result").innerHTML = `<h2 class="sec">Palm Reading</h2><div class="card">` +
      (d.ai ? `<div class="narrative">${d.narrative}</div>`
            : `<p>${d.message}</p><p class="hint">Scroll down and use the guided reading — it is free and instant.</p>`) +
      `</div>`;
    $("#palm-result").scrollIntoView({behavior: "smooth"});
  } catch (ex) { err($("#palm-result"), ex.message); }
};

/* guided questionnaire */
async function loadPalmQuestions() {
  const d = await fetch("/api/palm/questions").then(r => r.json());
  $("#palm-questions").innerHTML = d.questions.map(q => `
    <div class="q-block" data-id="${q.id}"><p>${q.q}</p>
      ${Object.entries(q.options).map(([val, txt]) =>
        `<label><input type="radio" name="q_${q.id}" value="${val}"> ${txt}</label>`).join("")}
    </div>`).join("");
}
loadPalmQuestions();

$("#btn-palm-guided").onclick = async () => {
  const answers = {};
  $$("#palm-questions .q-block").forEach(b => {
    const sel = b.querySelector("input:checked");
    if (sel) answers[b.dataset.id] = sel.value;
  });
  if (!Object.keys(answers).length) return alert("Answer at least one question.");
  try {
    const d = await api("/api/palm/guided", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({answers}),
    });
    $("#palm-result").innerHTML = `<h2 class="sec">Guided Palm Reading</h2>
      <div class="card">${d.reading.map(p => `<p>🖐 ${p}</p>`).join("")}</div>`;
    $("#palm-result").scrollIntoView({behavior: "smooth"});
  } catch (ex) { err($("#palm-result"), ex.message); }
};

/* default today's date in panchanga & muhurta forms */
const today = new Date().toISOString().slice(0, 10);
const pd = $('#panchanga-form input[name="date"]'); if (pd) pd.value = today;
const dm = $('#daymuhurta-form input[name="date"]'); if (dm) dm.value = today;
const fy = $('#festivals-form input[name="year"]'); if (fy) fy.value = new Date().getFullYear();
const vy = $("#vf-year"); if (vy) vy.value = new Date().getFullYear();

/* ---------- PWA ---------- */
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
/* preload labels for language toggle */
fetch("/api/health").catch(() => {});
