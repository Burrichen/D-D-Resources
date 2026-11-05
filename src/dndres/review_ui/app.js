/* Review Desk: client for `dndres review`. Plain JS, no build step. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const FLAG_CLASS = (f) => String(f).toLowerCase().replace(/\s+/g, "-");
const store = {
  get(k, d) { try { const v = localStorage.getItem("dndres." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("dndres." + k, JSON.stringify(v)); } catch { /* ignore */ } },
};

const S = {
  list: null,        // /api/items
  cur: null,         // /api/item payload
  a: null, b: null,  // member keys shown in the diff panes
  view: store.get("view", "prepared"),
  strip: store.get("strip", true),
  hideSame: store.get("hideSame", true),
  roles: {},
  method: "edited",
  dirty: false,
  slugTouched: false,
  diffSeq: 0,
};

// ------------------------------------------------------------------ api

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Dndres-Token": window.DNDRES_TOKEN },
    body: JSON.stringify(body),
  };
  const res = await fetch(path, opts);
  let data;
  try { data = await res.json(); } catch { data = { error: `HTTP ${res.status}` }; }
  if (!res.ok) { const e = new Error(data.error || `HTTP ${res.status}`); e.details = data.details || []; e.status = res.status; throw e; }
  return data;
}

function toast(msg, isErr = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "show" + (isErr ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.className = ""), isErr ? 6000 : 3200);
}

// ------------------------------------------------------------------ list

async function loadList() {
  try {
    S.list = await api("/api/items");
  } catch (e) {
    toast("Couldn't load the review list: " + e.message, true);
    return;
  }
  renderList();
}

function allItems() {
  return S.list ? [...S.list.conflicts, ...S.list.duplicates] : [];
}

function visibleItems() {
  const q = $("#filter").value.trim().toLowerCase();
  const hideStubs = $("#hide-stubs").checked;
  return allItems().filter((it) => {
    if (hideStubs && it.flag === "all stubs") return false;
    if (!q) return true;
    return (it.title + " " + it.members.join(" ") + " " + (it.reasons || []).join(" ")).toLowerCase().includes(q);
  });
}

function renderList() {
  const L = S.list;
  if (!L) return;
  $("#counts").textContent = `${L.conflicts.length} conflict${L.conflicts.length === 1 ? "" : "s"} · ${L.duplicates.length} duplicate group${L.duplicates.length === 1 ? "" : "s"}`;
  $("#generated").textContent = L.generated ? "duplicates.md generated " + new Date(L.generated).toLocaleString() : "";
  const vis = new Set(visibleItems().map((i) => i.id));
  const curId = S.cur?.item.id;
  const section = (title, items) => {
    const shown = items.filter((i) => vis.has(i.id));
    let h = `<div class="list-head">${esc(title)} (${shown.length}${shown.length !== items.length ? ` of ${items.length}` : ""})</div>`;
    if (!shown.length) h += `<div class="list-empty">${items.length ? "Hidden by filter." : "None."}</div>`;
    for (const it of shown) {
      const srcs = [...new Set(it.members.map((k) => k.startsWith("content:") ? "entry" : (k.split(":")[0].match(/-(v\d+)$/i)?.[1] ?? k.split(":")[0])))];
      h += `<a class="li${it.id === curId ? " active" : ""}" href="#/i/${it.id}">
        <div class="t" title="${esc(it.title)}">${it.number ? it.number + ". " : ""}${esc(it.title)}</div>
        <div class="m"><span class="flag ${FLAG_CLASS(it.flag)}">${esc(it.flag)}</span>${it.members.length} files · ${esc(srcs.join(", "))}</div>
        ${it.reasons?.length ? `<div class="why">${esc(it.reasons.join("; "))}</div>` : ""}
      </a>`;
    }
    return h;
  };
  $("#list").innerHTML = section("Conflicts", L.conflicts) + section("Duplicates", L.duplicates);
}

// ------------------------------------------------------------------ routing

function route() {
  const m = location.hash.match(/^#\/i\/([\w-]+)/);
  if (m) openItem(m[1]);
  else showHome();
}

function confirmLeave() {
  return !S.dirty || confirm("You have unsaved changes in this item. Discard them?");
}

function showHome() {
  S.cur = null;
  S.dirty = false;
  renderList();
  const L = S.list || { conflicts: [], duplicates: [], stubs: 0 };
  const ident = L.duplicates.filter((d) => d.flag === "IDENTICAL").length;
  const stubs = L.duplicates.filter((d) => d.flag === "all stubs").length;
  $("#main").innerHTML = `<div class="empty">
    <h1>Duplicates and conflicts</h1>
    <p class="muted">Pick an item on the left. This list is read fresh from <code>review/duplicates.md</code> and <code>review/conflicts.md</code> each time you refresh or come back to this tab.</p>
    <div class="stat-row">
      <div class="stat"><b>${L.conflicts.length}</b>open conflicts</div>
      <div class="stat"><b>${L.duplicates.length}</b>duplicate groups</div>
      <div class="stat"><b>${ident}</b>identical text</div>
      <div class="stat"><b>${stubs}</b>all stubs</div>
    </div>
    <ol>
      <li>The top half compares two versions side by side. Red is only in <b>A</b>, green is only in <b>B</b>, and the brighter highlight marks the words that differ.</li>
      <li>Fill the result: <b>Use A</b> or <b>Use B</b> takes one version, and <b>Merge A + B</b> combines both. Merge goes section by section, keeps everything from both sides, and marks the passages the two versions word differently.</li>
      <li>Resolve each marked passage with <b>Accept A</b>, <b>Accept B</b> or <b>Accept both</b>, or edit the result directly.</li>
      <li>Check the entry details on the right, then <b>Save entry</b> (<span class="kbd">⌘/Ctrl+S</span>). The group is removed from the review file, and the decision goes into <code>review/decisions.md</code>.</li>
      <li>If they aren't really the same thing, use <b>Dismiss…</b> instead.</li>
    </ol>
  </div>`;
}

async function openItem(id) {
  if (S.cur && S.cur.item.id !== id && !confirmLeave()) {
    history.replaceState(null, "", "#/i/" + S.cur.item.id);
    return;
  }
  if (S.cur?.item.id === id) return;
  $("#main").innerHTML = `<div class="empty muted">Loading…</div>`;
  let data;
  try {
    data = await api(`/api/item?id=${encodeURIComponent(id)}&strip=${S.strip ? 1 : 0}`);
  } catch (e) {
    S.cur = null;
    renderList();
    $("#main").innerHTML = `<div class="empty"><h1>Not found</h1><p class="muted">${esc(e.message)}</p><p><a href="#/">Back to overview</a></p></div>`;
    return;
  }
  S.cur = data;
  S.dirty = false;
  S.hadConflicts = false;
  S.slugTouched = false;
  S.method = "edited";
  S.roles = {};
  const sug = data.suggest;
  for (const m of data.members) if (m.kind === "raw") S.roles[m.key] = sug.roles?.[m.key] ?? (m.key === sug.primary ? "primary" : "merged");
  // default panes: entry (if any) or the largest file on the left, the next one on the right
  const ms = data.members.filter((m) => m.exists);
  const ordered = [...ms].sort((x, y) => (y.kind === "entry") - (x.kind === "entry") || y.prepared.length - x.prepared.length);
  S.a = ordered[0]?.key ?? data.members[0]?.key;
  S.b = ordered.find((m) => m.key !== S.a)?.key ?? data.members[1]?.key ?? S.a;
  renderList();
  renderItem();
  // conflicts start from the current entry; identical groups start from the one copy
  if (sug.mode === "update") setResult(member(sug.target).prepared, "use", false);
  else if (data.item.flag === "IDENTICAL") setResult(member(S.a).prepared, "use", false);
}

async function reloadCurrent() {
  if (!S.cur) return;
  const keep = $("#result")?.value ?? "";
  const id = S.cur.item.id;
  try {
    const data = await api(`/api/item?id=${encodeURIComponent(id)}&strip=${S.strip ? 1 : 0}`);
    S.cur.members = data.members;
    S.cur.suggest.extra_conflicts = data.suggest.extra_conflicts;
    renderDiff();
    renderWarnings();
    $("#result").value = keep;
    syncEditor();
  } catch (e) { toast(e.message, true); }
}

const member = (key) => S.cur.members.find((m) => m.key === key);
const textOf = (m) => (S.view === "original" ? m.body : m.prepared);
const shortLabel = (m) => (m.kind === "entry" ? "entry" : m.label);
const markerLabel = (m) => `${shortLabel(m)} · ${m.path}`;

// ------------------------------------------------------------------ item view

function renderItem() {
  const { item, members, suggest: sug, types } = S.cur;
  const upd = sug.mode === "update";
  const opt = (m, sel) => `<option value="${esc(m.key)}"${m.key === sel ? " selected" : ""}>${esc(shortLabel(m))} · ${esc(m.path)}${m.exists ? "" : " (missing)"}</option>`;
  const memberRow = (m) => {
    if (m.kind === "entry") return `<div class="member"><span class="src">entry</span><span class="path" title="${esc(m.path)}">${esc(m.path)}</span><span class="muted">target</span></div>`;
    const sel = S.roles[m.key];
    const size = (S.cur.item.sizes || {})[m.key];
    return `<div class="member${sel === "exclude" ? " excluded" : ""}" data-key="${esc(m.key)}">
      <span class="src">${esc(m.label)}</span>
      <span class="path" title="${esc(m.source + ":" + m.path)}">${esc(m.path)}</span>
      <span class="muted">${size ?? m.prepared.length} chars${m.exists ? "" : " · missing"}</span>
      <select class="role" aria-label="Role for ${esc(m.path)}" title="How this file is cited in the entry's sources">
        ${["primary", "merged", "superseded", "exclude"].map((r) => `<option${r === sel ? " selected" : ""}>${r}</option>`).join("")}
      </select></div>`;
  };
  const claims = item.kind === "conflict" ? `<div class="question"><b>${esc(item.title)}</b>
      ${Object.keys(item.claims).length ? `<ul>${Object.entries(item.claims).map(([k, v]) => `<li><code>${esc(k)}</code>: ${esc(v)}</li>`).join("")}</ul>` : ""}
      ${item.notes.length ? `<div class="muted">${esc(item.notes.join(" "))}</div>` : ""}</div>` : "";

  $("#main").innerHTML = `
  <section class="item-head">
    <div class="title-row">
      <span class="flag ${FLAG_CLASS(item.flag)}">${esc(item.flag)}</span>
      <h1>${esc(item.title)}</h1>
      ${item.reasons?.length ? `<span class="why">${esc(item.reasons.join("; "))}</span>` : ""}
    </div>
    <div class="members">${members.map(memberRow).join("")}</div>
    ${claims}
  </section>

  <section class="diff-wrap">
    <div class="diff-tools">
      <div class="group">
        <button class="btn small" id="prev-chg" title="Previous change">↑</button>
        <button class="btn small" id="next-chg" title="Next change">↓</button>
        <span class="stats" id="diff-stats"></span>
      </div>
      <span class="spacer"></span>
      <label class="check"><input type="checkbox" id="hide-same"${S.hideSame ? " checked" : ""}> Hide unchanged</label>
      <label class="check" title="Drop lines copied from your Obsidian templates and headings with nothing under them"><input type="checkbox" id="strip"${S.strip ? " checked" : ""}${S.view === "original" ? " disabled" : ""}> Strip template scaffolding</label>
      <div class="seg" role="group" aria-label="Text shown">
        <button id="v-prepared" class="${S.view === "prepared" ? "on" : ""}" title="Converted to content/ markdown: wikilinks resolved, dataview removed, %% comments moved to GM notes">Prepared</button>
        <button id="v-original" class="${S.view === "original" ? "on" : ""}" title="Exactly what is in raw/">Original</button>
      </div>
    </div>
    <div class="pane-heads">
      <div class="pane-head"><span class="side a">A</span>
        <select id="sel-a" aria-label="Version A">${members.map((m) => opt(m, S.a)).join("")}</select>
        <button class="btn small a" id="use-a">Use A</button>
        <button class="btn small" id="mergein-a" title="Merge A into whatever is in the result now">Merge into result</button>
      </div>
      <div class="pane-head"><span class="side b">B</span>
        <select id="sel-b" aria-label="Version B">${members.map((m) => opt(m, S.b)).join("")}</select>
        <button class="btn small b" id="use-b">Use B</button>
        <button class="btn small" id="mergein-b" title="Merge B into whatever is in the result now">Merge into result</button>
      </div>
    </div>
    <div class="diff" id="diff"></div>
  </section>

  <section class="bottom">
    <div class="result">
      <div class="result-tools">
        <span class="label">Result</span>
        <button class="btn small primary" id="merge-ab" title="Section-aware merge of A and B">Merge A + B</button>
        <button class="btn small a" id="use-a2">Use A</button>
        <button class="btn small b" id="use-b2">Use B</button>
        <button class="btn small ghost" id="clear">Clear</button>
        <span class="spacer"></span>
        <span class="muted" id="result-stats"></span>
      </div>
      <div class="conflict-bar" id="conflict-bar"></div>
      <div class="editor">
        <div class="backdrop" id="backdrop" aria-hidden="true"></div>
        <textarea id="result" spellcheck="false" aria-label="Result markdown"></textarea>
        <div class="placeholder" id="placeholder">Empty. Choose Use A, Use B or Merge A + B, or type here.</div>
      </div>
    </div>

    <form class="entry-form" id="entry-form" autocomplete="off">
      <h2>${upd ? "Update entry" : "New entry"}</h2>
      ${upd ? `<div class="note info">This updates <code>${esc(sug.id)}</code>. Ids are a public contract, so type and slug are locked.</div>` : ""}
      <div class="row2">
        <label class="field"><span>Type</span><select id="f-type"${upd ? " disabled" : ""}>${types.map((t) => `<option${t === sug.type ? " selected" : ""}>${t}</option>`).join("")}</select></label>
        <label class="field"><span>Status</span><select id="f-status">${["canonical", "draft"].map((s) => `<option${s === sug.status ? " selected" : ""}>${s}</option>`).join("")}</select></label>
      </div>
      <label class="field"><span>Name</span><input id="f-name" value="${esc(sug.name)}"></label>
      <label class="field"><span>Slug</span><input id="f-slug" value="${esc(sug.slug)}"${upd ? " disabled" : ""}></label>
      <div class="idpreview">id: <b id="id-preview"></b></div>
      <label class="field"><span>Aliases (one per line)</span><textarea id="f-aliases" rows="2" style="font-family:var(--sans)">${esc(sug.aliases.join("\n"))}</textarea></label>
      <label class="field"><span>Summary (one sentence)</span><textarea id="f-summary" rows="2" style="font-family:var(--sans)">${esc(sug.summary)}</textarea></label>
      <label class="field"><span>Tags (comma-separated, e.g. pantheon/major)</span><input id="f-tags" value="${esc(sug.tags.join(", "))}"></label>
      <label class="field"><span>Related ids (comma-separated)</span><input id="f-related" value="${esc(sug.related.join(", "))}" list="ids-list"></label>
      <datalist id="ids-list">${(S.cur.existing_ids || []).map((i) => `<option value="${esc(i)}">`).join("")}</datalist>
      <label class="field"><span>Licence</span><input id="f-licence" value="${esc(sug.licence)}"></label>
      <label class="field"><span>Extra fields (YAML, snake_case)</span><textarea id="f-extra" rows="4">${esc(sug.extra_yaml)}</textarea></label>
      <div id="warnings"></div>
      <label class="field"><span>Decision note for decisions.md (optional)</span><input id="f-note" placeholder="e.g. v3 is the newer lore"></label>
      <div id="errors"></div>
      <div class="actions">
        <button type="submit" class="btn primary" id="save">Save entry <span class="kbd">⌘S</span></button>
        ${item.kind === "duplicate" ? `<button type="button" class="btn danger" id="dismiss">Dismiss…</button>` : ""}
        <button type="button" class="btn ghost" id="skip" title="Go to the next item without changing anything">Skip</button>
      </div>
    </form>
  </section>`;

  bindItem();
  updateIdPreview();
  renderWarnings();
  renderDiff();
  syncEditor();
}

function bindItem() {
  $("#sel-a").onchange = (e) => { S.a = e.target.value; renderDiff(); };
  $("#sel-b").onchange = (e) => { S.b = e.target.value; renderDiff(); };
  for (const side of ["a", "b"]) {
    const use = () => {
      const m = member(S[side]);
      if (!m) return;
      setResult(m.prepared, "use");
      if (m.kind === "raw") {
        for (const k in S.roles) if (S.roles[k] === "primary") S.roles[k] = "merged";
        S.roles[m.key] = "primary";
        renderMembers();
        renderWarnings();
      }
      $("#result").focus();
    };
    $("#use-" + side).onclick = use;
    $("#use-" + side + "2").onclick = use;
    $("#mergein-" + side).onclick = () => mergeInto(side);
  }
  $("#merge-ab").onclick = mergeAB;
  $("#clear").onclick = () => setResult("", "edited");
  $("#prev-chg").onclick = () => jumpChange(-1);
  $("#next-chg").onclick = () => jumpChange(1);
  $("#hide-same").onchange = (e) => { S.hideSame = e.target.checked; store.set("hideSame", S.hideSame); renderDiff(); };
  $("#strip").onchange = (e) => { S.strip = e.target.checked; store.set("strip", S.strip); reloadCurrent(); };
  $("#v-prepared").onclick = () => setView("prepared");
  $("#v-original").onclick = () => setView("original");
  document.querySelectorAll(".member .role").forEach((sel) => {
    sel.onchange = (e) => {
      const key = e.target.closest(".member").dataset.key;
      if (e.target.value === "primary") for (const k in S.roles) if (S.roles[k] === "primary") S.roles[k] = "merged";
      S.roles[key] = e.target.value;
      S.dirty = true;
      renderMembers();
      renderWarnings();
    };
  });

  const ta = $("#result");
  ta.addEventListener("input", () => {
    if (!S.programmatic) {
      S.dirty = true;
      if (S.method === "use" || S.method === "merge") S.method += "+edit";
    }
    syncEditor();
  });
  ta.addEventListener("scroll", () => { $("#backdrop").scrollTop = ta.scrollTop; });
  ta.addEventListener("click", renderConflictBar);
  ta.addEventListener("keyup", renderConflictBar);
  new ResizeObserver(syncEditor).observe(ta);

  $("#f-name").addEventListener("input", () => {
    if (!S.slugTouched && S.cur.suggest.mode === "create") $("#f-slug").value = slugify($("#f-name").value);
    updateIdPreview();
  });
  $("#f-slug").addEventListener("input", () => { S.slugTouched = true; updateIdPreview(); });
  $("#f-type").addEventListener("change", updateIdPreview);
  $("#entry-form").addEventListener("input", () => { S.dirty = true; });
  $("#entry-form").addEventListener("submit", (e) => { e.preventDefault(); save(); });
  $("#skip").onclick = () => goNext(true);
  if ($("#dismiss")) $("#dismiss").onclick = openDismiss;
}

function renderMembers() {
  document.querySelectorAll(".member[data-key]").forEach((row) => {
    const r = S.roles[row.dataset.key];
    row.querySelector(".role").value = r;
    row.classList.toggle("excluded", r === "exclude");
  });
}

function setView(v) {
  S.view = v;
  store.set("view", v);
  $("#v-prepared").classList.toggle("on", v === "prepared");
  $("#v-original").classList.toggle("on", v === "original");
  $("#strip").disabled = v === "original";
  renderDiff();
}

function renderWarnings() {
  const sug = S.cur.suggest;
  const refs = [...new Set(S.cur.members.filter((m) => S.roles[m.key] !== "exclude").flatMap((m) => m.refs || []))];
  let h = "";
  if (sug.extra_conflicts?.length) {
    h += `<div class="note"><b>The files' frontmatter disagrees.</b> The extra fields above use the primary file's values, so change them if that's wrong.<ul>${sug.extra_conflicts.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></div>`;
  }
  if (refs.length) {
    h += `<div class="note info">These links point at notes that aren't curated yet, so they became plain text: ${refs.map((r) => `<code>${esc(r)}</code>`).join(", ")}</div>`;
  }
  $("#warnings").innerHTML = h;
}

function updateIdPreview() {
  $("#id-preview").textContent = `${$("#f-type").value}/${$("#f-slug").value || "…"}`;
}

function slugify(t) {
  return t.normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase() || "untitled";
}

// ------------------------------------------------------------------ diff

async function renderDiff() {
  const el = $("#diff");
  const A = member(S.a), B = member(S.b);
  if (!A || !B) { el.innerHTML = `<div class="diff-note">Pick two versions to compare.</div>`; return; }
  if (A.key === B.key) { el.innerHTML = `<div class="diff-note">A and B are the same file. Pick a different one on either side.</div>`; $("#diff-stats").textContent = ""; return; }
  const seq = ++S.diffSeq;
  let d;
  try { d = await api("/api/diff", { a: textOf(A), b: textOf(B) }); } catch (e) { el.innerHTML = `<div class="diff-note">${esc(e.message)}</div>`; return; }
  if (seq !== S.diffSeq) return;
  $("#diff-stats").textContent = d.hunks ? `${d.hunks} change${d.hunks === 1 ? "" : "s"} · −${d.removed} +${d.added} lines · ${d.similarity}% similar` : "No differences";
  const cell = (side, row) => {
    const has = side === "l" ? "l" in row : "r" in row;
    const n = side === "l" ? row.ln : row.rn;
    const segs = side === "l" ? row.ls : row.rs;
    const txt = side === "l" ? row.l : row.r;
    const cls = row.t === "chg" ? (has ? " has" : " none") : "";
    const body = !has ? "" : segs ? segs.map(([t, w]) => (w ? `<span class="w">${esc(t)}</span>` : esc(t))).join("") : esc(txt);
    return `<span class="ln ${side}${cls}">${has ? n : ""}</span><div class="c ${side}${cls}">${body}</div>`;
  };
  const rows = d.rows;
  const CTX = 3;
  const out = [];
  if (!rows.length) out.push(`<div class="diff-note">Both versions are empty.</div>`);
  let i = 0;
  while (i < rows.length) {
    if (S.hideSame && rows[i].t === "eq") {
      let j = i;
      while (j < rows.length && rows[j].t === "eq") j++;
      const start = i === 0 ? 0 : i + CTX, end = j === rows.length ? j : j - CTX;
      if (end - start > 2) {
        for (let k = i; k < start; k++) out.push(`<div class="drow eq">${cell("l", rows[k])}${cell("r", rows[k])}</div>`);
        out.push(`<div class="drow"><div class="fold" data-from="${start}" data-to="${end}">⋯ ${end - start} unchanged lines (click to show)</div></div>`);
        for (let k = end; k < j; k++) out.push(`<div class="drow eq">${cell("l", rows[k])}${cell("r", rows[k])}</div>`);
        i = j;
        continue;
      }
    }
    const r = rows[i];
    out.push(`<div class="drow ${r.t}"${r.h ? ` data-h="${r.h}"` : ""}>${cell("l", r)}${cell("r", r)}</div>`);
    i++;
  }
  el.innerHTML = out.join("");
  el.querySelectorAll(".fold").forEach((f) => {
    f.onclick = () => {
      const from = +f.dataset.from, to = +f.dataset.to;
      f.parentElement.outerHTML = rows.slice(from, to).map((r) => `<div class="drow eq">${cell("l", r)}${cell("r", r)}</div>`).join("");
    };
  });
  S.curHunk = 0;
}

function jumpChange(dir) {
  const el = $("#diff");
  const firsts = [...el.querySelectorAll(".drow[data-h]")].filter((r, i, a) => i === 0 || a[i - 1].dataset.h !== r.dataset.h);
  if (!firsts.length) return;
  const top = el.scrollTop + 4;
  let target;
  if (dir > 0) target = firsts.find((r) => r.offsetTop > top + 2) || firsts[0];
  else target = [...firsts].reverse().find((r) => r.offsetTop < top - 2) || firsts[firsts.length - 1];
  el.scrollTop = target.offsetTop - 30;
  el.querySelectorAll(".flash").forEach((r) => r.classList.remove("flash"));
  el.querySelectorAll(`.drow[data-h="${target.dataset.h}"]`).forEach((r) => r.classList.add("flash"));
}

// ------------------------------------------------------------------ result editor

// Replace a range of the result. insertText keeps the browser's undo stack (Cmd/Ctrl+Z works).
function replaceRange(start, end, text) {
  const ta = $("#result");
  S.programmatic = true;
  try {
    ta.focus();
    ta.setSelectionRange(start, end);
    if (!document.execCommand("insertText", false, text)) ta.setRangeText(text, start, end, "end");
  } finally {
    S.programmatic = false;
  }
}

function setResult(text, method, markDirty = true) {
  const ta = $("#result");
  const wasDirty = S.dirty;
  replaceRange(0, ta.value.length, text);
  ta.setSelectionRange(0, 0);
  ta.scrollTop = 0;
  S.method = method;
  S.dirty = markDirty || wasDirty;
  syncEditor();
}

async function mergeAB() {
  const A = member(S.a), B = member(S.b);
  if (!A || !B) return;
  if ($("#result").value.trim() && !confirm("Replace the current result with a fresh merge of A and B?")) return;
  try {
    const r = await api("/api/merge", { a: A.prepared, b: B.prepared, a_label: markerLabel(A), b_label: markerLabel(B) });
    setResult(r.text, "merge");
    toast(r.conflicts ? `Merged with ${r.conflicts} passage${r.conflicts === 1 ? "" : "s"} to decide. They're highlighted in the result.` : "Merged cleanly.");
    gotoConflict(0);
  } catch (e) { toast(e.message, true); }
}

async function mergeInto(side) {
  const M = member(S[side]);
  if (!M) return;
  const cur = $("#result").value;
  if (!cur.trim()) { setResult(M.prepared, "use"); return; }
  try {
    const r = await api("/api/merge", { a: cur, b: M.prepared, a_label: "result", b_label: markerLabel(M) });
    setResult(r.text, "merge");
    toast(r.conflicts ? `Merged ${shortLabel(M)} in: ${r.conflicts} new passage${r.conflicts === 1 ? "" : "s"} to decide.` : `Merged ${shortLabel(M)} into the result.`);
  } catch (e) { toast(e.message, true); }
}

function parseConflicts(text) {
  const lines = text.split("\n");
  const out = [];
  let cur = null, off = 0;
  lines.forEach((ln, i) => {
    if (/^<<<<<<<( |$)/.test(ln)) cur = { start: i, startOff: off, sep: -1, la: ln.slice(8).trim() || "A" };
    else if (cur && cur.sep < 0 && ln === "=======") cur.sep = i;
    else if (cur && cur.sep >= 0 && /^>>>>>>>( |$)/.test(ln)) {
      Object.assign(cur, { end: i, endOff: off + ln.length, lb: ln.slice(8).trim() || "B" });
      out.push(cur);
      cur = null;
    }
    off += ln.length + 1;
  });
  return out;
}

function syncEditor() {
  const ta = $("#result"), bd = $("#backdrop");
  if (!ta) return;
  const text = ta.value;
  const lines = text.split("\n");
  const cls = new Array(lines.length).fill("");
  for (const c of parseConflicts(text)) {
    for (let i = c.start; i <= c.end; i++) cls[i] = i === c.start || i === c.sep || i === c.end ? "cm" : i < c.sep ? "ca" : "cb";
  }
  bd.innerHTML = lines.map((l, i) => `<div${cls[i] ? ` class="${cls[i]}"` : ""}>${esc(l) || " "}</div>`).join("");
  bd.style.width = ta.clientWidth + "px";
  bd.scrollTop = ta.scrollTop;
  $("#placeholder").style.display = text ? "none" : "";
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  $("#result-stats").textContent = `${lines.length} lines · ${words} words`;
  renderConflictBar();
}

function currentConflict(list) {
  const pos = $("#result").selectionStart;
  let idx = list.findIndex((c) => pos >= c.startOff && pos <= c.endOff);
  if (idx < 0) idx = list.findIndex((c) => c.startOff >= pos);
  return idx < 0 ? 0 : idx;
}

function renderConflictBar() {
  const bar = $("#conflict-bar");
  if (!bar) return;
  const list = parseConflicts($("#result").value);
  if (!list.length) {
    // only say "all resolved" if this item had conflicts at some point
    bar.className = "conflict-bar" + (S.hadConflicts ? " show clear" : "");
    bar.innerHTML = "✓ All conflicts resolved.";
    return;
  }
  S.hadConflicts = true;
  const i = currentConflict(list), c = list[i];
  let nameA = c.la.split(" · ")[0], nameB = c.lb.split(" · ")[0];
  if (nameA === nameB) {
    // same vault on both sides: tell them apart by file name
    const base = (l) => (l.split(" · ")[1] || l).split("/").pop().replace(/\.md$/, "");
    nameA = `${nameA} (${base(c.la)})`;
    nameB = `${nameB} (${base(c.lb)})`;
  }
  bar.className = "conflict-bar show";
  bar.innerHTML = `<span class="count">Conflict ${i + 1} of ${list.length}</span>
    <button class="btn small a" data-act="a" title="${esc(c.la)}">Accept ${esc(nameA)}</button>
    <button class="btn small b" data-act="b" title="${esc(c.lb)}">Accept ${esc(nameB)}</button>
    <button class="btn small" data-act="both">Accept both</button>
    <span class="spacer" style="flex:1"></span>
    <button class="btn small ghost" data-nav="-1" title="Previous conflict">↑ Prev</button>
    <button class="btn small ghost" data-nav="1" title="Next conflict">↓ Next</button>`;
  bar.querySelectorAll("[data-act]").forEach((b) => (b.onclick = () => resolveConflict(i, b.dataset.act)));
  bar.querySelectorAll("[data-nav]").forEach((b) => (b.onclick = () => gotoConflict((i + +b.dataset.nav + list.length) % list.length)));
}

function gotoConflict(i) {
  const list = parseConflicts($("#result").value);
  if (!list.length) return;
  const c = list[Math.max(0, Math.min(i, list.length - 1))];
  const ta = $("#result");
  ta.focus();
  ta.setSelectionRange(c.startOff, c.startOff);
  const lineEl = $("#backdrop").children[c.start];
  if (lineEl) ta.scrollTop = Math.max(0, lineEl.offsetTop - 40);
  $("#backdrop").scrollTop = ta.scrollTop;
  renderConflictBar();
}

function resolveConflict(i, which) {
  const ta = $("#result");
  const text = ta.value;
  const c = parseConflicts(text)[i];
  if (!c) return;
  const lines = text.split("\n");
  const a = lines.slice(c.start + 1, c.sep), b = lines.slice(c.sep + 1, c.end);
  const listy = /^\s*([-*+]|\d+[.)]|\|)/;
  let repl = which === "a" ? a : which === "b" ? b : [...a, ...(a.length && b.length && !(listy.test(a[a.length - 1]) && listy.test(b[0])) ? [""] : []), ...b];
  replaceRange(c.startOff, c.endOff, repl.join("\n"));
  ta.setSelectionRange(c.startOff, c.startOff);
  S.dirty = true;
  syncEditor();
  const left = parseConflicts(ta.value);
  if (left.length) gotoConflict(Math.min(i, left.length - 1));
}

// ------------------------------------------------------------------ save / dismiss / next

async function save() {
  if (!S.cur) return;
  const body = $("#result").value;
  $("#errors").innerHTML = "";
  const payload = {
    id: S.cur.item.id,
    body,
    method: S.method,
    roles: S.roles,
    note: $("#f-note").value,
    meta: {
      type: $("#f-type").value, name: $("#f-name").value, slug: $("#f-slug").value,
      aliases: $("#f-aliases").value.split("\n").map((x) => x.trim()).filter(Boolean), summary: $("#f-summary").value, tags: $("#f-tags").value,
      related: $("#f-related").value, status: $("#f-status").value, licence: $("#f-licence").value,
      extra_yaml: $("#f-extra").value,
    },
  };
  $("#save").disabled = true;
  try {
    const r = await api("/api/save", payload);
    S.dirty = false;
    toast(r.message);
    await goNext(false);
  } catch (e) {
    $("#errors").innerHTML = `<div class="note err"><b>${esc(e.message)}</b>${e.details?.length ? `<ul>${e.details.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>` : ""}</div>`;
    $("#errors").scrollIntoView({ block: "nearest" });
  } finally {
    if ($("#save")) $("#save").disabled = false;
  }
}

function openDismiss() {
  const dlg = $("#dismiss-dlg");
  const reasons = S.list.dismiss_reasons;
  const def = S.cur.item.flag === "all stubs" ? "stubs" : "separate";
  $("#dismiss-reasons").innerHTML = Object.entries(reasons).map(([k, v]) =>
    `<label class="radio"><input type="radio" name="reason" value="${esc(k)}"${k === def ? " checked" : ""}> <span>${esc(v)}</span></label>`).join("");
  $("#dismiss-form").note.value = "";
  dlg.returnValue = "";
  dlg.showModal();
  dlg.onclose = async () => {
    if (dlg.returnValue !== "ok") return;
    const f = $("#dismiss-form");
    try {
      const r = await api("/api/dismiss", { id: S.cur.item.id, reason: f.reason.value, note: f.note.value });
      S.dirty = false;
      toast(r.message);
      await goNext(false);
    } catch (e) { toast(e.message, true); }
  };
}

async function goNext(askFirst) {
  if (askFirst && !confirmLeave()) return;
  const order = visibleItems().map((i) => i.id);
  const at = order.indexOf(S.cur?.item.id);
  S.dirty = false;
  await loadList();
  const now = visibleItems().map((i) => i.id);
  // the next item after the current one in the old order that still exists
  const next = order.slice(at + 1).find((id) => now.includes(id)) || now.find((id) => id !== S.cur?.item.id);
  S.cur = null;
  location.hash = next ? "#/i/" + next : "#/";
  if (!next) showHome();
}

// ------------------------------------------------------------------ boot

$("#filter").addEventListener("input", renderList);
$("#hide-stubs").checked = store.get("hideStubs", false);
$("#hide-stubs").addEventListener("change", (e) => { store.set("hideStubs", e.target.checked); renderList(); });
$("#btn-refresh").onclick = async () => { await loadList(); toast("Re-read the review files."); if (S.cur && !allItems().some((i) => i.id === S.cur.item.id)) toast("This item is no longer in the review files.", true); };
$("#btn-rescan").onclick = async () => {
  if (!confirm("Re-run `dndres dupes`? This regenerates review/duplicates.md from raw/ and content/.")) return;
  try { const r = await api("/api/rescan", {}); toast(r.message); await loadList(); } catch (e) { toast(e.message, true); }
};
window.addEventListener("hashchange", route);
window.addEventListener("focus", () => loadList());
window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    if (S.cur) save();
  }
});

loadList().then(route);
