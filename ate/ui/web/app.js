/* Liquid-glass ATE — Test Database + live timeline (DUT / config Continue) */
const RPC = "http://127.0.0.1:8766";
let pendingPrompt = null;
let gateQueue = [];
let runPollActive = false;
let sessionOpen = false;
let activeFamily = "opamp";
let fixtureCatalog = [];
let dbTree = { components: {} };
let dbContext = null;
let lastTimeline = null;
let lastScrollId = "";
let allTests = [];
let substepState = {};
let activeSubstepTestId = "";

async function rpc(method, params = {}) {
  const res = await fetch(RPC, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
  });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    if (res.status === 501) {
      throw new Error("Worker :8766 is JSON-RPC POST. Open UI at http://127.0.0.1:5174");
    }
    throw new Error(`Worker HTTP ${res.status}: ${text.slice(0, 160)}`);
  }
  if (body.error) throw new Error(body.error.message || JSON.stringify(body.error));
  return body.result;
}

function $(id) { return document.getElementById(id); }

let knownFamilies = ["opamp", "logic", "level", "switch"];
let familyLabels = { opamp: "OpAmp", logic: "Logic", level: "Level", switch: "Analog SW" };

const FAMILY_UI = {
  opamp: { brand: "OpAmp ATE", kicker: "Operator console" },
  logic: { brand: "Logic ATE", kicker: "Operator console" },
  switch: { brand: "Analog Switch ATE", kicker: "Operator console" },
  lim: { brand: "Analog Switch ATE", kicker: "Operator console" },
  level: { brand: "Level ATE", kicker: "Stub — no suite yet" },
};

function familyMeta(family) {
  if (FAMILY_UI[family]) return FAMILY_UI[family];
  const nice = (familyLabels[family] || String(family || "ATE")).replace(/_/g, " ");
  return { brand: `${nice} ATE`, kicker: "Imported family" };
}

function renderFamilyRail(known, labels) {
  const rail = document.querySelector(".family-rail");
  if (!rail) return;
  if (Array.isArray(known) && known.length) knownFamilies = known.slice();
  if (labels && typeof labels === "object") {
    familyLabels = { ...familyLabels, ...labels };
  }
  const builtins = new Set(["opamp", "logic", "level", "switch"]);
  rail.querySelectorAll(".family-btn[data-extra='1']").forEach((el) => el.remove());
  (known || []).forEach((fam) => {
    if (fam === "lim") return;
    if (rail.querySelector(`.family-btn[data-family="${fam}"]`)) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "family-btn";
    btn.dataset.family = fam;
    btn.dataset.extra = "1";
    btn.textContent = familyLabels[fam] || fam;
    if (fam === "level") {
      btn.classList.add("family-stub");
      btn.title = "Stub slot — no Level suite yet";
    }
    if (builtins.has(fam)) {
      const levelBtn = rail.querySelector('.family-btn[data-family="level"]');
      if (levelBtn) rail.insertBefore(btn, levelBtn);
      else rail.appendChild(btn);
    } else {
      rail.appendChild(btn);
    }
  });
}

function paintBrand(family) {
  const meta = familyMeta(family);
  const title = $("brand-title");
  if (title) title.textContent = meta.brand;
  const kicker = document.querySelector(".brand-kicker");
  if (kicker) kicker.textContent = meta.kicker;
  document.querySelectorAll(".family-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.family === family);
  });
}

function updateFamilyChrome(family) {
  activeFamily = family || "opamp";
  paintBrand(activeFamily);
  const gainPanel = $("panel-gain-boards");
  if (gainPanel) gainPanel.classList.toggle("hidden", activeFamily !== "opamp");
}

async function syncFamilyFromWorker() {
  const res = await rpc("get_family");
  renderFamilyRail(res.known || [], res.labels || {});
  updateFamilyChrome(res.family || "opamp");
  return activeFamily;
}

async function switchFamily(family) {
  if (!family || family === activeFamily) return activeFamily;
  const res = await rpc("set_family", { family });
  updateFamilyChrome(res.family || family);
  await loadFixtureCatalog();
  await loadTests();
  await loadParamDefaults();
  log(`Family switched: ${activeFamily}\n`);
  return activeFamily;
}

function familyFromComponent(component) {
  const c = String(component || "").trim().toLowerCase().replace(/[\s_]/g, "");
  if (c === "logic") return "logic";
  if (c === "level") return "level";
  if (c === "opamp") return "opamp";
  if (c === "switch" || c === "analogswitch" || c === "analogsw" || c === "lim") return "switch";
  const hit = knownFamilies.find((f) => String(f).toLowerCase().replace(/[\s_]/g, "") === c);
  if (hit) return hit;
  return c || "opamp";
}

function componentFromFamily(family) {
  const labels = { opamp: "OpAmp", logic: "Logic", switch: "AnalogSwitch", lim: "AnalogSwitch", level: "Level" };
  if (labels[family]) return labels[family];
  const comps = Object.keys(dbTree.components || {});
  return comps.find((c) => c.toLowerCase() === family) || "";
}

function firstCampaignInComponent(component) {
  const partsObj = ((dbTree.components || {})[component] || {}).parts || {};
  const parts = Object.keys(partsObj);
  if (!parts.length) return null;
  const part = parts[0];
  const pkgsObj = (partsObj[part] || {}).packages || {};
  const packages = Object.keys(pkgsObj);
  const pkg = packages[0] || "";
  const opsObj = (pkgsObj[pkg] || {}).operators || {};
  const operators = Object.keys(opsObj);
  const prefer = writeOperatorLabel();
  const op = operators.includes(prefer) ? prefer : (operators[0] || prefer || "Eugene");
  const versions = (opsObj[op] || {}).versions || [];
  return {
    component,
    part,
    package: pkg,
    operator: op,
    version: versions[0] || "Version_1",
    model: "",
    year: ($("db-year") && $("db-year").value) || "2026",
  };
}

const OWNER_KEY = "ate_operator";
let ownersList = [];

function readSavedOwner() {
  try {
    return localStorage.getItem(OWNER_KEY) || "all";
  } catch (_) {
    return "all";
  }
}

function saveOwner(id) {
  try {
    localStorage.setItem(OWNER_KEY, id);
  } catch (_) { /* ignore */ }
}

async function loadOwners() {
  const el = $("owner-select");
  if (!el) return;
  try {
    const res = await rpc("list_owners");
    ownersList = res.owners || [];
  } catch (_) {
    ownersList = [];
  }
  const cur = readSavedOwner();
  el.innerHTML = ownersList.map((o) => {
    const sel = o.id === cur ? "selected" : "";
    return `<option value="${o.id}" ${sel}>${o.label}</option>`;
  }).join("");
  if (!el.value && ownersList[0]) el.value = ownersList[0].id;
  el.onchange = async () => {
    saveOwner(el.value);
    try {
      await applyOwner(el.value);
    } catch (e) {
      alert(e.message);
    }
  };
}

async function applyOwner(id) {
  const row = ownersList.find((o) => o.id === id);
  if (!row || id === "all") return;
  const part = String(row.default_part || "").toUpperCase();
  const label = row.label || id;
  paintCampaign({
    component: row.default_component,
    part,
    package: row.default_package || "",
    operator: label,
    version: "Version_1",
    model: part,
    year: ($("db-year") && $("db-year").value) || "2026",
  });
  await applyDb();
  log(`Operator ${label}: ${row.default_component} / ${part} / ${label}\n`);
}

function writeOperatorLabel() {
  const id = ($("owner-select") && $("owner-select").value) || readSavedOwner();
  if (!id || id === "all") return "";
  const row = ownersList.find((o) => o.id === id);
  return (row && row.label) || id;
}

function requireWriteOperator() {
  const label = ($("db-operator") && $("db-operator").value) || writeOperatorLabel();
  if (!label || label === "All" || label === "all" || label === "_unassigned") {
    throw new Error("Pick a person operator (not All) before writing folders / DEMO / START");
  }
  return label;
}

let inventoryRows = [];
let categoryRows = [];

async function loadCategories() {
  const el = $("np-category");
  if (!el) return;
  try {
    const res = await rpc("list_categories");
    categoryRows = res.categories || [];
  } catch (_) {
    categoryRows = [];
  }
  el.innerHTML = categoryRows.map((c) => {
    const tag = c.live ? "" : " (stub)";
    return `<option value="${c.id}">${c.run_ic || c.id}${tag}</option>`;
  }).join("");
  el.onchange = async () => {
    const row = categoryRows.find((c) => c.id === el.value);
    if (!row) return;
    const comp = row.component || "";
    if ($("db-component") && comp) {
      const comps = Object.keys(dbTree.components || {});
      if (comps.includes(comp)) $("db-component").value = comp;
    }
    if (row.live && row.family) {
      try {
        await switchFamily(row.family);
      } catch (e) {
        log(`Category family: ${e.message}\n`);
      }
    } else {
      log(`RUN-IC class ${row.run_ic || row.id} is stub -- folders only, no suite.\n`);
    }
  };
}

async function loadInventory() {
  const el = $("inv-select");
  if (!el) return;
  try {
    const res = await rpc("list_inventory");
    inventoryRows = res.parts || [];
  } catch (_) {
    inventoryRows = [];
  }
  el.innerHTML = `<option value="">-- pick a row --</option>` + inventoryRows.map((r, i) => {
    const st = r.status || "";
    const cls = r.category || "";
    return `<option value="${i}">${r.part} · ${cls} · ${st} · ${r.package || ""}</option>`;
  }).join("");
  el.onchange = () => {
    const row = inventoryRows[Number(el.value)];
    if (!row) return;
    if ($("np-category")) {
      // Tracking class vs live suite: Level Shifter RS0204 uses ate_suite=logic
      $("np-category").value = row.ate_suite || row.category || "opamp";
    }
    if ($("np-part")) $("np-part").value = row.part || "";
    if ($("np-package")) $("np-package").value = row.package || "";
    if ($("np-model")) $("np-model").value = row.model || row.part || "";
  };
}

function log(text) {
  const el = $("log");
  if (!el) return;
  el.textContent += text;
  if (el.textContent.length > 80000) {
    el.textContent = el.textContent.slice(-40000);
  }
  el.scrollTop = el.scrollHeight;
}

function setTiles(mapping) {
  document.querySelectorAll(".tile").forEach((t) => {
    const k = t.dataset.k;
    t.classList.toggle("on", !!(mapping && mapping[k]));
    t.classList.toggle("off", !(mapping && mapping[k]));
  });
}

async function loadMappedCoverage() {
  const el = $("setup-map-hint");
  if (!el) return;
  try {
    const c = await rpc("mapped_coverage");
    const miss = c.missing_specs || [];
    const dmm = c.dmm ? "DMM found" : "DMM not in Discover (VOL / Logic IDD need it at run)";
    el.textContent = miss.length
      ? `Map coverage FAIL: ${miss.join(", ")}`
      : `Map coverage OK: ${c.n_map} sheet_map tests registered. ${dmm}`;
  } catch (e) {
    el.textContent = `Map coverage: ${e.message}`;
  }
}

function setRunPill(mode) {
  const el = $("header-bin");
  if (!el) return;
  const map = {
    ready: "READY",
    running: "RUNNING",
    run: "RUN",
    wait: "WAIT",
    pass: "PASS",
    fail: "FAIL",
    stopping: "STOPPING",
  };
  el.textContent = map[mode] || String(mode).toUpperCase();
  el.className = "run-pill " + (mode || "ready");
}

async function syncRunState() {
  try {
    const st = await rpc("session_status");
    if (st.busy || runPollActive) {
      if ($("header-bin")?.classList.contains("stopping")) return;
      setRunPill("running");
    } else if (pendingPrompt) {
      setRunPill("wait");
    } else if ($("header-bin")?.textContent === "STOPPING") {
      setRunPill("ready");
    }
    return st;
  } catch (_) {
    return null;
  }
}

function switchPage(name) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  $(`page-${name}`).classList.add("active");
  document.querySelector(`.tab[data-page="${name}"]`).classList.add("active");
  if (name === "results") loadLayoutPreview().catch(() => {});
}

function selectedDuts() {
  const picked = [...document.querySelectorAll(".dut-cb:checked")].map((c) => Number(c.value));
  if (picked.length) return picked.sort((a, b) => a - b);
  return [Number($("unit").value) || 1];
}

function selectedChannels() {
  const order = ["CHA", "CHB"];
  const picked = [...document.querySelectorAll(".ch-cb:checked")].map((c) => c.value.toUpperCase());
  if (!picked.length) return ["CHA"];
  // Always Channel A pass (all DUTs) before Channel B
  return order.filter((c) => picked.includes(c));
}

let paramCatalog = { tests: {}, gain_profiles: {}, psu_golden: {}, gbw_steps: [], gbw_run_labels: {}, controls: [], sample_size: 4 };

function isManualMode() {
  return $("manual-mode") && $("manual-mode").checked;
}

function condNum(id, fallback) {
  const el = $(`cond-${id}`);
  if (!el) return fallback;
  const n = Number(el.value);
  return Number.isFinite(n) ? n : fallback;
}

function benchValues() {
  const d = mergeTestDefaults(selectedTests());
  if (activeFamily !== "opamp") {
    const out = {
      vcc: condNum("vcc", d.vcc),
      freq_hz: d.freq_hz,
      amp_vpp: d.amp_vpp,
      n_repeats: d.n_repeats,
    };
    const vccb = condNum("vccb", d.vccb);
    if (vccb != null && Number.isFinite(Number(vccb))) out.vccb = Number(vccb);
    if (isManualMode() && $("freq")) {
      out.freq_hz = Number($("freq").value);
      out.amp_vpp = Number($("amp").value);
      out.n_repeats = Number($("repeats").value);
    }
    return out;
  }
  if (isManualMode()) {
    return {
      vcc: Number($("vcc").value),
      freq_hz: Number($("freq").value),
      amp_vpp: Number($("amp").value),
      n_repeats: Number($("repeats").value),
    };
  }
  return {
    vcc: d.vcc,
    freq_hz: d.freq_hz,
    amp_vpp: d.amp_vpp,
    n_repeats: d.n_repeats,
  };
}

function params() {
  const duts = selectedDuts();
  const channels = selectedChannels();
  const bench = benchValues();
  const ids = selectedTests();
  const gbwOn = ids.includes("gbw");
  const profileKey = (gbwOn && $("gain-profile") && $("gain-profile").value) || "default";
  const labels = paramCatalog.gbw_run_labels || {};
  const runLabel = gbwOn
    ? (($("run-label") && $("run-label").value.trim()) || labels[profileKey] || "")
    : "";
  if ($("unit")) $("unit").value = String(duts[0] || 1);
  const out = {
    ...bench,
    unit_index: duts[0],
    dut_indices: duts,
    channels: channels,
    channel: channels[0],
    reset_before_run: $("reset") ? $("reset").checked : false,
    part: (dbContext && dbContext.part_key) || "rs622",
    year: $("db-year").value || undefined,
    run_label: runLabel,
    gain_profile: gbwOn ? profileKey : "default",
    current_limit_a: (paramCatalog.psu_golden && paramCatalog.psu_golden.current_limit_a) || 0.1,
  };
  return out;
}

function selectedTests() {
  return [...document.querySelectorAll(".test-item input:checked")].map((i) => i.value);
}

function mergeTestDefaults(ids) {
  const out = {
    vcc: 5.0,
    freq_hz: 500,
    amp_vpp: 0.004,
    n_repeats: 3,
    channels: ["CHA"],
  };
  const channelUnion = new Set();
  for (const id of ids) {
    const d = paramCatalog.tests[id];
    if (!d) continue;
    Object.assign(out, d);
    if (d.channels) {
      for (const c of d.channels) channelUnion.add(String(c).toUpperCase());
    }
  }
  if (channelUnion.size) {
    out.channels = ["CHA", "CHB"].filter((c) => channelUnion.has(c));
  }
  return out;
}

function applyTestDefaults(force) {
  const ids = selectedTests();
  if (!ids.length) {
    if ($("param-active-hint")) $("param-active-hint").textContent = "Select tests — standard defaults apply.";
    renderRunPlans();
    return;
  }
  const d = mergeTestDefaults(ids);
  if ((force || !isManualMode()) && $("vcc")) {
    $("vcc").value = d.vcc;
    if ($("freq")) $("freq").value = d.freq_hz;
    if ($("amp")) $("amp").value = d.amp_vpp;
    if ($("repeats")) $("repeats").value = d.n_repeats;
    delete $("vcc").dataset.userEdited;
  }
  if (ids.includes("gbw") && d.gain_profile && $("gain-profile")) {
    $("gain-profile").value = d.gain_profile;
    syncGainProfileHint(force);
  }
  const chans = selectedChannels().join("+");
  const manual = isManualMode();
  if ($("param-advanced")) $("param-advanced").classList.toggle("hidden", !manual);
  if ($("param-active-hint")) {
    $("param-active-hint").textContent = manual
      ? `Manual — ${ids.join(", ")} · ${chans}`
      : `${ids.join(", ")} · ${chans} — pick tests / corners above · expand run plan below`;
  }
  renderRunPlans();
}

function fillGainProfiles(rows) {
  const sel = $("gain-profile");
  if (!sel) return;
  sel.innerHTML = (rows || [])
    .map(
      (r) =>
        `<option value="${r.key}">${r.label || r.key} — RF=${r.rf} RI=${r.ri} gain=${r.gain}</option>`
    )
    .join("");
}

function syncGainProfileHint(setLabel) {
  const key = $("gain-profile") && $("gain-profile").value;
  const rows = (paramCatalog.gain_profiles && paramCatalog.gain_profiles.G11) || [];
  const row = rows.find((r) => r.key === key);
  const labels = paramCatalog.gbw_run_labels || {};
  const autoLabel = labels[key] || (row && row.label) || key || "";
  if ($("run-label")) {
    if (setLabel || !$("run-label").dataset.userEdited) {
      $("run-label").value = autoLabel;
    }
  }
  if ($("gbw-plan-title")) {
    $("gbw-plan-title").textContent = autoLabel || "GBW run";
  }
  if (row && $("gain-profile-hint")) {
    $("gain-profile-hint").textContent =
      `RF=${row.rf} RI=${row.ri} gain=${row.gain} — board must match before Continue.`;
  }
  renderRunPlans();
}

function planStepsForTest(t) {
  if (t.fixed_steps && t.fixed_steps.length) return t.fixed_steps;
  if (t.id === "gbw") {
    const steps = paramCatalog.gbw_steps || [];
    if (steps.length) return steps;
  }
  return [{ id: "run", label: "Run / capture", phase: "measure" }];
}

function sortTestsForPlan(tests) {
  const modeRank = new Map(
    (fixtureCatalog || []).map((m, i) => [m.mode, i])
  );
  const within = new Map();
  for (const m of fixtureCatalog || []) {
    (m.tests || []).forEach((id, i) => within.set(id, i));
  }
  return [...tests].sort((a, b) => {
    const ra = modeRank.has(a.fixture_mode) ? modeRank.get(a.fixture_mode) : 99;
    const rb = modeRank.has(b.fixture_mode) ? modeRank.get(b.fixture_mode) : 99;
    if (ra !== rb) return ra - rb;
    const wa = within.has(a.id) ? within.get(a.id) : 99;
    const wb = within.has(b.id) ? within.get(b.id) : 99;
    if (wa !== wb) return wa - wb;
    return String(a.id).localeCompare(String(b.id));
  });
}

function gbwPlanExtrasHtml() {
  const profileKey = ($("gain-profile") && $("gain-profile").value) || "default";
  const rows = (paramCatalog.gain_profiles && paramCatalog.gain_profiles.G11) || [];
  const row = rows.find((r) => r.key === profileKey) || {};
  const runLabel = ($("run-label") && $("run-label").value) || profileKey;
  let opts = rows
    .map(
      (r) =>
        `<option value="${r.key}"${r.key === profileKey ? " selected" : ""}>${r.label || r.key} — RF=${r.rf} RI=${r.ri}</option>`
    )
    .join("");
  if (!opts) {
    opts = `<option value="default" selected>Std G11 — RI=1k RF=10k</option>`;
  }
  const manual = isManualMode();
  const rf = row.rf || "10k";
  const ri = row.ri || "1k";
  return {
    summarySuffix: `G11 locked (RF=${rf} RI=${ri}) · <span id="gbw-plan-title">${runLabel}</span>`,
    bodyPrefix: `
      <input type="hidden" id="run-label" value="${runLabel}" />
      <input type="hidden" id="gain-profile" value="${profileKey}" />
      ${manual ? `<label>Alt network (manual only)
        <select id="gain-profile-manual">${opts}</select>
      </label><p class="hint" id="gain-profile-hint">Must match soldered RF/RI before Continue.</p>` : `<p class="hint" id="gain-profile-hint">Gain 11 locked to G11 board · 50 mVpp @ 1 kHz → sweep to Vout×0.707</p>`}`,
  };
}

function renderOneTestPlan(t, duts, channels) {
  const tag = t.short_tag || t.id;
  const mode = t.fixture_mode || "";
  const instr = (t.required_instruments || []).join("+") || "MSO+PSU+AWG";
  const steps = planStepsForTest(t);
  const dual = t.dual_channel !== false;
  const chans = dual ? channels : [channels[0] || "CHA"];
  let extras = null;
  if (t.id === "gbw") extras = gbwPlanExtrasHtml();
  const summaryCore = extras
    ? `${tag} — ${extras.summarySuffix}`
    : `${tag} — ${t.label} · ${mode} · ${instr}`;
  let html = `<details class="test-plan-details test-plan-collapsible" data-test-id="${t.id}">
    <summary>${summaryCore}</summary>
    <div class="test-plan-body">`;
  if (extras) html += extras.bodyPrefix;
  else if (t.notes) html += `<p class="hint">${t.notes}</p>`;
  for (const ch of chans) {
    const chName = ch === "CHA" ? "Ch A" : ch === "CHB" ? "Ch B" : ch;
    html += `<details class="test-plan-nest">
      <summary>${chName} · all DUTs</summary>
      <div class="test-plan-body">`;
    for (const dut of duts) {
      html += `<details class="test-plan-nest test-plan-nest-dut">
        <summary>DUT ${dut} · ${chName}</summary>
        <div class="test-plan-body"><div class="slew-plan-grid">`;
      for (const step of steps) {
        html += `<div class="slew-step-chip" data-test="${t.id}" data-dut="${dut}" data-ch="${ch}" data-step="${step.id}" data-phase="${step.phase || ""}">${step.label}</div>`;
      }
      html += `</div></div></details>`;
    }
    html += `</div></details>`;
  }
  html += `</div></details>`;
  return html;
}

function renderRunPlans() {
  const box = $("test-plans");
  if (!box) return;
  const ids = selectedTests();
  const picked = sortTestsForPlan(
    ids.map((id) => allTests.find((t) => t.id === id)).filter(Boolean)
  );
  if (!picked.length) {
    box.innerHTML = "";
    return;
  }
  const duts = selectedDuts();
  const channels = selectedChannels();
  box.innerHTML = picked.map((t) => renderOneTestPlan(t, duts, channels)).join("");
  const sel = box.querySelector("#gain-profile-manual");
  if (sel) {
    sel.addEventListener("change", () => {
      const hidden = box.querySelector("#gain-profile");
      if (hidden) hidden.value = sel.value;
      syncGainProfileHint(true);
    });
  }
}

async function loadParamDefaults() {
  try {
    const part = (dbContext && dbContext.part_key) || "rs622";
    paramCatalog = await rpc("list_param_defaults", { part, family: activeFamily });
    if (!paramCatalog.controls) paramCatalog.controls = [];
    renderConditions();
    renderDutPicks();
    applyTestDefaults(false);
  } catch (_) {
    paramCatalog = { tests: {}, gain_profiles: {}, psu_golden: { current_limit_a: 0.1 }, gbw_steps: [], gbw_run_labels: {}, controls: [], sample_size: 4 };
    renderConditions();
  }
}

function renderConditions() {
  const panel = $("panel-run-conditions");
  const box = $("run-conditions");
  if (!panel || !box) return;
  const opamp = activeFamily === "opamp";
  panel.classList.toggle("hidden", opamp);
  if (opamp) {
    box.innerHTML = "";
    return;
  }
  const rows = paramCatalog.controls || [];
  if (!rows.length) {
    box.innerHTML = `<p class="hint">No YAML corners for this part. Tests are still checkboxes below. Add vcc_sweep_list / vcc_sweep or a controls: list in ate/config/parts.</p>`;
    return;
  }
  box.innerHTML = rows.map((c) => {
    const id = `cond-${c.id}`;
    const val = c.value != null ? c.value : "";
    const choices = c.choices || [];
    if (choices.length) {
      const have = new Set(choices.map((x) => String(x)));
      const extra = (val !== "" && !have.has(String(val)))
        ? `<option value="${val}" selected>${val}</option>`
        : "";
      const opts = extra + choices.map((x) => {
        const sel = String(x) === String(val) ? "selected" : "";
        return `<option value="${x}" ${sel}>${x}</option>`;
      }).join("");
      return `<label>${c.label}<select id="${id}">${opts}</select></label>`;
    }
    return `<label>${c.label}<input id="${id}" type="number" step="0.01" value="${val}" /></label>`;
  }).join("");
}

function renderDutPicks() {
  const box = $("dut-picks");
  if (!box) return;
  const n = Math.max(1, Math.min(16, Number(paramCatalog.sample_size) || 4));
  const prev = new Set([...document.querySelectorAll(".dut-cb:checked")].map((c) => String(c.value)));
  if (!prev.size) prev.add("1");
  let html = `<span class="hint">DUTs:</span>`;
  for (let i = 1; i <= n; i += 1) {
    const checked = prev.has(String(i)) ? "checked" : "";
    html += `<label class="check"><input type="checkbox" class="dut-cb" value="${i}" ${checked} /> ${i}</label>`;
  }
  box.innerHTML = html;
}

function kindLabel(kind) {
  if (kind === "dut_change") return "DUT";
  if (kind === "config_change") return "Board";
  if (kind === "channel_change") return "Channel";
  if (kind === "measure") return "Measure";
  return kind || "Operator";
}

function shortGateTitle(promptOrTitle) {
  if (promptOrTitle && typeof promptOrTitle === "object") {
    const tag = String(promptOrTitle.test_tag || "").trim();
    if (tag) return tag.length > 28 ? `${tag.slice(0, 25)}...` : tag;
    promptOrTitle = promptOrTitle.title;
  }
  const t = String(promptOrTitle || "Operator action");
  return t.length > 44 ? `${t.slice(0, 41)}...` : t;
}

function updateGateDock(prompt) {
  const dock = $("gate-dock");
  const bubbles = $("gate-bubbles");
  const btn = $("gate-dock-btn");
  const badge = $("gate-badge");
  if (!dock || !bubbles) return;

  if (prompt && prompt.id) {
    const idx = gateQueue.findIndex((p) => p.id === prompt.id);
    if (idx >= 0) gateQueue[idx] = prompt;
    else gateQueue.push(prompt);
  } else {
    gateQueue = [];
  }

  const waiting = gateQueue.length;
  dock.classList.toggle("has-pending", waiting > 0);
  if (badge) badge.textContent = String(waiting);
  if (btn) btn.classList.toggle("hidden", waiting === 0);

  bubbles.innerHTML = gateQueue
    .map(
      (p) =>
        `<button type="button" class="gate-bubble" data-id="${p.id}" title="${p.title || ""}">
          <span class="gate-bubble-kind">${kindLabel(p.kind)}${p.test_tag ? " · " + p.test_tag : ""}</span>
          <span class="gate-bubble-title">${shortGateTitle(p)}</span>
        </button>`
    )
    .join("");

  bubbles.querySelectorAll(".gate-bubble").forEach((el) => {
    el.onclick = () => {
      const p = gateQueue.find((x) => x.id === el.dataset.id);
      if (p) openOperatorModal(p);
    };
  });
}

function openOperatorModal(payload) {
  pendingPrompt = payload;
  const kind = kindLabel(payload.kind);
  const tag = String(payload.test_tag || "").trim();
  $("modal-kind").textContent = tag ? `${kind} · ${tag}` : kind;
  $("modal-title").textContent = payload.title || "Operator action";
  $("modal-next").textContent = payload.next_hint || "";
  $("modal-list").innerHTML = (payload.checklist || [])
    .map((c) => `<li>${c}</li>`)
    .join("");
  $("modal").classList.remove("hidden");
  setRunPill("wait");
}

function showModal(payload) {
  updateGateDock(payload);
  openOperatorModal(payload);
}

function hideModal() {
  if (pendingPrompt) {
    gateQueue = gateQueue.filter((p) => p.id !== pendingPrompt.id);
    updateGateDock(gateQueue[0] || null);
  }
  pendingPrompt = null;
  $("modal").classList.add("hidden");
}

async function syncPendingGate({ autoOpen = true } = {}) {
  try {
    const p = await rpc("get_pending_prompt");
    if (p) {
      updateGateDock(p);
      if (autoOpen && ($("modal").classList.contains("hidden") || pendingPrompt?.id !== p.id)) {
        openOperatorModal(p);
      }
      return p;
    }
    updateGateDock(null);
    if (pendingPrompt) hideModal();
    return null;
  } catch (_) {
    return null;
  }
}

async function respondContinue() {
  if (!pendingPrompt) {
    const p = await syncPendingGate({ autoOpen: true });
    if (!p) return false;
  }
  await rpc("operator_respond", { prompt_id: pendingPrompt.id, continue: true });
  hideModal();
  return true;
}

function fmtTs(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch (_) {
    return iso;
  }
}

function entryLine(e) {
  const tag =
    e.kind === "dut_change" ? "DUT" :
    e.kind === "config_change" ? "CFG" :
    e.kind === "channel_change" ? "CH" :
    "TEST";
  const ts = e.finished_at || e.started_at;
  const msg = e.message ? ` — ${e.message}` : "";
  const ch = e.channel ? ` · ${e.channel}` : "";
  return `<li class="${e.status}" data-id="${e.id}">
    <span class="ts">${fmtTs(ts)} · ${tag} · ${e.status}</span>
    <strong>${e.label}</strong>${ch}${msg}
  </li>`;
}

function renderStepStatusBar(tl) {
  const bar = $("step-status-bar");
  if (!bar) return;
  const rows = (tl && tl.entries) ? tl.entries : [];
  if (!rows.length) {
    bar.innerHTML = "";
    return;
  }
  bar.innerHTML = rows.map((e) => {
    const st = e.status || "pending";
    const ch = e.channel ? ` [${e.channel}]` : "";
    const msg = e.message ? e.message : (e.next_hint || "");
    return `<div class="step-row ${st}" data-id="${e.id}">
      <span class="step-dot"></span>
      <span class="step-label">${e.label}${ch}</span>
      <span class="step-msg">${st}${msg ? " · " + msg : ""}</span>
    </div>`;
  }).join("");

  // Substeps only while a selected test is actively running
  const runningEntry =
    tl && tl.current && tl.current.status === "running" ? tl.current : null;
  const subTestId = runningEntry && runningEntry.test_id ? runningEntry.test_id : "";
  const subTest = subTestId ? allTests.find((t) => t.id === subTestId) : null;
  if (
    runningEntry &&
    subTest &&
    selectedTests().includes(subTestId) &&
    subTest.fixed_steps &&
    subTest.fixed_steps.length &&
    Object.keys(substepState).length
  ) {
    const subHtml = subTest.fixed_steps.map((s) => {
      const st = substepState[s.id] || "pending";
      return `<div class="step-row ${st}">
        <span class="step-dot"></span>
        <span class="step-label">↳ ${s.label}</span>
        <span class="step-msg">${st}</span>
      </div>`;
    }).join("");
    bar.innerHTML += subHtml;
  }
}

function updateSubstepChip(testId, stepId, status) {
  if (!testId || !selectedTests().includes(testId)) return;
  if (testId !== activeSubstepTestId) {
    substepState = {};
    activeSubstepTestId = testId;
  }
  substepState[stepId] = status;
  document.querySelectorAll(`.slew-step-chip[data-step="${stepId}"]`).forEach((el) => {
    el.classList.remove("done", "running", "pending", "pass", "fail");
    el.classList.add(status);
  });
  if (lastTimeline) renderStepStatusBar(lastTimeline);
}

function renderTimeline(tl) {
  if (!tl || !tl.entries) return;
  lastTimeline = tl;
  const pct = tl.progress_pct || 0;
  $("progress-bar").style.width = `${pct}%`;
  $("progress-meta").textContent =
    `${tl.done_count || 0} / ${tl.total_count || 0} · ${pct}%` +
    (tl.session_id ? ` · ${tl.session_id}` : "");

  const waiting = tl.waiting;
  const next = tl.next;
  const banner = $("next-banner");
  if (waiting) {
    banner.className = "next-banner wait";
    banner.textContent = `WAITING: ${waiting.label}` +
      (waiting.next_hint ? ` → ${waiting.next_hint}` : " — press Continue");
  } else if (tl.current && tl.current.status === "running") {
    banner.className = "next-banner";
    banner.textContent = `RUNNING: ${tl.current.label}` +
      (next ? ` · Next: ${next.label}` : "");
  } else if (next) {
    banner.className = "next-banner";
    banner.textContent = `NEXT: ${next.label}` +
      (next.next_hint ? ` — ${next.next_hint}` : "");
  } else if (tl.finished_at) {
    banner.className = "next-banner";
    banner.textContent = `DONE · finished ${fmtTs(tl.finished_at)}`;
  } else {
    banner.className = "next-banner";
    banner.textContent = "Next: —";
  }

  $("timeline").innerHTML = (tl.entries || []).map(entryLine).join("");
  $("history").innerHTML = (tl.history || []).slice().reverse().map(entryLine).join("");
  renderStepStatusBar(tl);

  const cid = (tl.current || {}).id;
  if (cid && cid !== lastScrollId) {
    lastScrollId = cid;
    const cur = document.querySelector(`#timeline li[data-id="${cid}"]`);
    if (cur) cur.scrollIntoView({ block: "nearest" });
  }
}

function fillSelect(el, values, selected) {
  if (!el) return;
  el.innerHTML = (values || []).map((v) => {
    const sel = v === selected ? "selected" : "";
    return `<option value="${v}" ${sel}>${v}</option>`;
  }).join("");
}

const CAMPAIGN_KEY = "ate_last_campaign";
const CAMPAIGN_BY_FAMILY_KEY = "ate_last_campaign_by_family";
const DEFAULT_CAMPAIGN = {
  component: "OpAmp",
  part: "RS622",
  package: "TTSOP8",
  operator: "Eugene",
  version: "Version_1",
  model: "RS622XK",
  year: "2026",
};

function readSavedCampaign() {
  try {
    const raw = localStorage.getItem(CAMPAIGN_KEY);
    if (!raw) return { ...DEFAULT_CAMPAIGN };
    return { ...DEFAULT_CAMPAIGN, ...JSON.parse(raw) };
  } catch (_) {
    return { ...DEFAULT_CAMPAIGN };
  }
}

function saveCampaign(sel) {
  const payload = {
    component: sel.component || "",
    part: sel.part || "",
    package: sel.package || "",
    operator: sel.operator || "",
    version: sel.version || "",
    model: sel.model || "",
    year: sel.year || "",
  };
  try {
    localStorage.setItem(CAMPAIGN_KEY, JSON.stringify(payload));
  } catch (_) { /* ignore */ }
  try {
    const fam = familyFromComponent(sel.component);
    const all = JSON.parse(localStorage.getItem(CAMPAIGN_BY_FAMILY_KEY) || "{}");
    all[fam] = payload;
    localStorage.setItem(CAMPAIGN_BY_FAMILY_KEY, JSON.stringify(all));
  } catch (_) { /* ignore */ }
}

function readSavedByFamily(family) {
  try {
    const all = JSON.parse(localStorage.getItem(CAMPAIGN_BY_FAMILY_KEY) || "{}");
    const hit = all[family];
    return hit && hit.component ? hit : null;
  } catch (_) {
    return null;
  }
}

function ensureTreeHasCampaign(sel) {
  if (!dbTree.components) dbTree.components = {};
  const c = sel.component || DEFAULT_CAMPAIGN.component;
  const p = sel.part || DEFAULT_CAMPAIGN.part;
  const pkg = sel.package || DEFAULT_CAMPAIGN.package;
  const op = sel.operator || DEFAULT_CAMPAIGN.operator;
  const ver = sel.version || DEFAULT_CAMPAIGN.version;
  if (!dbTree.components[c]) dbTree.components[c] = { parts: {} };
  if (!dbTree.components[c].parts[p]) dbTree.components[c].parts[p] = { packages: {} };
  if (!dbTree.components[c].parts[p].packages[pkg]) {
    dbTree.components[c].parts[p].packages[pkg] = { operators: {} };
  }
  const pkgNode = dbTree.components[c].parts[p].packages[pkg];
  if (!pkgNode.operators) pkgNode.operators = {};
  if (!pkgNode.operators[op]) pkgNode.operators[op] = { versions: [ver] };
  const vers = pkgNode.operators[op].versions || [];
  if (!vers.includes(ver)) vers.push(ver);
  pkgNode.operators[op].versions = vers;
}

function paintCampaign(sel) {
  ensureTreeHasCampaign(sel);
  refreshDbCascades(sel);
  if ($("db-model")) $("db-model").value = sel.model || sel.part || "";
  if (sel.year && $("db-year") && !$("db-year").value) $("db-year").value = sel.year;
  if ($("db-breadcrumb") && sel.component) {
    $("db-breadcrumb").textContent =
      `${sel.component} / ${sel.part} / ${sel.package} / ${sel.operator || "?"} / ${sel.version}` +
      (sel.model ? ` · ${sel.model}` : "");
  }
}

function currentDbSelection() {
  return {
    component: $("db-component").value,
    part: $("db-part").value,
    package: $("db-package").value,
    operator: ($("db-operator") && $("db-operator").value) || "",
    version: $("db-version").value,
    model: $("db-model").value,
    year: $("db-year").value,
  };
}

function refreshDbCascades(preserve) {
  const comps = Object.keys(dbTree.components || {});
  const sel = preserve || currentDbSelection();
  const component = comps.includes(sel.component) ? sel.component : comps[0];
  fillSelect($("db-component"), comps, component);

  const partsObj = (dbTree.components[component] || {}).parts || {};
  const parts = Object.keys(partsObj);
  const part = parts.includes(sel.part) ? sel.part : parts[0];
  fillSelect($("db-part"), parts, part);

  const pkgsObj = (partsObj[part] || {}).packages || {};
  const packages = Object.keys(pkgsObj);
  const pkg = packages.includes(sel.package) ? sel.package : packages[0];
  fillSelect($("db-package"), packages, pkg);

  const opsObj = (pkgsObj[pkg] || {}).operators || {};
  let operators = Object.keys(opsObj);
  // Prefer person labels from owners when tree empty
  if (!operators.length) {
    operators = ownersList.filter((o) => o.id !== "all").map((o) => o.label || o.id);
  }
  const preferOp = sel.operator || writeOperatorLabel();
  const operator = operators.includes(preferOp) ? preferOp : operators[0];
  if ($("db-operator")) fillSelect($("db-operator"), operators, operator);

  const versions = (opsObj[operator] || {}).versions || ["Version_1"];
  const version = versions.includes(sel.version) ? sel.version : versions[0];
  fillSelect($("db-version"), versions, version);
}

function renderDbHints(ctx) {
  dbContext = ctx;
  if (!ctx) return;
  $("db-breadcrumb").textContent =
    `${ctx.component} / ${ctx.part} / ${ctx.package} / ${ctx.operator || "?"} / ${ctx.version} · ${ctx.model}`;
  $("db-model").value = ctx.model || "";
  if (!$("db-year").value && ctx.year) $("db-year").value = ctx.year;
  $("db-path-hint").textContent = `Photos: ${ctx.photo_example}`;
  $("db-excel-hint").textContent = `Lab report: ${ctx.lab_report}`;
  $("results-db-hint").textContent =
    `Lab report: ${ctx.lab_report} · sessions: ${ctx.sessions}`;
  const n = ctx.sample_size || 4;
  $("unit").max = n;
  document.querySelectorAll(".dut-cb").forEach((cb) => {
    const v = Number(cb.value);
    cb.disabled = v > n;
    if (v > n) cb.checked = false;
  });
  refreshTagsUI();
}

async function pollEvents() {
  try {
    const events = await rpc("get_events");
    for (const ev of events || []) {
      if (ev.type === "log") log(ev.payload?.text || "");
      if (ev.type === "timeline") renderTimeline(ev.payload);
      if (ev.type === "progress") {
        if (ev.payload.status === "waiting_operator") {
          setRunPill("wait");
        } else if (ev.payload.status === "running") {
          if (!pendingPrompt) setRunPill("run");
        }
        if (ev.payload.test_id && ev.payload.status === "running" && !ev.payload.substep) {
          if (ev.payload.test_id !== activeSubstepTestId) {
            substepState = {};
            activeSubstepTestId = ev.payload.test_id;
          }
        }
        if (ev.payload.substep && ev.payload.test_id) {
          updateSubstepChip(
            ev.payload.test_id,
            ev.payload.substep,
            ev.payload.status
          );
        }
        if (
          ev.payload.test_id &&
          (ev.payload.status === "pass" || ev.payload.status === "fail")
        ) {
          substepState = {};
          activeSubstepTestId = "";
          if (lastTimeline) renderStepStatusBar(lastTimeline);
        }
      }
      if (ev.type === "operator_prompt") showModal(ev.payload);
    }
    if (runPollActive || pendingPrompt) {
      await syncPendingGate({ autoOpen: true });
      await syncRunState();
    }
  } catch (_) {
    /* worker may be starting */
  }
}

function formatGain(g) {
  if (g === null || g === undefined) return "n/a";
  return String(g);
}

function renderGainBoards(modes) {
  const box = $("gain-boards");
  if (!box) return;
  if (activeFamily !== "opamp") {
    box.innerHTML = "";
    return;
  }
  const list = modes || [];
  const general = list.filter((m) => (m.board_class || "general") === "general" && m.gain != null && m.mode !== "ATE");
  const research = list.filter((m) => m.board_class === "research");
  const chip = (m, kind) => `
      <div class="gain-chip ${kind}" title="RF=${m.rf || "?"} RI=${m.ri || "?"}">
        <strong>${m.mode} → ${formatGain(m.gain)}</strong>
        <span>${m.label || ""} · locked</span>
      </div>`;
  box.innerHTML =
    `<div class="gain-section-label">General testboard</div>` +
    general.map((m) => chip(m, "general")).join("") +
    (research.length
      ? `<div class="gain-section-label">VOS research only (not general board)</div>` +
        research.map((m) => chip(m, "research")).join("")
      : "");
}

async function loadFixtureCatalog() {
  try {
    const part = (dbContext && dbContext.part_key) || "rs622";
    fixtureCatalog = await rpc("list_fixture_modes", { part });
  } catch (_) {
    fixtureCatalog = [];
  }
  renderGainBoards(fixtureCatalog);
}

async function loadDb() {
  dbTree = await rpc("list_db_tree");
  const info = await rpc("get_db_context");
  const ctx = info.context || {};
  const saved = readSavedCampaign();
  const sel = {
    component: ctx.component || saved.component,
    part: ctx.part || saved.part,
    package: ctx.package || saved.package,
    operator: ctx.operator || saved.operator || writeOperatorLabel() || "Eugene",
    version: ctx.version || saved.version,
    model: ctx.model || saved.model,
    year: ctx.year || saved.year || $("db-year")?.value || "2026",
  };
  paintCampaign(sel);
  renderDbHints({ ...saved, ...ctx, ...sel });
  try {
    await applyDb();
  } catch (e) {
    log(`Campaign restore warn: ${e.message}\n`);
  }
  if (info.guide?.orchestration) {
    log("DB guide:\n" + info.guide.orchestration.map((s) => `  ${s}`).join("\n") + "\n");
  }
}

let campaignTags = [];
let campaignBoards = [];
let boardVocab = [];

function renderTagChips(el, tags, { removable = false } = {}) {
  if (!el) return;
  el.innerHTML = "";
  for (const t of tags || []) {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = t;
    if (removable) {
      const x = document.createElement("button");
      x.type = "button";
      x.className = "tag-chip-x";
      x.textContent = "x";
      x.title = "Remove";
      x.onclick = () => {
        campaignTags = campaignTags.filter((v) => v !== t);
        if (t.startsWith("board:")) {
          const b = t.slice(6);
          campaignBoards = campaignBoards.filter((v) => v !== b);
        }
        paintTagsEditor();
      };
      chip.appendChild(x);
    }
    el.appendChild(chip);
  }
  if (!(tags || []).length) {
    const empty = document.createElement("span");
    empty.className = "hint";
    empty.textContent = "none";
    el.appendChild(empty);
  }
}

function paintTagsEditor() {
  renderTagChips($("db-tag-chips"), campaignTags, { removable: false });
  renderTagChips($("tags-editor-chips"), campaignTags, { removable: true });
}

async function refreshTagsUI() {
  try {
    const data = await rpc("list_tags");
    campaignTags = Array.isArray(data.tags) ? data.tags.slice() : [];
    campaignBoards = Array.isArray(data.boards) ? data.boards.slice() : [];
    boardVocab = Array.isArray(data.boards_vocab) ? data.boards_vocab.slice() : [];
    const sel = $("tag-board-select");
    if (sel) fillSelect(sel, boardVocab.length ? boardVocab : ["(no boards.yaml)"], boardVocab[0] || "");
    paintTagsEditor();
    if ($("tags-path-hint")) {
      $("tags-path-hint").textContent =
        `TAGS.txt: ${data.tags_txt || "—"} · yaml: ${data.tags_yaml || "—"}`;
    }
  } catch (e) {
    if ($("tags-path-hint")) $("tags-path-hint").textContent = `Tags: ${e.message}`;
  }
}

async function applyDb() {
  const sel = currentDbSelection();
  const operator = sel.operator || requireWriteOperator();
  const res = await rpc("set_db_context", {
    component: sel.component,
    part: sel.part,
    package: sel.package,
    operator,
    version: sel.version,
    model: sel.model || undefined,
    year: sel.year || undefined,
  });
  renderDbHints(res.context);
  saveCampaign({ ...sel, operator, ...(res.context || {}) });
  log(`Campaign applied: ${res.context.root}\n`);
  if (res.created?.length) {
    log(`Created ${res.created.length} folder(s) under DUT tree\n`);
  }
  if (res.family_error) {
    log(`Family not switched: ${res.family_error}\n`);
  }
  if (res.family) updateFamilyChrome(res.family);
  await loadParamDefaults();
  await loadFixtureCatalog();
  await loadTests();
  await loadMappedCoverage();
  await refreshDetectedPanel();
  await refreshTagsUI();
}

function fillDetectFamilySelect() {
  const el = $("detect-family");
  if (!el) return;
  const fams = (knownFamilies || []).filter((f) => f !== "lim");
  const cur = activeFamily || "logic";
  fillSelect(el, fams.length ? fams : ["opamp", "logic", "switch"], cur);
}

function fillDetectCopyFrom() {
  const el = $("detect-copy-from");
  if (!el) return;
  const sel = currentDbSelection();
  const partsObj = ((dbTree.components || {})[sel.component] || {}).parts || {};
  const parts = Object.keys(partsObj).filter((p) => p !== sel.part);
  const opts = [""].concat(parts);
  el.innerHTML = "";
  opts.forEach((p) => {
    const o = document.createElement("option");
    o.value = p;
    o.textContent = p || "-- same-family part --";
    el.appendChild(o);
  });
}

async function refreshDetectedPanel() {
  const box = $("detected-tests");
  const hint = $("detect-hint");
  if (!box) return;
  fillDetectFamilySelect();
  fillDetectCopyFrom();
  try {
    const res = await rpc("list_detected_tests", { family: activeFamily });
    const rows = res.detected || [];
    box.innerHTML = "";
    if (!rows.length) {
      box.innerHTML = '<p class="hint">No unmatched def test_* (or golden roots missing).</p>';
    } else {
      rows.slice(0, 80).forEach((r) => {
        const div = document.createElement("div");
        div.className = "test-item";
        const blocked = !!r.blocked;
        const status = blocked ? "blocked" : "ready";
        const reason = blocked ? (r.blocked_reason || "blocked") : "wrap-ready";
        const shortFile = String(r.file || "").replace(/\\/g, "/").split("/").slice(-2).join("/");
        div.innerHTML =
          `<label style="display:flex;gap:8px;align-items:flex-start;width:100%">` +
          `<input type="checkbox" class="detect-cb" data-id="${r.id}" data-fn="${r.fn || ""}" ` +
          `data-file="${encodeURIComponent(r.file || "")}" ${blocked ? "disabled" : ""} />` +
          `<span><strong>${r.id}</strong> <span class="hint">(${status})</span><br/>` +
          `<span class="hint">${shortFile}:${r.lineno || "?"} — ${reason}</span></span></label>`;
        box.appendChild(div);
      });
    }
    const missing = (res.roots || []).filter((x) => !x.exists).map((x) => x.label || x.path);
    if (hint) {
      hint.textContent =
        `Scanned ${res.scanned_files || 0} files → ${res.count || 0} unmatched` +
        (res.blocked_count ? ` (${res.blocked_count} blocked)` : "") +
        (missing.length ? `. Missing golden: ${missing.join(", ")}` : ".");
    }
  } catch (e) {
    box.innerHTML = "";
    if (hint) hint.textContent = `Detect scan: ${e.message}`;
  }
}

async function loadTests() {
  const tests = await rpc("list_tests");
  allTests = tests;
  const box = $("test-list");
  box.innerHTML = "";
  if (!tests.length) {
    const stub =
      activeFamily === "level"
        ? "Level family is a stub slot — no characterization suite yet."
          : activeFamily === "logic"
          ? "Logic family loaded — no enabled tests for this part/campaign."
          : (activeFamily === "lim" || activeFamily === "switch")
            ? "Analog Switch family loaded — no enabled tests for this part/campaign."
            : "No tests registered for this family.";
    box.innerHTML = `<p class="hint">${stub}</p>`;
    renderRunPlans();
    return;
  }
  const preferred = new Set();

  const groups = new Map();
  for (const t of tests) {
    const mode = t.fixture_mode || "OTHER";
    if (!groups.has(mode)) groups.set(mode, []);
    groups.get(mode).push(t);
  }

  // Preserve fixture catalog order when known; unknown modes append
  const modeOrder = (fixtureCatalog || []).map((m) => m.mode);
  const modes = [
    ...modeOrder.filter((m) => groups.has(m)),
    ...[...groups.keys()].filter((m) => !modeOrder.includes(m)),
  ];

  for (const mode of modes) {
    const items = groups.get(mode) || [];
    const cat = fixtureCatalog.find((m) => m.mode === mode);
    const isResearch = (cat?.board_class || (mode === "G201" || mode === "G1001" ? "research" : "general")) === "research";
    const gainTxt = cat && cat.gain != null ? ` · gain ${formatGain(cat.gain)}` : "";
    const label = cat?.label || mode;
    const wrap = document.createElement("details");
    wrap.className = "fixture-group" + (isResearch ? " research" : "");
    wrap.open = false;
    wrap.innerHTML = `<summary class="fixture-group-title">${mode}${gainTxt} — ${label}</summary>`;
    const grid = document.createElement("div");
    grid.className = "fixture-group-tests";
    for (const t of items) {
      const id = `t-${t.id}`;
      const checked = !isResearch && preferred.has(t.id) ? "checked" : "";
      const tag = t.short_tag || t.id;
      const instr = (t.required_instruments || []).join("+") || "MSO+PSU+AWG";
      grid.innerHTML += `
        <label class="test-item" for="${id}">
          <input id="${id}" type="checkbox" value="${t.id}" ${checked} />
          <span><strong>${tag}</strong> — ${t.label}<br/><span class="mode-tag">${t.fixture_mode} · ${instr}${isResearch ? " · research" : ""}</span></span>
        </label>`;
    }
    wrap.appendChild(grid);
    box.appendChild(wrap);
  }
  renderRunPlans();
  document.querySelectorAll(".test-item input").forEach((inp) => {
    inp.addEventListener("change", () => {
      renderRunPlans();
      applyTestDefaults(false);
    });
  });
  applyTestDefaults(false);
}

async function refreshSession() {
  try {
    const st = await rpc("session_status");
    sessionOpen = !!st.open;
    setTiles(st.mapping || {});
    $("btn-start").disabled = !sessionOpen;
    $("session-hint").textContent = sessionOpen
      ? `Session open: ${Object.keys(st.mapping || {}).join(", ")}`
      : "Init = Discover → Open Session";
    if (st.db) renderDbHints(st.db);
    if (st.timeline) renderTimeline(st.timeline);
  } catch (e) {
    $("session-hint").textContent = `Worker offline — start ate worker. (${e.message})`;
  }
}

document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => switchPage(t.dataset.page));
});

const familyRail = document.querySelector(".family-rail");
if (familyRail) {
  familyRail.addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".family-btn");
    if (!btn) return;
    const family = btn.dataset.family;
    if (!family) return;
    const dirFam = familyFromComponent(($("db-component") && $("db-component").value) || "");
    if (family === activeFamily && dirFam === family) return;
    try {
      const component = componentFromFamily(family);
      const hasDir = !!(component && (dbTree.components || {})[component]);
      if (hasDir) {
        const last = readSavedByFamily(family);
        const sel = (last && (dbTree.components || {})[last.component])
          ? last
          : firstCampaignInComponent(component);
        if (sel) paintCampaign(sel);
        await applyDb();
      } else {
        await switchFamily(family);
      }
    } catch (e) {
      alert(e.message);
    }
  });
}

["db-component", "db-part", "db-package", "db-operator", "db-version"].forEach((id) => {
  const el = $(id);
  if (!el) return;
  el.addEventListener("change", async () => {
    refreshDbCascades();
    if ((id === "db-component" || id === "db-part") && $("db-model")) {
      $("db-model").value = "";
    }
    // Component change also switches family suite in the same click
    if (id === "db-component") {
      const fam = familyFromComponent(($("db-component") && $("db-component").value) || "");
      if (fam && fam !== activeFamily) {
        try {
          await switchFamily(fam);
        } catch (e) {
          log(`Family switch: ${e.message}\n`);
        }
      }
    }
    try {
      await applyDb();
    } catch (e) {
      alert(e.message);
    }
  });
});

$("btn-apply-db").onclick = async () => {
  try {
    await applyDb();
  } catch (e) {
    alert(e.message);
  }
};

if ($("btn-tag-add-board")) {
  $("btn-tag-add-board").onclick = () => {
    const b = ($("tag-board-select") && $("tag-board-select").value) || "";
    if (!b || b.startsWith("(")) return;
    if (!campaignBoards.includes(b)) campaignBoards.push(b);
    const tok = `board:${b}`;
    if (!campaignTags.includes(tok)) campaignTags.push(tok);
    paintTagsEditor();
  };
}
if ($("btn-tag-add-free")) {
  $("btn-tag-add-free").onclick = () => {
    const t = (($("tag-free") && $("tag-free").value) || "").trim();
    if (!t) return;
    if (!campaignTags.includes(t)) campaignTags.push(t);
    if ($("tag-free")) $("tag-free").value = "";
    paintTagsEditor();
  };
}
if ($("btn-tags-save")) {
  $("btn-tags-save").onclick = async () => {
    try {
      const res = await rpc("save_tags", { tags: campaignTags, boards: campaignBoards });
      campaignTags = res.tags || campaignTags;
      campaignBoards = res.boards || campaignBoards;
      paintTagsEditor();
      if ($("tags-path-hint")) {
        $("tags-path-hint").textContent = `Saved TAGS.txt: ${res.tags_txt}`;
      }
      log(`Tags saved (${(res.tags || []).length})\n`);
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-tags-reload")) {
  $("btn-tags-reload").onclick = () => refreshTagsUI().catch((e) => alert(e.message));
}
if ($("btn-tags-import")) {
  $("btn-tags-import").onclick = async () => {
    try {
      const src = (($("tag-import-root") && $("tag-import-root").value) || "").trim();
      if (!src) {
        alert("Paste a campaign root path");
        return;
      }
      const res = await rpc("import_tags", { from_root: src, merge: true });
      campaignTags = res.tags || [];
      campaignBoards = res.boards || [];
      paintTagsEditor();
      log(`Imported tags from ${src}\n`);
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-tags-filter")) {
  $("btn-tags-filter").onclick = async () => {
    try {
      const tag = (($("tag-filter") && $("tag-filter").value) || "").trim();
      if (!tag) return;
      const res = await rpc("filter_campaigns_by_tag", {
        tag,
        component: ($("db-component") && $("db-component").value) || "",
      });
      const ul = $("tag-filter-results");
      if (!ul) return;
      ul.innerHTML = "";
      for (const c of res.campaigns || []) {
        const li = document.createElement("li");
        li.textContent = `${c.component}/${c.part}/${c.package}/${c.operator}/${c.version}`;
        li.title = c.root;
        ul.appendChild(li);
      }
      if (!(res.campaigns || []).length) {
        const li = document.createElement("li");
        li.textContent = "No campaigns matched";
        ul.appendChild(li);
      }
    } catch (e) {
      alert(e.message);
    }
  };
}

$("btn-open-db").onclick = async () => {
  try {
    await rpc("open_db_root");
  } catch (e) {
    alert(e.message);
  }
};

$("btn-open-sessions").onclick = async () => {
  try {
    await rpc("open_sessions");
  } catch (e) {
    alert(e.message);
  }
};

$("btn-import-xlsx").onclick = async () => {
  try {
    const path = ($("db-xlsx-path") && $("db-xlsx-path").value.trim()) || "";
    const res = await rpc("import_workbook", path ? { source_path: path } : { pick: true });
    if (res.workbook) {
      $("db-excel-hint").textContent = "Lab report: " + res.workbook;
    }
    if (res.context) renderDbHints(res.context);
    log("Imported workbook: " + (res.workbook || "?") + "\n");
    log("sheet_map: " + res.sheet_map_action + " — " + (res.note || "") + "\n");
    if (res.sheets && res.sheets.length) {
      log("Sheets: " + res.sheets.join(", ") + "\n");
    }
  } catch (e) {
    alert(e.message);
  }
};

if ($("btn-import-family")) {
  $("btn-import-family").onclick = async () => {
    try {
      const source = ($("db-family-source") && $("db-family-source").value.trim()) || "";
      const family = ($("db-family-key") && $("db-family-key").value.trim()) || "";
      if (!source) {
        alert("Paste a GitHub URL / owner/repo, or a local family folder.");
        return;
      }
      const res = await rpc("import_family", { source, family });
      renderFamilyRail(res.known || [], res.labels || {});
      if (res.family) {
        log("Imported family: " + res.family + " -> " + (res.dest || "") + "\n");
        log((res.note || "") + "\n");
        if (res.load_error) log("Load warning: " + res.load_error + "\n");
        if (res.copied) log("Copied: " + res.copied.join(", ") + "\n");
      }
      await syncFamilyFromWorker();
      if (res.family && res.family !== "opamp") {
        try { await switchFamily(res.family); } catch (_) { /* stay on current */ }
      }
    } catch (e) {
      alert(e.message);
    }
  };
}

$("btn-discover").onclick = async () => {
  try {
    const m = await rpc("discover");
    setTiles(m);
    log(`Discovered ${JSON.stringify(m)}\n`);
    await loadMappedCoverage();
  } catch (e) {
    alert(e.message);
  }
};

$("btn-open").onclick = async () => {
  try {
    const m = await rpc("open_session");
    setTiles(m);
    sessionOpen = true;
    $("btn-start").disabled = false;
    log(`Session open ${JSON.stringify(m)}\n`);
    const need = ["MSO", "PSU", "AWG"];
    const miss = need.filter((k) => !m[k]);
    if (miss.length) {
      alert(
        `Session open but missing: ${miss.join(", ")}\n\n` +
          "Close Ultra Sigma / other VISA apps, check DP832 USB+power, then Open Session again."
      );
    }
    await refreshSession();
    await loadMappedCoverage();
    if (!m.DMM) {
      log("DMM not in session -- OpAmp VOL and Logic IDD/VOUT/cap_load will fail until Discover finds it\n");
    }
  } catch (e) {
    alert(e.message);
  }
};

$("btn-shot").onclick = async () => {
  try {
    const r = await rpc("screenshot", { test_key: "ORT" });
    log(`Screenshot: ${r.path}\n`);
    alert(`JPEG saved:\n${r.path}`);
  } catch (e) {
    alert(e.message);
  }
};

$("btn-folder").onclick = async () => {
  try {
    const duts = selectedDuts();
    const ids = selectedTests();
    const testKey = ids.includes("slew")
      ? "SlewRate"
      : ids.includes("settling")
        ? "SettlingTime"
        : ids.includes("gbw")
          ? "GBW"
          : "ORT";
    await rpc("open_screenshots", {
      test_key: testKey,
      unit_index: duts[0],
    });
  } catch (e) {
    alert(e.message);
  }
};

if ($("btn-tests-all")) {
  $("btn-tests-all").onclick = () => {
    document.querySelectorAll("#test-list .test-item input").forEach((i) => { i.checked = true; });
    renderRunPlans();
    applyTestDefaults(false);
  };
}
if ($("btn-tests-none")) {
  $("btn-tests-none").onclick = () => {
    document.querySelectorAll("#test-list .test-item input").forEach((i) => { i.checked = false; });
    renderRunPlans();
    applyTestDefaults(false);
  };
}

if ($("btn-new-product")) {
  $("btn-new-product").onclick = async () => {
    const part = ($("np-part") && $("np-part").value.trim()) || "";
    if (!part) return alert("Enter a part number we are testing");
    try {
      const operator = requireWriteOperator();
      const pkg = ($("np-package") && $("np-package").value.trim()) || "SOT23";
      const model = ($("np-model") && $("np-model").value.trim()) || part;
      const res = await rpc("ensure_product", {
        category: $("np-category") && $("np-category").value,
        part,
        package: pkg,
        model,
        operator,
        sample_size: Number($("np-sample") && $("np-sample").value) || 4,
        open_folder: true,
      });
      if ($("np-hint")) $("np-hint").textContent = `${res.note || ""} ${res.root || ""}`;
      log(`New product: ${res.root}\n${res.note || ""}\n`);
      if (res.loaded_family) updateFamilyChrome(res.loaded_family);
      dbTree = await rpc("list_db_tree");
      paintCampaign({
        component: res.component,
        part,
        package: pkg,
        operator: res.operator || operator,
        version: "Version_1",
        model,
        year: ($("db-year") && $("db-year").value) || "2026",
      });
      await applyDb();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-add-version")) {
  $("btn-add-version").onclick = async () => {
    try {
      const operator = requireWriteOperator();
      const sel = currentDbSelection();
      const res = await rpc("ensure_version", {
        component: sel.component,
        part: sel.part,
        package: sel.package,
        operator,
        copy_from_version: sel.version,
        sample_size: Number((dbContext && dbContext.sample_size) || 4),
        open_folder: false,
        apply: true,
      });
      log(`+ Version: ${res.version} → ${res.root}\n`);
      dbTree = await rpc("list_db_tree");
      paintCampaign({
        ...sel,
        operator: res.operator || operator,
        version: res.version,
        model: (dbContext && dbContext.model) || sel.model,
      });
      await applyDb();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-new-session")) {
  $("btn-new-session").onclick = async () => {
    try {
      requireWriteOperator();
      await applyDb();
      const label = ($("session-run-label") && $("session-run-label").value.trim()) || "";
      const res = await rpc("new_run_session", { run_label: label });
      log(`+ Session: ${res.session_id}\n${res.path || ""}\n${res.note || ""}\n`);
      if ($("session-hint")) {
        $("session-hint").textContent =
          `Last run record: ${res.session_id}. Discover → Open Session still required for instruments.`;
      }
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-refresh-detected")) {
  $("btn-refresh-detected").onclick = async () => {
    try {
      await refreshDetectedPanel();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-copy-tests")) {
  $("btn-copy-tests").onclick = async () => {
    try {
      requireWriteOperator();
      const src = ($("detect-copy-from") && $("detect-copy-from").value) || "";
      const dest = ($("db-part") && $("db-part").value) || "";
      if (!src) return alert("Pick a same-family source part");
      if (!dest) return alert("Apply a campaign part first");
      const res = await rpc("enable_tests_on_part", {
        source_part: src,
        dest_part: dest,
      });
      log(`Copy tests ${src} → ${dest}: added ${(res.added || []).join(", ") || "(none new)"}\n`);
      await loadTests();
    } catch (e) {
      alert(e.message);
    }
  };
}

async function wrapSelectedDetected() {
  const fam = ($("detect-family") && $("detect-family").value) || activeFamily || "logic";
  const part = ($("db-part") && $("db-part").value) || "";
  const cbs = Array.from(document.querySelectorAll("#detected-tests .detect-cb:checked"));
  if (!cbs.length) {
    alert("Tick one or more wrap-ready detected tests");
    return;
  }
  for (const cb of cbs) {
    const file = decodeURIComponent(cb.dataset.file || "");
    const fn = cb.dataset.fn || "";
    const id = cb.dataset.id || "";
    const res = await rpc("wrap_detected_test", {
      file,
      fn,
      test_id: id,
      family: fam,
      enable_part: part,
    });
    log(`Wrap ${res.id} → ${res.module} (family ${res.family})\n`);
    if (res.loaded_family) updateFamilyChrome(res.loaded_family);
  }
  await loadTests();
  await refreshDetectedPanel();
}

// Click on detected panel: double-click row or use wrap via refresh button area
if ($("detected-tests")) {
  const wrapBtn = document.createElement("button");
  wrapBtn.type = "button";
  wrapBtn.id = "btn-wrap-detected";
  wrapBtn.className = "btn accent";
  wrapBtn.textContent = "Wrap + enable on part";
  wrapBtn.style.marginTop = "8px";
  wrapBtn.onclick = async () => {
    try {
      requireWriteOperator();
      await wrapSelectedDetected();
    } catch (e) {
      alert(e.message);
    }
  };
  const hint = $("detect-hint");
  if (hint && hint.parentNode) hint.parentNode.insertBefore(wrapBtn, hint);
}

if ($("btn-demo")) {
  $("btn-demo").onclick = async () => {
    try {
      requireWriteOperator();
      await applyDb();
      const res = await rpc("run_demo", { test_ids: selectedTests(), params: params() });
      log(`DEMO: ${res.note || ""}\nSession: ${res.session || ""}\n`);
      (res.steps || []).forEach((s) => {
        const inst = (s.instruments || []).join("+") || "none";
        log(`  ${s.test_id} -> ${inst} ${JSON.stringify(s.mock)}\n`);
      });
      const tb = $("results-table") && $("results-table").querySelector("tbody");
      if (tb) {
        tb.innerHTML = "";
        for (const s of res.steps || []) {
          const inst = (s.instruments || []).join("+") || "none";
          tb.innerHTML += `<tr><td>demo</td><td>${s.test_id}</td><td>true</td><td>mock ${inst}</td></tr>`;
        }
      }
      setRunPill("pass");
      switchPage("results");
    } catch (e) {
      alert(e.message);
    }
  };
}

$("btn-start").onclick = async () => {
  const ids = selectedTests();
  if (!ids.length) return alert("Select at least one test");
  const duts = selectedDuts();
  if (!duts.length) return alert("Select at least one DUT");
  if (!sessionOpen) return alert("Open Session first");
  if (runPollActive) return alert("Run already in progress");
  try {
    requireWriteOperator();
  } catch (e) {
    return alert(e.message);
  }
  try {
    await applyDb();
  } catch (_) {
    /* keep previous campaign if apply fails */
  }
  switchPage("run");
  $("timeline").innerHTML = "";
  $("history").innerHTML = "";
  $("step-status-bar").innerHTML = "";
  substepState = {};
  activeSubstepTestId = "";
  lastScrollId = "";
  gateQueue = [];
  updateGateDock(null);
  $("progress-bar").style.width = "0%";
  $("progress-meta").textContent = "starting…";
  $("next-banner").textContent = "Building plan…";
  setRunPill("running");
  runPollActive = true;
  try {
    await rpc("run_sequence_async", { test_ids: ids, params: params() });
    await waitForRunComplete();
    const results = await rpc("get_last_run_results");
    const tb = $("results-table").querySelector("tbody");
    tb.innerHTML = "";
    let allOk = true;
    for (const r of results || []) {
      allOk = allOk && r.success;
      const ch = r.channel ? ` ${r.channel}` : "";
      tb.innerHTML += `<tr><td>${r.dut ?? ""}${ch}</td><td>${r.test_id}</td><td>${r.success}</td><td>${r.summary || r.error || ""}</td></tr>`;
    }
    try {
      const tl = await rpc("get_timeline");
      if (tl) renderTimeline(tl);
    } catch (_) { /* ignore */ }
    setRunPill(allOk ? "pass" : "fail");
    switchPage("results");
  } catch (e) {
    setRunPill("fail");
    alert(e.message);
  } finally {
    runPollActive = false;
  }
};

async function waitForRunComplete() {
  for (let i = 0; i < 7200; i++) {
    const st = await rpc("session_status");
    if (!st.busy) return;
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("Run timed out waiting for worker");
}

$("btn-stop").onclick = async () => {
  try {
    setRunPill("stopping");
    await rpc("stop");
    runPollActive = false;
    hideModal();
    gateQueue = [];
    updateGateDock(null);
    await syncRunState();
    log("STOP sent — bench safe idle, run cancelled\n");
    setRunPill("ready");
  } catch (e) {
    setRunPill("fail");
    alert(e.message);
  }
};

$("modal-continue").onclick = async () => {
  try {
    await respondContinue();
  } catch (e) {
    alert(e.message);
  }
};

$("modal-abort").onclick = async () => {
  if (!pendingPrompt) return;
  await rpc("operator_respond", { prompt_id: pendingPrompt.id, continue: false });
  hideModal();
};

if ($("gate-dock-btn")) {
  $("gate-dock-btn").onclick = async () => {
    const p = await syncPendingGate({ autoOpen: true });
    if (!p) alert("No pending operator action — test may still be running (check RUN bin).");
  };
}

document.addEventListener("keydown", (e) => {
  if (e.defaultPrevented) return;
  const tag = (e.target && e.target.tagName) || "";
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  if (e.key === "c" || e.key === "C") {
    if (pendingPrompt || gateQueue.length) {
      e.preventDefault();
      respondContinue().catch((err) => alert(err.message));
    }
  }
});

let layoutState = { test_key: "", cells: [] };

function shotUrl(shot) {
  return shot && shot.url ? shot.url : "";
}

function layoutLabel(cell) {
  const pol = cell.polarity ? `${cell.polarity} ` : "";
  return `U${cell.unit} ${pol}${cell.channel || ""}`.trim();
}

function fillLayoutSelect(preview) {
  const sel = $("layout-test");
  if (!sel) return;
  const tests = preview.tests || [];
  const current = preview.test_key || sel.value;
  sel.innerHTML = tests.map((t) => {
    const label = `${t.excel_sheet} (${t.test_key})`;
    const selAttr = t.test_key === current ? " selected" : "";
    return `<option value="${t.test_key}"${selAttr}>${label}</option>`;
  }).join("");
}

function showCompare(cell) {
  const box = $("layout-compare");
  const pair = $("layout-compare-pair");
  const latest = $("layout-img-latest");
  const prev = $("layout-img-prev");
  if (!box || !cell) return;
  $("layout-compare-title").textContent = `${layoutLabel(cell)} @ ${cell.anchor}`;
  if (cell.latest) {
    latest.src = shotUrl(cell.latest);
    latest.alt = cell.latest.name;
  } else {
    latest.removeAttribute("src");
    latest.alt = "no latest";
  }
  if (cell.previous) {
    prev.src = shotUrl(cell.previous);
    prev.alt = cell.previous.name;
    prev.parentElement.style.display = "";
  } else {
    prev.removeAttribute("src");
    prev.alt = "no previous";
    prev.parentElement.style.display = cell.latest ? "none" : "";
  }
  box.classList.remove("hidden");
  if (pair) pair.classList.toggle("overlay", !!($("layout-overlay") && $("layout-overlay").checked));
}

function renderLayoutGrid(preview) {
  const grid = $("layout-grid");
  const src = $("layout-source");
  if (src) src.textContent = preview.hint || preview.source || "";
  if (!grid) return;
  layoutState = { test_key: preview.test_key || "", cells: preview.cells || [] };
  const units = [...new Set(layoutState.cells.map((c) => c.unit).filter(Boolean))].sort((a, b) => a - b);
  if (units.length) grid.style.gridTemplateColumns = `repeat(${Math.min(units.length, 4)}, minmax(0, 1fr))`;
  grid.innerHTML = "";
  layoutState.cells.forEach((cell, idx) => {
    const el = document.createElement("div");
    el.className = "layout-cell";
    el.dataset.idx = String(idx);
    const shot = cell.latest;
    const img = shot
      ? `<img src="${shotUrl(shot)}" alt="${shot.name}" />`
      : `<div class="layout-empty">no shot yet</div>`;
    el.innerHTML = `${img}<div class="layout-meta">${layoutLabel(cell)} · ${cell.n_shots || 0} files</div><input data-raw="${cell.raw}" value="${cell.anchor || ""}" />`;
    el.addEventListener("click", (ev) => {
      if (ev.target.tagName === "INPUT") return;
      grid.querySelectorAll(".layout-cell").forEach((n) => n.classList.remove("active"));
      el.classList.add("active");
      showCompare(cell);
    });
    grid.appendChild(el);
  });
}

async function loadLayoutPreview(testKey) {
  const key = testKey || ($("layout-test") && $("layout-test").value) || "";
  const preview = await rpc("layout_preview", key ? { test_key: key } : {});
  fillLayoutSelect(preview);
  renderLayoutGrid(preview);
  return preview;
}

async function saveLayoutPreview() {
  const grid = $("layout-grid");
  if (!grid || !layoutState.test_key) return;
  const photos = {};
  grid.querySelectorAll("input[data-raw]").forEach((inp) => {
    photos[inp.dataset.raw] = inp.value.trim();
  });
  await rpc("save_photo_layout", { test_key: layoutState.test_key, photos });
  await loadLayoutPreview(layoutState.test_key);
}

function tick() {
  $("clock").textContent = new Date().toLocaleTimeString();
}

function pollLoop() {
  pollEvents().finally(() => {
    const ms = runPollActive || pendingPrompt ? 350 : 900;
    setTimeout(pollLoop, ms);
  });
}

(async function boot() {
  tick();
  setInterval(tick, 1000);
  pollLoop();
  paintCampaign(readSavedCampaign());
  ["vcc", "freq", "amp", "repeats"].forEach((id) => {
    const el = $(id);
    if (el) el.addEventListener("input", () => { el.dataset.userEdited = "1"; });
  });
  if ($("manual-mode")) {
    $("manual-mode").addEventListener("change", () => applyTestDefaults(false));
  }
  document.querySelectorAll(".dut-cb").forEach((inp) => {
    inp.addEventListener("change", renderRunPlans);
  });
  document.querySelectorAll(".ch-cb").forEach((inp) => {
    inp.addEventListener("change", () => {
      inp.dataset.userEdited = "1";
      renderRunPlans();
    });
  });
  if ($("layout-test")) {
    const onLayoutTest = () => {
      loadLayoutPreview($("layout-test").value).catch((e) => alert(e.message));
    };
    $("layout-test").addEventListener("change", onLayoutTest);
    $("layout-test").addEventListener("input", onLayoutTest);
  }
  if ($("btn-layout-reload")) {
    $("btn-layout-reload").onclick = () => loadLayoutPreview($("layout-test") && $("layout-test").value).catch((e) => alert(e.message));
  }
  if ($("btn-layout-save")) {
    $("btn-layout-save").onclick = () => saveLayoutPreview().catch((e) => alert(e.message));
  }
  if ($("layout-overlay")) {
    $("layout-overlay").addEventListener("change", () => {
      const pair = $("layout-compare-pair");
      if (pair) pair.classList.toggle("overlay", $("layout-overlay").checked);
    });
  }
  for (let i = 0; i < 20; i++) {
    try {
      await rpc("ping");
      $("session-hint").textContent = "Worker online — Discover → Open Session";
      await loadDb();
      await loadOwners();
      await loadCategories();
      await loadInventory();
      const ownerId = readSavedOwner();
      if (ownerId && ownerId !== "all") {
        try {
          await applyOwner(ownerId);
        } catch (e) {
          log(`Operator default warn: ${e.message}\n`);
        }
      }
      await syncFamilyFromWorker();
      await loadFixtureCatalog();
      await loadParamDefaults();
      await syncPendingGate({ autoOpen: false });
      const st = await syncRunState();
      if (st && st.busy) {
        runPollActive = true;
        switchPage("run");
        waitForRunComplete()
          .then(() => rpc("get_last_run_results"))
          .then((results) => {
            runPollActive = false;
            if (results && results.length) {
              const tb = $("results-table").querySelector("tbody");
              if (tb) {
                tb.innerHTML = "";
                for (const r of results) {
                  const ch = r.channel ? ` ${r.channel}` : "";
                  tb.innerHTML += `<tr><td>${r.dut ?? ""}${ch}</td><td>${r.test_id}</td><td>${r.success}</td><td>${r.summary || r.error || ""}</td></tr>`;
                }
              }
            }
          })
          .catch(() => { runPollActive = false; });
      }
      await loadTests();
      await refreshSession();
      return;
    } catch (e) {
      if (i === 0) {
        $("session-hint").textContent =
          "Waiting for worker on :8766 — double-click restart_ate_worker.bat";
      }
      if (i === 19) {
        log(`Worker not reachable: ${e.message}\n`);
        $("session-hint").textContent =
          "Worker offline — run restart_ate_worker.bat then Ctrl+F5";
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
  }
})();
