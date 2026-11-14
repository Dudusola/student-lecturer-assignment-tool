"use strict";
// All data lives in this page; the server only parses files, solves the assignment and builds exports.

const STRONG = 0.75, PARTIAL = 0.40;
const ROLES = {
  students: [["name", "Name"], ["matric", "Matric no."], ["field", "Field", true]],
  lecturers: [["name", "Name"], ["field", "Specialization", true], ["capacity", "Max students", true]],
};
const state = { students: null, lecturers: null, result: null, focus: null };
const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, props = {}, ...kids) => {
  const n = Object.assign(document.createElement(tag), props);
  n.append(...kids.filter((k) => k != null && k !== false));
  return n;
};
const plural = (n, one, many = one + "s") => `${n} ${n === 1 ? one : many}`;
const pct = (s) => `${Math.round(s * 100)}%`;
const label = (score, hasFields) =>
  !hasFields || score == null ? "" : score >= STRONG ? "strong" : score >= PARTIAL ? "partial" : "weak";

$("#today").textContent = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

// ---------- the Python engine (Pyodide) ----------
// utils/ runs in the browser, so files are never uploaded. Downloads are cached after the first visit.
const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
const engineNote = (text, cls = "") => { const n = $("#engine"); n.textContent = text; n.className = "engine " + cls; };
const wheelUrls = async (pick) => {
  const all = await (await fetch("/wheels/index.json")).json();
  return all.filter(pick).map((w) => new URL(`/wheels/${w}`, location.href).href);
};
const engine = (async () => {
  engineNote("Getting the matcher ready… the first visit downloads about 20 MB.");
  const py = await loadPyodide({ indexURL: PYODIDE });
  await py.loadPackage(["numpy", "pandas", "lxml", "typing-extensions", "micropip"]);
  const urls = await wheelUrls((w) => !w.startsWith("reportlab"));
  await py.pyimport("micropip").install.callKwargs(py.toPy(urls), { deps: false });
  py.unpackArchive(await (await fetch("/py/utils.zip")).arrayBuffer(), "zip");
  engineNote("Ready. Your files stay on this computer.", "is-ready");
  return py;
})();
engine.catch(() => engineNote("The matcher couldn’t load. Check your connection and reload the page.", "is-error"));
// scipy (the solver) is fetched in the background as soon as the basics are in.
const solver = engine.then(async (py) => { await py.loadPackage("scipy"); return py; });
let printer = null;  // PDF support, fetched on the first PDF export
const exporter = () => (printer ??= engine.then(async (py) => {
  await py.loadPackage(["pillow", "charset-normalizer"]);
  await py.pyimport("micropip").install.callKwargs(py.toPy(await wheelUrls((w) => w.startsWith("reportlab"))), { deps: false });
  return py;
}));

async function pycall(ready, fn, ...args) {
  const py = await ready;
  const svc = py.pyimport("utils.service");
  const pyArgs = args.map((a) => (a == null ? a : py.toPy(a)));
  try {
    const out = svc[fn](...pyArgs);
    if (out == null || typeof out !== "object") return out;
    const js = out.toJs({ dict_converter: Object.fromEntries, create_pyproxies: false });
    out.destroy();
    return js;
  } catch (e) {
    const last = String(e.message || e).trim().split("\n").pop();
    const known = /^(?:\w+\.)*(?:DataError|ValueError): (.+)$/.exec(last);
    throw new Error(known ? known[1] : "Something went wrong. Check the file and try again.");
  } finally {
    pyArgs.forEach((a) => a?.destroy?.());
    svc.destroy();
  }
}

const MIME = {
  csv: "text/csv", pdf: "application/pdf",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};
function download(bytes, name, ext) {
  const url = URL.createObjectURL(new Blob([bytes], { type: MIME[ext] }));
  el("a", { href: url, download: name }).click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------- loading files ----------

function setTable(kind, table) {
  state[kind] = { ...table, map: { ...table.detected } };
  state.result = null;
  renderSlot(kind);
  renderRules();
}

async function loadFile(kind, file) {
  const slot = $(`.slot[data-kind="${kind}"]`);
  const drop = $(".drop", slot);
  $(".error", slot).textContent = "";
  if (file.size > 5 * 1024 * 1024) { $(".error", slot).textContent = "That file is over 5 MB."; return; }
  drop.classList.add("is-busy");
  try {
    setTable(kind, await pycall(engine, "read_upload", file.name, new Uint8Array(await file.arrayBuffer())));
    state[kind].fileName = file.name;
    renderSlot(kind);
  } catch (e) {
    $(".error", slot).textContent = e.message;
  } finally {
    drop.classList.remove("is-busy");
  }
}

for (const slot of document.querySelectorAll(".slot")) {
  const kind = slot.dataset.kind, drop = $(".drop", slot), input = $("input", drop);
  input.addEventListener("change", () => input.files[0] && loadFile(kind, input.files[0]));
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("is-over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("is-over"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault(); drop.classList.remove("is-over");
    if (e.dataTransfer.files[0]) loadFile(kind, e.dataTransfer.files[0]);
  });
  $(".change", slot).addEventListener("click", () => { input.value = ""; input.click(); });
}

$("#sample").addEventListener("click", async () => {
  try {
    const s = await pycall(engine, "sample");
    setTable("students", s.students); setTable("lecturers", s.lecturers);
    state.students.fileName = state.lecturers.fileName = "sample";
    renderSlot("students"); renderSlot("lecturers");
  } catch (e) { $("#rules-note").textContent = e.message; }
});

// ---------- column mapping ----------
function rows(kind) {
  const t = state[kind];
  if (!t) return null;
  const idx = (role) => (t.map[role] ? t.columns.indexOf(t.map[role]) : -1);
  const get = (r, role) => (idx(role) >= 0 ? String(r[idx(role)] ?? "").trim() : "");
  return t.rows.map((r) =>
    kind === "students"
      ? { name: get(r, "name"), matric: get(r, "matric"), field: get(r, "field") }
      : { name: get(r, "name"), field: get(r, "field"), capacity: parseCap(get(r, "capacity")) }
  ).filter((p) => p.name);
}
const parseCap = (v) => { const n = Math.trunc(Number(v)); return Number.isFinite(n) && n > 0 && v !== "" ? Math.min(n, 2000) : null; };

function problems(kind) {
  const t = state[kind];
  if (!t) return [];
  const out = [];
  if (!t.map.name) out.push("Choose the name column.");
  if (kind === "students") {
    if (!t.map.matric) out.push("Choose the matric number column.");
    else if (t.map.matric === t.map.name) out.push("Name and matric number can’t be the same column.");
    else {
      const list = rows(kind), seen = new Set(), dups = new Set();
      for (const s of list) { if (!s.matric) { out.push(`${plural(list.filter((x) => !x.matric).length, "student")} without a matric number.`); break; } }
      for (const s of list) { if (s.matric && seen.has(s.matric)) dups.add(s.matric); seen.add(s.matric); }
      if (dups.size) out.push(`Duplicate matric numbers: ${[...dups].slice(0, 4).join(", ")}${dups.size > 4 ? "…" : ""}`);
    }
  } else {
    const seen = new Set(), dups = new Set();
    for (const l of rows(kind)) { if (seen.has(l.name)) dups.add(l.name); seen.add(l.name); }
    if (dups.size) out.push(`Duplicate lecturer names: ${[...dups].slice(0, 4).join(", ")}`);
  }
  return out;
}

function renderSlot(kind) {
  const slot = $(`.slot[data-kind="${kind}"]`), t = state[kind];
  $(".drop", slot).hidden = !!t;
  $(".loaded", slot).hidden = !t;
  if (!t) return;
  const list = rows(kind);
  const fields = new Set(list.map((p) => p.field.toLowerCase()).filter(Boolean)).size;
  const count = $(".loaded-count", slot);
  count.replaceChildren(
    kind === "students" ? plural(list.length, "student") : plural(list.length, "lecturer"),
    el("small", { textContent: [t.fileName === "sample" ? "Sample list" : t.fileName, fields ? plural(fields, kind === "students" ? "field" : "specialization") : "no field column"].filter(Boolean).join(" · ") })
  );
  const map = $(".map", slot);
  map.replaceChildren(...ROLES[kind].map(([role, text, optional]) => {
    const sel = el("select", { name: role },
      ...(optional ? [el("option", { value: "", textContent: "None" })] : []),
      ...t.columns.map((c) => el("option", { value: c, textContent: c, selected: t.map[role] === c })));
    if (!optional && !t.map[role]) sel.prepend(el("option", { value: "", textContent: "Choose…", selected: true, disabled: true }));
    sel.addEventListener("change", () => { t.map[role] = sel.value || null; state.result = null; renderSlot(kind); renderRules(); });
    return el("label", {}, text, sel);
  }));
  $(".error", slot).textContent = problems(kind).join(" ");
}

// ---------- rules ----------
const form = $("#rules");
const settings = () => {
  const fd = new FormData(form);
  return { mode: fd.get("mode"), global_max: parseCap(fd.get("global_max")), min_score: Number(fd.get("min_score")) / 100 };
};

function capacities(lecturers, n, globalMax) {
  const fair = Math.ceil(n / Math.max(lecturers.length, 1));
  return lecturers.map((l) => l.capacity || globalMax || fair);
}

function renderRules() {
  const s = settings(), note = $("#rules-note"), btn = $(".publish", form);
  $("#min-out").textContent = pct(s.min_score);
  $("#min-row input").disabled = s.mode !== "smart";
  note.classList.remove("is-warning");
  const st = rows("students"), lt = rows("lecturers");
  const ready = st && lt && st.length && lt.length && !problems("students").length && !problems("lecturers").length;
  btn.disabled = !ready;
  if (!st || !lt) { note.textContent = `Add the ${!st && !lt ? "two lists" : !st ? "student list" : "lecturer list"} to publish.`; return; }
  if (!ready) { note.textContent = "Fix the highlighted list first."; note.classList.add("is-warning"); return; }
  const places = capacities(lt, st.length, s.global_max).reduce((a, b) => a + b, 0);
  if (places < st.length) {
    note.textContent = `Limits add up to ${places} places for ${st.length} students; ${st.length - places} will be left unplaced.`;
    note.classList.add("is-warning");
  } else {
    note.textContent = `${plural(st.length, "student")} into ${plural(places, "place")} across ${plural(lt.length, "lecturer")}.`;
  }
}
form.addEventListener("input", renderRules);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $(".publish", form), note = $("#rules-note");
  const students = rows("students"), lecturers = rows("lecturers"), s = settings();
  btn.disabled = true; btn.setAttribute("aria-busy", "true"); btn.textContent = "Setting the list…";
  try {
    const r = await pycall(solver, "run_assign", students, lecturers, s.mode, s.global_max, s.min_score);
    state.result = {
      ...r, students, lecturers,
      names: lecturers.map((l) => l.name),
      current: r.assignments.map((a) => (a ? lecturers.findIndex((l) => l.name === a) : -1)),
      original: r.assignments.map((a) => (a ? lecturers.findIndex((l) => l.name === a) : -1)),
    };
    state.focus = null;
    renderList(true);
    $("#paper").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  } catch (err) {
    note.textContent = err.message; note.classList.add("is-warning");
  } finally {
    btn.removeAttribute("aria-busy"); btn.textContent = "Publish the list"; btn.disabled = false;
  }
});

// ---------- the list ----------
function scoreOf(i, j) { const r = state.result; return j >= 0 && r.has_fields ? r.scores[i][j] : null; }

function renderList(fresh = false) {
  const r = state.result;
  $("#notice").hidden = !!r;
  $("#paper").hidden = !r;
  $("#press").hidden = !r;
  document.body.classList.toggle("has-list", !!r);
  if (!r) return;

  const groups = r.names.map(() => []), unplaced = [];
  r.current.forEach((j, i) => (j >= 0 ? groups[j] : unplaced).push(i));
  const caps = r.names.map((n) => r.caps[n]);
  const maxCap = Math.max(...caps, ...groups.map((g) => g.length));
  const counts = { strong: 0, partial: 0, weak: 0 };
  r.current.forEach((j, i) => { const l = j >= 0 && label(scoreOf(i, j), r.has_fields); if (l) counts[l]++; });
  const placed = r.current.length - unplaced.length;

  const order = r.names.map((_, j) => j).sort((a, b) => r.names[a].localeCompare(r.names[b]));
  const columns = $("#columns");
  columns.classList.toggle("has-focus", state.focus != null);
  columns.classList.toggle("is-fresh", fresh);  // the entrance plays once, on publish
  columns.replaceChildren(
    ...order.map((j, k) => lecturerColumn(j, groups[j], caps[j], maxCap, k)),
    ...(unplaced.length ? [unplacedColumn(unplaced, order.length)] : [])
  );

  const fieldLine = r.has_fields
    ? ` ${plural(counts.strong, "strong match", "strong matches")}, ${counts.partial} partial, ${counts.weak ? `${counts.weak} weak (circled)` : "none weak"}.`
    : " No field columns, so students were spread evenly.";
  $("#summary").textContent = `${plural(placed, "student")} placed with ${plural(r.names.length, "lecturer")}${unplaced.length ? `, ${unplaced.length} not placed` : ""}.${fieldLine}`;
  $("#press-counts").innerHTML = "";
  $("#press-counts").append(
    el("b", { textContent: placed }), ` of ${r.current.length} placed`,
    ...(r.has_fields ? [" · ", el("b", { textContent: counts.strong }), " strong · ", el("b", { textContent: counts.weak }), " weak"] : []),
    ...(unplaced.length ? [" · ", el("b", { textContent: unplaced.length }), " not placed"] : [])
  );
  applyFind();
}

function loadBar(n, cap, maxCap) {
  const over = n > cap;
  const track = el("span", { className: "load-track" });
  track.style.setProperty("--cap", Math.max(cap, n));
  track.style.setProperty("--u", `${100 / maxCap}%`);
  if (maxCap <= 40) {
    for (let k = 0; k < Math.max(cap, n); k++) track.append(el("i", { className: k < n ? (k >= cap ? "over" : "on") : "" }));
  } else {
    track.classList.add("solid");
    track.style.setProperty("--fill", Math.min(n / Math.max(cap, n), 1));
  }
  return el("div", { className: "load" + (over ? " is-over" : ""), role: "img", ariaLabel: `${n} of ${cap} places filled${over ? ", over the limit" : ""}` },
    track, el("span", { textContent: `${n}/${cap}${over ? " over" : ""}` }));
}

function lecturerColumn(j, members, cap, maxCap, k) {
  const r = state.result, lec = r.lecturers[j];
  const head = el("button", { type: "button", className: "lect-head", ariaPressed: String(state.focus === j) },
    el("span", { className: "lect-name", textContent: lec.name }),
    lec.field ? el("span", { className: "lect-field", textContent: lec.field }) : null);
  head.addEventListener("click", () => { state.focus = state.focus === j ? null : j; renderList(); });
  const col = el("article", { className: "lect" + (state.focus === j ? " is-focus" : "") },
    head, loadBar(members.length, cap, maxCap), nameList(members, j));
  col.style.setProperty("--i", k);
  return col;
}

function unplacedColumn(members, k) {
  const col = el("article", { className: "lect unplaced" },
    el("div", { className: "lect-head" },
      el("span", { className: "lect-name", textContent: "Not placed" }),
      el("span", { className: "lect-field", textContent: "No lecturer had room, or no match cleared your minimum." })),
    nameList(members, -1));
  col.style.setProperty("--i", k);
  return col;
}

function nameList(members, j) {
  const r = state.result;
  members.sort((a, b) => r.students[a].name.localeCompare(r.students[b].name));
  return el("ol", { className: "names" }, ...members.map((i) => {
    const s = r.students[i], score = scoreOf(i, j), lab = label(score, r.has_fields);
    const moved = r.current[i] !== r.original[i];
    const btn = el("button", { type: "button", className: "st", ariaLabel: `${s.name}, ${s.matric}${lab ? `, ${lab} match ${pct(score)}` : ""}${moved ? ", moved by you" : ""}. Move.` },
      el("span", { className: "st-name", textContent: s.name }),
      el("span", { className: "st-mat", textContent: s.matric }),
      s.field ? el("span", { className: "st-field", textContent: s.field + (lab ? ` · ${pct(score)}` : "") }) : null);
    const li = el("li", { className: [lab, moved && "moved"].filter(Boolean).join(" ") }, btn);
    li.dataset.find = `${s.name} ${s.matric}`.toLowerCase();
    btn.addEventListener("click", () => openMove(li, i));
    return li;
  }));
}

function openMove(li, i) {
  const open = $(".move", li);
  if (open) { open.remove(); return; }
  document.querySelectorAll(".move").forEach((m) => m.remove());
  const r = state.result, loads = r.names.map(() => 0);
  r.current.forEach((j) => j >= 0 && loads[j]++);
  const options = r.names.map((n, j) => ({ j, n, score: scoreOf(i, j) }))
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || a.n.localeCompare(b.n));
  const sel = el("select", {},
    ...options.map((o) => el("option", {
      value: o.j, selected: o.j === r.current[i],
      textContent: `${o.n}${o.score != null ? ` · ${pct(o.score)} match` : ""} · ${loads[o.j]}/${r.caps[o.n]}`,
    })),
    el("option", { value: -1, selected: r.current[i] === -1, textContent: "Leave unplaced" }));
  sel.addEventListener("change", () => { r.current[i] = Number(sel.value); renderList(); });
  sel.addEventListener("keydown", (e) => { if (e.key === "Escape") { box.remove(); $(".st", li).focus(); } });
  const box = el("div", { className: "move" }, el("label", {}, `Move ${r.students[i].name} to`, sel));
  li.append(box);
  sel.focus();
}

// ---------- find ----------
function applyFind() {
  const q = $("#find").value.trim().toLowerCase();
  let first = null;
  document.querySelectorAll(".names li").forEach((li) => {
    const hit = q.length > 1 && (li.dataset.find.includes(q) || li.closest(".lect").querySelector(".lect-name").textContent.toLowerCase().includes(q));
    li.classList.toggle("hit", hit);
    if (hit && !first) first = li;
  });
  return first;
}
$("#find").addEventListener("input", () => { const f = applyFind(); f && f.scrollIntoView({ block: "center", behavior: "smooth" }); });

// ---------- export ----------
function exportRows() {
  const r = state.result;
  return r.students.map((s, i) => {
    const j = r.current[i], score = scoreOf(i, j), lab = label(score, r.has_fields);
    return {
      ...s, lecturer: j >= 0 ? r.names[j] : "", lecturer_field: j >= 0 ? r.lecturers[j].field : "", score,
      match: j < 0 ? "Unassigned" : lab ? lab[0].toUpperCase() + lab.slice(1) : "No field data",
    };
  });
}

document.querySelectorAll("[data-export]").forEach((btn) => btn.addEventListener("click", async () => {
  const fmt = btn.dataset.export;
  btn.setAttribute("aria-busy", "true");
  try {
    const ext = { Excel: "xlsx", PDF: "pdf", Word: "docx", CSV: "csv" }[fmt];
    download(await pycall(fmt === "PDF" ? exporter() : engine, "export", fmt, exportRows()), `supervision-list.${ext}`, ext);
  } catch (e) {
    $("#press-counts").textContent = e.message;
  } finally {
    btn.removeAttribute("aria-busy");
  }
}));
$("#print").addEventListener("click", () => window.print());

document.querySelectorAll("[data-template]").forEach((btn) => btn.addEventListener("click", async () => {
  const [kind, ext] = btn.dataset.template.split(".");
  try { download(await pycall(engine, "template", kind, ext), `${kind}_template.${ext}`, ext); }
  catch (e) { engineNote(e.message, "is-error"); }
}));

renderRules();
