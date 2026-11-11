// Annotation Explorer: reads data/papers.json (built by pipeline/build_index.py)
// and renders the ranked list, the enhanced abstract and the workflow view.

const TIER_COLORS = {
  preferred: "var(--tier-preferred)",
  caution: "var(--tier-caution)",
  later: "var(--tier-later)",
  exclude: "var(--tier-exclude)",
};
const INVOLVEMENT = {
  core: "Core contribution",
  used: "Used",
  mentioned: "Mentioned",
  none: "Not addressed",
  unknown: "Unknown (not in sources read)",
};
const RULES = {
  1: "Rule 1 · scope",
  2: "Rule 2 · too specific",
  3: "Rule 3 · algorithm",
  4: "Rule 4 · defines markers",
  5: "Rule 5 · general",
};

// Diagram layout (viewBox 760 x 300), modeled on the mockup's workflow figure.
const NODE_W = 150, NODE_H = 54;
const LAYOUT = {
  sequencing: [15, 22],
  quantification: [205, 22],
  preprocessing: [395, 22],
  dimensionality_reduction: [595, 22],
  batch_correction: [595, 128],
  clustering: [395, 128],
  annotation: [205, 128],
  trajectory: [95, 230],
  cell_communication: [315, 230],
};
const EDGES = [
  ["sequencing", "quantification"],
  ["quantification", "preprocessing"],
  ["preprocessing", "dimensionality_reduction"],
  ["dimensionality_reduction", "batch_correction"],
  ["batch_correction", "clustering"],
  ["dimensionality_reduction", "clustering"],
  ["clustering", "annotation"],
  ["annotation", "trajectory"],
  ["annotation", "cell_communication"],
];

// How a tool/method's popularity is counted in the "All ingested papers" view.
// Each use is classed per paper as proposed / used / compared / mentioned.
const METRICS = {
  using: { label: "Papers using it", hint: "used or proposed", classes: ["used", "proposed"] },
  baseline: { label: "Used as a baseline", hint: "compared against", classes: ["compared"] },
  proposed: { label: "Proposed here", hint: "the paper's own method", classes: ["proposed"] },
  cited: { label: "Citation-weighted", hint: "sum of citation scores of papers using it", classes: ["used", "proposed"], weighted: true },
};
const CLASS_LABELS = { proposed: "Proposed", used: "Used", compared: "Baseline", mentioned: "Mentioned" };

const state = {
  data: null, tier: "all", query: "", ingestedOnly: false, selected: null, stage: null,
  view: "paper",          // bottom panel: "paper" or "all"
  metric: "using",
  usageTier: "all",       // "all" or "preferred" for the aggregate counts
  tool: null,             // {kind, name} open in the tool card
  toolFilter: null,       // {name, ids:Set} filtering the left list
};
const byId = {};

// --- small DOM helpers --------------------------------------------------------
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}
function svg(tag, attrs = {}, ...children) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) el.setAttribute(k, v);
  for (const c of children.flat()) if (c != null) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const fmt = (n) => (n == null ? "—" : n.toLocaleString());
const link = (label, url) => h("a", { href: url, target: "_blank", rel: "noopener" }, label);

// --- data ---------------------------------------------------------------------
async function load() {
  try {
    const res = await fetch("data/papers.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    state.data = await res.json();
  } catch (e) {
    document.getElementById("abstract").replaceChildren(
      h("div", { class: "notice warn" },
        "Couldn't load data/papers.json. Serve this folder over HTTP (browsers block fetch() from file://), e.g. ",
        h("code", {}, "python -m http.server 8765 --directory web"),
        ", and run ", h("code", {}, "python pipeline/build_index.py"), " first."));
    return;
  }
  const fromHash = decodeURIComponent(location.hash.slice(1));
  const papers = state.data.papers;
  for (const p of papers) byId[p.id] = p;
  state.selected = papers.find((p) => p.id === fromHash) || papers.find((p) => p.ingest) || papers[0];
  renderStats();
  renderFilters();
  renderLegend();
  renderList();
  document.querySelector(`.paper[data-id="${CSS.escape(state.selected.id)}"]`)?.scrollIntoView({ block: "center" });
  renderSelected();
}

function visiblePapers() {
  const q = state.query.trim().toLowerCase();
  return state.data.papers.filter((p) => {
    if (state.tier !== "all" && p.tier !== state.tier) return false;
    if (state.ingestedOnly && !p.ingest) return false;
    if (state.toolFilter && !state.toolFilter.ids.has(p.id)) return false;
    if (!q) return true;
    const tools = p.ingest ? (p.ingest.tools || []).map((t) => t.name).join(" ") : "";
    return `${p.title} ${p.first_author} ${p.journal} ${p.category} ${p.focus} ${tools}`.toLowerCase().includes(q);
  });
}

// --- header and filters -------------------------------------------------------
function renderStats() {
  const ps = state.data.papers;
  const ingested = ps.filter((p) => p.ingest).length;
  const preferred = ps.filter((p) => p.tier === "preferred").length;
  document.getElementById("stats").replaceChildren(
    h("div", {}, h("b", {}, ps.length), "papers ranked"),
    h("div", {}, h("b", {}, preferred), "preferred"),
    h("div", {}, h("b", {}, ingested), "ingested by agent"),
    h("div", {}, h("b", {}, state.data.generated), "index built"),
  );
}

function renderFilters() {
  const wrap = document.getElementById("tier-filter");
  const opts = [{ key: "all", label: "All" }, ...state.data.tiers];
  wrap.replaceChildren(...opts.map((t) => {
    const n = t.key === "all" ? state.data.papers.length : state.data.papers.filter((p) => p.tier === t.key).length;
    return h("button", {
      class: "chip", "aria-pressed": String(state.tier === t.key),
      onclick: () => { state.tier = t.key; renderFilters(); renderList(); },
    }, `${t.label} (${n})`);
  }));
}

function renderLegend() {
  const el = document.getElementById("legend");
  if (state.view === "all") {
    el.replaceChildren(h("span", { class: "coverage-legend" }, "Fewer papers cover this step",
      h("i", { class: "ramp" }), "More papers"));
    return;
  }
  el.replaceChildren(
    ...Object.entries(INVOLVEMENT).map(([k, label]) =>
      h("span", {}, h("i", { style: `background: var(--inv-${k});${k === "mentioned" ? "border-style:dashed;" : ""}` }), label.split(" (")[0])));
}

function renderViewToggle() {
  const n = state.data.papers.filter((p) => p.ingest).length;
  const opt = (key, label) => h("button", {
    "aria-pressed": String(state.view === key),
    onclick: () => { state.view = key; state.tool = null; renderWorkflow(); },
  }, label);
  document.getElementById("view-toggle").replaceChildren(opt("paper", "This paper"), opt("all", `All ingested papers (${n})`));
  document.getElementById("workflow-title").textContent =
    state.view === "all" ? "Most-used tools and methods per workflow step" : "Where it fits in the scRNA-seq workflow";
}

function renderActiveFilter() {
  const el = document.getElementById("active-filter");
  if (!state.toolFilter) { el.replaceChildren(); return; }
  el.replaceChildren(h("span", { class: "filter-chip" },
    `Using ${state.toolFilter.name} (${state.toolFilter.ids.size})`,
    h("button", {
      "aria-label": "Clear tool filter", title: "Clear filter",
      onclick: () => { state.toolFilter = null; renderList(); },
    }, "×")));
}

// --- left: ranked list --------------------------------------------------------
function renderList() {
  renderActiveFilter();
  const list = document.getElementById("paper-list");
  const papers = visiblePapers();
  if (!papers.length) {
    list.replaceChildren(h("li", { class: "empty" }, "No papers match these filters."));
    return;
  }
  const items = [];
  let tier = null;
  for (const p of papers) {
    if (p.tier !== tier) {
      tier = p.tier;
      const label = state.data.tiers.find((t) => t.key === tier).label;
      const count = papers.filter((x) => x.tier === tier).length;
      items.push(h("li", { class: "tier-heading", role: "presentation" },
        h("span", {}, h("span", { class: "dot", style: `background:${TIER_COLORS[tier]}` }), label),
        h("span", {}, count)));
    }
    items.push(h("li", {
      class: "paper", role: "option", tabindex: "0", "data-id": p.id,
      "aria-selected": String(state.selected && state.selected.id === p.id),
      onclick: () => select(p),
      onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(p); } },
    },
      h("div", { class: "rank" }, `#${p.rank}`),
      h("div", {},
        h("div", { class: "title", title: p.title }, p.title),
        h("div", { class: "meta" },
          h("span", {}, `${p.first_author} ${p.year}`),
          h("span", {}, `${fmt(p.citations)} cites`),
          p.ingest ? h("span", { class: "badge-ingested" }, "● ingested") : h("span", { class: "badge-pending" }, "○ pending")))));
  }
  list.replaceChildren(...items);
}

function select(p) {
  state.selected = p;
  if (state.view === "paper") state.stage = null;
  history.replaceState(null, "", `#${encodeURIComponent(p.id)}`);
  document.querySelectorAll(".paper").forEach((el) => el.setAttribute("aria-selected", String(el.dataset.id === p.id)));
  document.querySelector(`.paper[data-id="${CSS.escape(p.id)}"]`)?.scrollIntoView({ block: "nearest" });
  renderSelected();
}

// Arrow keys move through the visible list.
document.addEventListener("keydown", (e) => {
  if (!state.data || !["ArrowDown", "ArrowUp"].includes(e.key)) return;
  if (e.target.matches("input")) return;
  const papers = visiblePapers();
  const i = papers.findIndex((p) => p.id === state.selected.id);
  const next = papers[Math.max(0, Math.min(papers.length - 1, i + (e.key === "ArrowDown" ? 1 : -1)))];
  if (next && next !== state.selected) {
    e.preventDefault();
    select(next);
    document.querySelector(`.paper[data-id="${CSS.escape(next.id)}"]`)?.scrollIntoView({ block: "nearest" });
  }
});

// --- right top: enhanced abstract ---------------------------------------------
function renderSelected() {
  renderAbstract(state.selected);
  const ing = state.selected.ingest;
  if (ing && !state.stage) {
    const order = ["core", "used", "mentioned"];
    const firstCore = order.map((k) => Object.keys(LAYOUT).find((s) => ing.workflow[s].involvement === k)).find(Boolean);
    state.stage = firstCore || "annotation";
  }
  renderWorkflow();
}

function renderWorkflow() {
  if (!state.stage) state.stage = "annotation";
  renderViewToggle();
  renderLegend();
  renderDiagram();
  if (state.view === "all") renderUsageDetail();
  else renderStageDetail();
}

function renderAbstract(p) {
  const ing = p.ingest;
  const tierLabel = state.data.tiers.find((t) => t.key === p.tier).label;
  const main = h("div", { class: "abstract-main" },
    h("h2", {}, p.title),
    h("div", { class: "byline" }, `${p.first_author} et al. · ${p.journal || "—"} · ${p.year}`),
    h("div", { class: "tags" },
      h("span", { class: "tag tier", style: `background:${TIER_COLORS[p.tier]}` }, `${tierLabel} · #${p.tier_rank} in tier`),
      h("span", { class: "tag" }, RULES[p.rule] || `Rule ${p.rule}`),
      h("span", { class: "tag" }, `${p.category.replace(/_/g, " ")} · ${p.focus.replace(/_/g, " ")}`),
      p.recent && h("span", { class: "tag" }, "recent"),
      p.markers_defined && h("span", { class: "tag" }, "defines markers")),
  );

  if (ing) {
    const ea = ing.enhanced_abstract;
    main.append(
      h("div", { class: "tldr" }, h("strong", {}, "In one line"), ea.tldr),
      ...ea.sections.map((s) => h("div", { class: "section" }, h("h3", {}, s.heading), h("p", {}, s.body))),
    );
    if ((ea.key_findings || []).length || (ea.limitations || []).length) {
      main.append(h("div", { class: "twocol" },
        h("div", {}, h("h3", {}, "Key findings"), h("ul", {}, (ea.key_findings || []).map((x) => h("li", {}, x)))),
        h("div", {}, h("h3", {}, "Limitations"), h("ul", {}, (ea.limitations || []).map((x) => h("li", {}, x))))));
    }
    main.append(h("div", { class: "why" }, h("h3", {}, "Why it matters for this project"), h("p", {}, ea.why_it_matters)));
    if ((ing.cell_types || []).length) main.append(markerTable(ing.cell_types));
    main.append(h("div", { class: "provenance" },
      `Ingested ${ing.ingestion.date} by ${ing.ingestion.agent} from: `,
      ing.ingestion.sources.map((s, i) => [i ? ", " : "", link(s.label, s.url)]),
      ing.ingestion.notes ? ` — ${ing.ingestion.notes}` : ""));
  } else {
    main.append(
      h("div", { class: "notice" },
        h("p", { style: "margin:0 0 6px" }, h("b", {}, "Not ingested yet. "), "This paper is ranked, but the agent hasn't read it, so there's no enhanced abstract or workflow mapping."),
        h("p", { style: "margin:0 0 6px" }, "Screening note: ", p.reason),
        h("p", { style: "margin:0" }, "To ingest: ", h("code", {}, `python pipeline/fetch_sources.py ${p.id}`),
          ", have the agent write ", h("code", {}, `ingested/${p.id}.json`), " (see AGENT_INGEST.md), then ",
          h("code", {}, "python pipeline/build_index.py"), ".")),
      h("div", { class: "why" }, h("h3", {}, "Why it was listed"), h("p", {}, p.why_listed)));
  }

  document.getElementById("abstract").replaceChildren(main, renderAside(p));
  document.querySelector(".panel-top").scrollTop = 0;
}

function markerTable(cellTypes) {
  const genes = (list, cls) => (list || []).map((g, i) => [i ? ", " : "", h("span", { class: `gene ${cls}` }, g)]);
  return h("details", { class: "markers", open: true },
    h("summary", {}, `Marker definitions from this paper (${cellTypes.length})`),
    h("table", {},
      h("thead", {}, h("tr", {}, h("th", {}, "Cell type"), h("th", {}, "Positive"), h("th", {}, "Negative"), h("th", {}, "Context"))),
      h("tbody", {}, cellTypes.map((c) => h("tr", {},
        h("td", {}, c.name), h("td", {}, genes(c.positive_markers, "pos")),
        h("td", {}, genes(c.negative_markers, "neg")), h("td", {}, c.context || ""))))));
}

function renderAside(p) {
  const ing = p.ingest;
  const links = [];
  if (p.free_url) links.push(h("li", {}, link(`Free full text (${p.access_route || "open"})`, p.free_url)));
  links.push(h("li", {}, link(`DOI: ${p.doi}`, `https://doi.org/${p.doi}`)));
  if (p.pmid) links.push(h("li", {}, link(`PubMed ${p.pmid}`, `https://pubmed.ncbi.nlm.nih.gov/${p.pmid}/`)));
  if (p.openalex_id) links.push(h("li", {}, link("OpenAlex record", p.openalex_id)));
  const groups = [];
  if (ing) {
    for (const [key, label] of [["code", "Code"], ["datasets", "Datasets"], ["other", "Other"]]) {
      const items = ing.links[key] || [];
      if (items.length) groups.push(h("div", { class: "group" }, label), h("ul", {}, items.map((l) => h("li", {}, link(l.label, l.url)))));
    }
  }

  const citeBox = h("div", { class: "box" },
    h("h3", {}, "Citations"),
    h("div", { class: "citebig" }, fmt(p.citations)),
    h("div", { class: "citesub" },
      `${p.citations_per_year ?? "—"} per year · OpenAlex, ${p.citations_retrieved || "n/a"}`),
    p.citation_history.length ? h("div", { class: "chart" }, citationChart(p.citation_history)) : null);

  const s = p.scores;
  const meter = (v) => h("div", { class: "meter" }, h("span", { style: `width:${Math.round(v * 100)}%` }));
  const rankBox = h("div", { class: "box" },
    h("h3", {}, "Ranking"),
    h("div", { class: "citesub", style: "margin-bottom:6px" },
      `#${p.rank} overall · tier first, then recency and citations`),
    h("div", { class: "scores" },
      "Recency", meter(s.recency), s.recency.toFixed(2),
      "Citations", meter(s.citations), s.citations.toFixed(2),
      "Within tier", meter(s.within_tier), s.within_tier.toFixed(2)));

  return h("div", { class: "aside" },
    h("div", { class: "box" }, h("h3", {}, "Links"), h("ul", {}, links), groups),
    citeBox, rankBox);
}

function citationChart(history) {
  const W = 250, H = 80, pad = 14;
  const max = Math.max(...history.map((d) => d.count), 1);
  const bw = (W - 4) / history.length;
  const g = svg("svg", { viewBox: `0 0 ${W} ${H + pad}`, role: "img", "aria-label": "Citations per year" });
  history.forEach((d, i) => {
    const bh = Math.max(1, (d.count / max) * (H - 12));
    const x = 2 + i * bw;
    g.append(svg("rect", { class: "bar", x: x + 1, y: H - bh, width: Math.max(2, bw - 3), height: bh, rx: 2 },
      svg("title", {}, `${d.year}: ${d.count} citations`)));
    if (history.length <= 8 || i % 2 === 0 || i === history.length - 1) {
      g.append(svg("text", { class: "lbl", x: x + bw / 2, y: H + 11, "text-anchor": "middle" }, `'${String(d.year).slice(2)}`));
    }
  });
  return g;
}

// --- right bottom: workflow diagram -------------------------------------------
function renderDiagram() {
  const root = document.getElementById("diagram");
  const p = state.selected;
  const wf = p.ingest ? p.ingest.workflow : null;
  const defs = svg("defs", {},
    svg("marker", { id: "arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" },
      svg("path", { class: "arrowhead", d: "M0,0 L10,5 L0,10 z" })));
  const edges = EDGES.map(([a, b]) => {
    const [ax, ay] = LAYOUT[a], [bx, by] = LAYOUT[b];
    const [x1, y1, x2, y2] = anchor(ax, ay, bx, by);
    return svg("line", { class: "edge", x1, y1, x2, y2, "marker-end": "url(#arrow)" });
  });
  const all = state.view === "all";
  const nodes = state.data.stages.map(({ key, label }) => {
    const [x, y] = LAYOUT[key];
    const lines = wrap(label, 18);
    let cls, sub, aria, style = null;
    if (all) {
      const cov = coverage(key);
      const share = cov.known ? cov.covered / cov.known : 0;
      const top = rankedItems(key, "tools")[0] || rankedItems(key, "methods")[0];
      cls = `agg${share > 0.55 ? " strong" : ""}`;
      style = `--share:${Math.round(share * 85)}%`;
      sub = `${cov.covered}/${cov.known} papers${top ? " · " + clip(top.name, 14) : ""}`;
      aria = `${label}: covered by ${cov.covered} of ${cov.known} papers`;
    } else {
      const inv = wf ? wf[key].involvement : "na";
      cls = inv;
      sub = wf ? INVOLVEMENT[inv].split(" (")[0] : "";
      aria = `${label}: ${wf ? INVOLVEMENT[inv] : "not ingested"}`;
    }
    const g = svg("g", {
      class: `node ${cls}${state.stage === key ? " sel" : ""}`, tabindex: "0", role: "button", "aria-label": aria, style,
    },
      svg("rect", { x, y, width: NODE_W, height: NODE_H, rx: 9 }),
      ...lines.map((ln, i) => svg("text", { x: x + NODE_W / 2, y: y + 22 + i * 14 - (lines.length - 1) * 6, "text-anchor": "middle" }, ln)),
      svg("text", { class: "inv", x: x + NODE_W / 2, y: y + NODE_H - 7, "text-anchor": "middle" }, sub));
    const pick = () => { state.stage = key; state.tool = null; renderWorkflow(); };
    g.addEventListener("click", pick);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
    return g;
  });
  root.replaceChildren(defs, ...edges, ...nodes);
}

// Start and end points on the rectangle edges facing each other.
function anchor(ax, ay, bx, by) {
  const acx = ax + NODE_W / 2, acy = ay + NODE_H / 2, bcx = bx + NODE_W / 2, bcy = by + NODE_H / 2;
  const clip = (cx, cy, dx, dy) => {
    const sx = dx ? (NODE_W / 2 + 3) / Math.abs(dx) : Infinity;
    const sy = dy ? (NODE_H / 2 + 3) / Math.abs(dy) : Infinity;
    const s = Math.min(sx, sy);
    return [cx + dx * s, cy + dy * s];
  };
  const dx = bcx - acx, dy = bcy - acy;
  const [x1, y1] = clip(acx, acy, dx, dy);
  const [x2, y2] = clip(bcx, bcy, -dx, -dy);
  return [x1, y1, x2, y2].map((v) => v.toFixed(1));
}

function wrap(text, max) {
  const words = text.split(" ");
  const lines = [""];
  for (const w of words) {
    const cur = lines[lines.length - 1];
    if ((cur + " " + w).trim().length > max && cur) lines.push(w);
    else lines[lines.length - 1] = (cur + " " + w).trim();
  }
  return lines.slice(0, 2);
}

function renderStageDetail() {
  const el = document.getElementById("stage-detail");
  const p = state.selected;
  const ing = p.ingest;
  if (!ing) {
    el.replaceChildren(h("h3", {}, "Workflow mapping not available"),
      h("p", { class: "hint" }, "The agent maps each paper onto these workflow steps when it ingests the paper. This one hasn't been ingested yet."));
    return;
  }
  const stage = state.data.stages.find((s) => s.key === state.stage);
  const st = ing.workflow[state.stage];
  // Pills open the cross-paper tool card when the name is in the usage data.
  const pill = (raw, kinds, extra, title) => {
    const target = resolveName(raw, kinds);
    return target
      ? h("button", { class: "pill linky", title: title || `See how often ${target.name} is used across papers`, onclick: () => openTool(target.kind, target.name) }, raw, extra)
      : h("span", { class: "pill", title: title || "" }, raw, extra);
  };
  const roleLabel = { proposed: "proposed", used: "used", compared: "compared" };
  el.replaceChildren(...[
    h("h3", {}, stage.label),
    h("span", { class: `inv-pill ${st.involvement}` }, INVOLVEMENT[st.involvement]),
    h("p", {}, st.summary),
    (st.methods || []).length ? [h("h4", {}, "Methods"), h("div", { class: "pills" }, st.methods.map((m) => pill(m, ["methods"])))] : null,
    (st.tools || []).length ? [h("h4", {}, "Tools at this step"), h("div", { class: "pills" }, st.tools.map((t) => pill(t, ["tools"])))] : null,
    (ing.algorithms || []).length ? [h("h4", {}, "Algorithms in this paper"),
      h("div", { class: "pills" }, ing.algorithms.map((a) =>
        pill(a.name, ["methods", "tools"], h("small", {}, roleLabel[a.role]), a.description)))] : null,
    (ing.tools || []).length ? [h("h4", {}, "Tools in this paper"),
      h("div", { class: "pills" }, ing.tools.map((t) =>
        pill(t.name, ["tools"], h("small", {}, [t.language, roleLabel[t.role]].filter(Boolean).join(" · ")))))] : null,
    h("p", { class: "hint", style: "margin-top:12px" }, "Click a step in the diagram to see how this paper relates to it, or a highlighted tool to see how widely it's used."),
  ].flat(Infinity).filter(Boolean));
}

// --- "All ingested papers" view: usage across papers ---------------------------
const clip = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

function inScope(id) {
  const p = byId[id];
  return p && p.ingest && (state.usageTier === "all" || p.tier === "preferred");
}

function coverage(stageKey) {
  const inv = Object.entries(state.data.usage[stageKey].involvement).filter(([id]) => inScope(id));
  const covered = inv.filter(([, v]) => v === "core" || v === "used").length;
  const unknown = inv.filter(([, v]) => v === "unknown").length;
  return { covered, unknown, known: inv.length - unknown, total: inv.length };
}

// Value of one tool/method bucket under the current metric and tier filter.
function metricValue(bucket) {
  const m = METRICS[state.metric];
  let v = 0;
  for (const u of bucket.uses) {
    if (!inScope(u.id) || !m.classes.includes(u.cls)) continue;
    v += m.weighted ? byId[u.id].scores.citations : 1;
  }
  return v;
}

function rankedItems(stageKey, kind) {
  return state.data.usage[stageKey][kind]
    .map((b) => ({ ...b, value: metricValue(b) }))
    .filter((b) => b.value > 0)
    .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name));
}

function resolveName(raw, kinds) {
  for (const kind of kinds) {
    const name = state.data.aliases[kind][raw] || raw;
    const found = Object.values(state.data.usage).some((st) => st[kind].some((b) => b.name === name));
    if (found) return { kind, name };
  }
  return null;
}

function openTool(kind, name) {
  state.view = "all";
  state.tool = { kind, name };
  renderWorkflow();
  document.querySelector(".panel-bottom").scrollIntoView({ block: "nearest" });
}

function usageControls() {
  const metricSel = h("select", {
    "aria-label": "Popularity measure",
    onchange: (e) => { state.metric = e.target.value; renderWorkflow(); },
  }, Object.entries(METRICS).map(([k, m]) => h("option", { value: k, selected: state.metric === k }, m.label)));
  const tierBox = h("label", { class: "toggle" },
    h("input", {
      type: "checkbox", checked: state.usageTier === "preferred",
      onchange: (e) => { state.usageTier = e.target.checked ? "preferred" : "all"; renderWorkflow(); },
    }), "Preferred tier only");
  return h("div", { class: "usage-controls" }, metricSel, tierBox);
}

function barList(stageKey, kind) {
  const items = rankedItems(stageKey, kind);
  if (!items.length) return h("p", { class: "hint" }, "None recorded for this step.");
  const max = items[0].value;
  const weighted = METRICS[state.metric].weighted;
  return h("ol", { class: "bars" }, items.slice(0, 12).map((b) => {
    const counts = {};
    for (const u of b.uses) if (inScope(u.id)) counts[u.cls] = (counts[u.cls] || 0) + 1;
    const breakdown = Object.entries(counts).map(([c, n]) => `${CLASS_LABELS[c]} ${n}`).join(" · ");
    return h("li", {},
      h("button", { class: "bar-row", title: breakdown, onclick: () => openTool(kind, b.name) },
        h("span", { class: "bar-name" }, b.name, b.unlisted ? h("small", { title: "Not in the vocabulary yet" }, " *") : null),
        h("span", { class: "bar-track" }, h("span", { class: "bar-fill", style: `width:${Math.max(4, (b.value / max) * 100)}%` })),
        h("span", { class: "bar-val" }, weighted ? b.value.toFixed(1) : b.value)));
  }));
}

function renderUsageDetail() {
  const el = document.getElementById("stage-detail");
  if (state.tool) { el.replaceChildren(...toolCard(state.tool)); return; }
  const stage = state.data.stages.find((s) => s.key === state.stage);
  const cov = coverage(state.stage);
  const n = state.data.papers.filter((p) => inScope(p.id)).length;
  el.replaceChildren(...[
    h("h3", {}, stage.label),
    h("p", { class: "cov" },
      `${cov.covered} of ${cov.known} papers perform this step`,
      cov.unknown ? ` (${cov.unknown} unknown, e.g. abstract-only)` : "", "."),
    usageControls(),
    h("h4", {}, "Tools"), barList(state.stage, "tools"),
    h("h4", {}, "Methods"), barList(state.stage, "methods"),
    h("p", { class: "hint", style: "margin-top:10px" },
      `n = ${n} ingested paper${n === 1 ? "" : "s"}${state.usageTier === "preferred" ? " (preferred tier)" : ""}. `,
      `${METRICS[state.metric].label}: ${METRICS[state.metric].hint}. Counts reflect this sample, which leans toward annotation-method papers. Click a bar for details.`),
  ].flat(Infinity).filter(Boolean));
}

function toolCard({ kind, name }) {
  const stageHits = [];
  const paperClasses = {};
  const versions = new Set();
  let meta = {};
  for (const s of state.data.stages) {
    const b = state.data.usage[s.key][kind].find((x) => x.name === name);
    if (!b) continue;
    meta = b;
    const uses = b.uses.filter((u) => inScope(u.id));
    if (!uses.length) continue;
    stageHits.push({ stage: s, uses });
    for (const u of uses) {
      (paperClasses[u.id] ||= new Set()).add(u.cls);
      u.versions.forEach((v) => versions.add(v));
    }
  }
  const ids = Object.keys(paperClasses).sort((a, b) => byId[a].rank - byId[b].rank);
  const back = h("button", { class: "linkbtn", onclick: () => { state.tool = null; renderWorkflow(); } },
    `← Back to ${state.data.stages.find((s) => s.key === state.stage).label}`);
  return [
    back,
    h("h3", {}, name),
    h("div", { class: "tags" },
      h("span", { class: "tag" }, kind === "tools" ? (meta.kind || "tool") : "method"),
      meta.language && h("span", { class: "tag" }, meta.language),
      versions.size && h("span", { class: "tag" }, `versions: ${[...versions].sort().join(", ")}`),
      meta.unlisted && h("span", { class: "tag" }, "not in vocabulary")),
    meta.url && h("p", {}, link(meta.url.replace(/^https?:\/\//, ""), meta.url)),
    h("p", { class: "cov" }, `Appears in ${ids.length} ingested paper${ids.length === 1 ? "" : "s"} across ${stageHits.length} step${stageHits.length === 1 ? "" : "s"}.`),
    h("h4", {}, "By workflow step"),
    h("div", { class: "pills" }, stageHits.map(({ stage, uses }) =>
      h("button", { class: "pill linky", onclick: () => { state.stage = stage.key; state.tool = null; renderWorkflow(); } },
        stage.label, h("small", {}, uses.length)))),
    h("h4", {}, "Papers"),
    h("ul", { class: "paper-mini" }, ids.map((id) => {
      const p = byId[id];
      return h("li", {},
        h("button", { class: "linkbtn", onclick: () => select(p) }, `#${p.rank} ${clip(p.title, 70)}`),
        h("small", {}, ` ${p.first_author} ${p.year} · ${[...paperClasses[id]].map((c) => CLASS_LABELS[c]).join(", ")}`));
    })),
    h("button", {
      class: "action", onclick: () => { state.toolFilter = { name, ids: new Set(ids) }; renderList(); },
    }, `Show only these ${ids.length} papers in the list`),
  ];
}

// --- wiring -------------------------------------------------------------------
document.getElementById("search").addEventListener("input", (e) => { state.query = e.target.value; renderList(); });
document.getElementById("ingested-only").addEventListener("change", (e) => { state.ingestedOnly = e.target.checked; renderList(); });
window.addEventListener("hashchange", () => {
  const p = state.data && state.data.papers.find((x) => x.id === decodeURIComponent(location.hash.slice(1)));
  if (p && p !== state.selected) select(p);
});

load();
