/* Liquid-glass ATE — Test Database + live timeline (DUT / config Continue) */
const RPC = "http://127.0.0.1:8766";
let pendingPrompt = null;
let gateQueue = [];
let gateHeld = false;
let lastActivity = { phase: "idle", text: "", delayS: 0, delayAt: 0 };
let runPollActive = false;
let sessionOpen = false;
let activeFamily = "opamp";
let fixtureCatalog = [];
let dbTree = { components: {} };
let diskPartsByOperator = {};
const PART_SCOPE_KEY = "ate_part_scope";
let detectedCache = [];
let dbContext = null;
let lastTimeline = null;
let lastScrollId = "";
let allTests = [];
let substepState = {};
let activeSubstepTestId = "";

async function rpc(method, params = {}) {
  let last = null;
  for (let i = 0; i < 2; i++) {
    try {
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
    } catch (e) {
      last = e;
      const msg = String((e && e.message) || e);
      if (i === 0 && /fetch|network|Failed/i.test(msg)) {
        await new Promise((r) => setTimeout(r, 400));
        continue;
      }
      throw e;
    }
  }
  throw last;
}

function $(id) { return document.getElementById(id); }

function notice(msg) {
  const text = String(msg || "");
  log(text + (text.endsWith("\n") ? "" : "\n"));
  const bar = $("notice-banner");
  const body = $("notice-banner-text");
  if (body) body.textContent = text;
  if (bar) bar.classList.remove("hidden");
}

function hideNotice() {
  const bar = $("notice-banner");
  if (bar) bar.classList.add("hidden");
}

function setBootSplash(msg) {
  const el = $("boot-splash-msg");
  if (el && msg) el.textContent = msg;
}

function hideBootSplash() {
  const el = $("boot-splash");
  if (el) el.classList.add("hidden");
}

let knownFamilies = ["opamp", "logic", "level", "switch", "power"];
let familyLabels = { opamp: "OpAmp", logic: "Logic", level: "Level", switch: "Analog SW", power: "Power" };
let railType = "opamp";

const FAMILY_UI = {
  opamp: { brand: "OpAmp ATE", kicker: "Operator console" },
  logic: { brand: "Logic ATE", kicker: "Operator console" },
  switch: { brand: "Analog Switch ATE", kicker: "Operator console" },
  lim: { brand: "Analog Switch ATE", kicker: "Operator console" },
  level: { brand: "Level ATE", kicker: "Level Shifters" },
  power: { brand: "Power ATE", kicker: "LDO / Linear Regulator" },
};

function familyMeta(family) {
  if (!family) return { brand: "ATE", kicker: "Stub — no suite yet" };
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
  const builtins = new Set(["opamp", "logic", "level", "switch", "power"]);
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
    if (builtins.has(fam)) {
      const powerBtn = rail.querySelector('.family-btn[data-family="power"]');
      if (powerBtn) rail.insertBefore(btn, powerBtn);
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

function paintPsuWiring() {
  const el = $("psu-wiring-hint");
  if (!el) return;
  const fam = String(activeFamily || "opamp").toLowerCase();
  const lines = {
    opamp:
      "OpAmp: PSU CH1=VDD 2.5 V, CH2=VSS 2.5 V (not 5 V on one banana). Iset=100 mA. OVP=2.8 V, OCP=0.2 A. CH3 OFF. Scope CH1=IN+, CH2=VOUT. AWG CH1=stimulus.",
    logic:
      "Logic: PSU CH1=VCC (often 3.3 V; 5 V only when the test says so). Iset=100 mA. OVP=Vset+0.3 V, OCP=0.2 A. CH2=Vref / CH3=V+ only on VOH/VOL. CIN/CPD: CH1 only. AWG CH1=input.",
    level:
      "Level RS0204: PSU CH1=VCCA, CH2=VCCB (VCCA <= VCCB). Iset=100 mA. OVP=Vset+0.3 V. AWG CH2=OE unless the test ties OE to VCCA.",
    power:
      "LDO: CH1=VIN (IQ: CH1=VOUT bias, CH2=VIN). EN=CH3 5.0 V / 50 mA when Continue lists it. Iset=100 mA (VIN 400 mA on load tests). OVP lamp = armed (Vset+0.3), not a trip unless the output drops. OVP=Vset+0.3 V -- not 6 V.",
    switch:
      "Analog SW: PSU CH1=V+. Iset=100 mA. OVP=Vset+0.3 V. CH2/CH3 only when the Continue list names them.",
    lim:
      "Analog SW: PSU CH1=V+. Iset=100 mA. OVP=Vset+0.3 V. CH2/CH3 only when the Continue list names them.",
  };
  el.textContent = lines[fam] || lines.opamp;
}

function updateFamilyChrome(family) {
  activeFamily = family == null ? "opamp" : family;
  if (activeFamily && activeFamily !== "lim") railType = activeFamily;
  paintBrand(railType);
  paintInventory(railType);
  if ($("np-category")) {
    const catId = typeForFamily(railType);
    if (catId) $("np-category").value = catId;
  }
  const gainPanel = $("panel-gain-boards");
  if (gainPanel) gainPanel.classList.toggle("hidden", activeFamily !== "opamp");
  paintPsuWiring();
  if (!(dbContext && dbContext.probe_channels && dbContext.probe_channels.length)) {
    applyProbeChannels(fallbackProbeChannels());
  }
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
  if (c === "power" || c === "ldo" || c === "linearregulator") return "power";
  const hit = knownFamilies.find((f) => String(f).toLowerCase().replace(/[\s_]/g, "") === c);
  if (hit) return hit;
  if (!c) return "opamp";
  return "";
}

function componentFromFamily(family) {
  const labels = { opamp: "OpAmp", logic: "Logic", switch: "AnalogSwitch", lim: "AnalogSwitch", level: "Level", power: "Power" };
  if (labels[family]) return labels[family];
  const comps = Object.keys(dbTree.components || {});
  return comps.find((c) => c.toLowerCase() === family) || "";
}

function pickLatestVersion(vers) {
  const live = (vers || []).filter(Boolean);
  if (!live.length) return "Version_1";
  let best = live[0];
  let bestN = -1;
  for (const v of live) {
    const m = String(v).match(/Version_(\d+)/i);
    const n = m ? Number(m[1]) : 0;
    if (n >= bestN) {
      bestN = n;
      best = v;
    }
  }
  return best;
}

function syncOwnerSelectFromFolder(label) {
  const el = $("owner-select");
  if (!el || !label) return;
  const want = String(label).trim();
  const row = ownerRowByName(want);
  if (!row || row.id === "all") return;
  if (el.value !== row.id) {
    el.value = row.id;
    saveOwner(row.id);
  }
  syncPersonSkusFromOwner(row.label || want);
}

function campaignKnown(sel) {
  const partsObj = ((dbTree.components || {})[sel.component] || {}).parts || {};
  if (!sel.part || !partsObj[sel.part]) return false;
  const pkgs = (partsObj[sel.part].packages || {});
  if (!sel.package || !pkgs[sel.package]) return false;
  const ops = (pkgs[sel.package].operators || {});
  if (!sel.operator || sel.operator === "_unassigned" || !ops[sel.operator]) return false;
  return !!(sel.version && (ops[sel.operator].versions || []).includes(sel.version));
}

function pickLiveOperator(operators, prefer) {
  const list = Array.isArray(operators)
    ? operators.filter((o) => o && o !== "_unassigned" && !hiddenOperatorName(o))
    : [];
  const live = list.filter((o) => o !== "_unassigned");
  if (prefer && !hiddenOperatorName(prefer) && live.includes(prefer)) return prefer;
  if (live.length) return live[0];
  return "";
}

function firstCampaignInComponent(component) {
  const partsObj = ((dbTree.components || {})[component] || {}).parts || {};
  const parts = liveKeys(partsObj);
  if (!parts.length) return null;
  const part = parts[0];
  const pkgsObj = (partsObj[part] || {}).packages || {};
  const packages = liveKeys(pkgsObj);
  const pkg = packages[0] || "";
  const opsObj = (pkgsObj[pkg] || {}).operators || {};
  const operators = Object.keys(opsObj).filter((k) => k && !k.startsWith(".") && k !== "_unassigned");
  const prefer = writeOperatorLabel();
  const op = pickLiveOperator(operators, prefer);
  const versions = (opsObj[op] || {}).versions || [];
  return {
    component,
    part,
    package: pkg,
    operator: op,
    version: pickLatestVersion(versions),
    model: "",
    year: ($("db-year") && $("db-year").value) || "2026",
  };
}

const OWNER_KEY = "ate_operator";
const FIRST_RUN_ADD = "+ Add Your Name";
let firstRunPicked = new Set();
let ownersList = [];
let personSkuCodes = [];
const PERSON_CANON = {
  lim: "SeeLim",
  seelim: "SeeLim",
  ariff: "Ariff",
  eugene: "Eugene",
  changthong: "ChangTong",
  changtong: "ChangTong",
  soo: "Soo",
  chuntak: "Chun Tak",
  chuntat: "Chun Tak",
};

function personFold(s) {
  return String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function displayPerson(name) {
  const raw = String(name || "").trim();
  if (!raw) return "";
  return PERSON_CANON[personFold(raw)] || raw;
}

function ownerRowByName(raw) {
  const want = personFold(String(raw || "").replace(/\s*\(observe\)\s*$/i, ""));
  if (!want) return null;
  const row = (ownersList || []).find((o) => {
    if (!o) return false;
    return personFold(o.id) === want
      || personFold(o.label) === want
      || personFold(displayPerson(o.label || o.id)) === want;
  });
  if (!row) return null;
  if (row.alias_of) {
    return (ownersList || []).find((o) => o && o.id === row.alias_of) || row;
  }
  return row;
}

function readSavedOwner() {
  try {
    return localStorage.getItem(OWNER_KEY) || "";
  } catch (_) {
    return "";
  }
}

function saveOwner(id) {
  try {
    localStorage.setItem(OWNER_KEY, id);
  } catch (_) { /* ignore */ }
}

function ownerIsObserver(id) {
  const s = String(id || "").toLowerCase();
  if (!s || s === "all" || s === "kevin" || s === "ate") return true;
  const row = ownerRowByName(id) || ownersList.find((o) => o.id === id || String(o.label || "").toLowerCase() === s);
  if (!row) return false;
  const lab = String(row.label || "").toLowerCase();
  return String(row.role || "").toLowerCase() === "observer"
    || String(row.id || "").toLowerCase() === "kevin"
    || String(row.id || "").toLowerCase() === "ate"
    || lab === "kevin"
    || lab === "ate";
}

function hiddenOperatorName(name) {
  const s = String(name || "").trim().toLowerCase();
  return !s || s === "all" || s === "kevin" || s === "ate" || s === "_unassigned";
}

function hiddenOwnerRow(o) {
  if (!o) return true;
  if (o.alias_of) return true;
  if (String(o.id || "") === "all") return false;
  return hiddenOperatorName(o.id) || hiddenOperatorName(o.label) || ownerIsObserver(o.id);
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
  let cur = readSavedOwner();
  const aliasRow = ownersList.find((o) => o && o.id === cur && o.alias_of);
  if (aliasRow && aliasRow.alias_of) {
    cur = aliasRow.alias_of;
    saveOwner(cur);
  }
  el.innerHTML = ownersList.filter((o) => o && (o.id === "all" || !hiddenOwnerRow(o))).map((o) => {
    const sel = o.id === cur ? "selected" : "";
    return `<option value="${o.id}" ${sel}>${displayPerson(o.label || o.id)}</option>`;
  }).join("");
  if (cur && !hiddenOwnerRow(ownersList.find((o) => o.id === cur) || { id: cur, label: cur })) {
    el.value = cur;
  } else if (cur && (cur === "all" || (ownersList.find((o) => o.id === cur) || {}).id === "all")) {
    el.value = "all";
  } else {
    const first = ownersList.find((o) => o && o.id !== "all" && !hiddenOwnerRow(o));
    if (first) {
      el.value = first.id;
      saveOwner(first.id);
    }
  }
  el.onchange = async () => {
    saveOwner(el.value);
    try {
      await applyOwner(el.value);
    } catch (e) {
      alert(e.message);
    }
  };
  const curRow = ownersList.find((o) => o.id === el.value);
  if (curRow && !ownerIsObserver(curRow.id)) {
    syncPersonSkusFromOwner(curRow.label || curRow.id);
  } else {
    personSkuCodes = [];
    paintPersonSkuChips();
  }
  paintSettingsPcHint();
  paintPartScopeHint();
}

function sameOperator(a, b) {
  return String(a || "").trim().toLowerCase() === String(b || "").trim().toLowerCase();
}

async function applyOwner(id) {
  const row = ownersList.find((o) => o.id === id);
  if (!row || ownerIsObserver(id)) return;
  syncPersonSkusFromOwner(row.label || id);
  const label = row.label || id;
  const last = readSavedCampaignForOwner(id);
  if (last && last.part) {
    paintCampaign({
      ...last,
      operator: label,
      year: last.year || ($("db-year") && $("db-year").value) || "2026",
    });
    await applyDb();
    log(`Operator ${label}: ${last.component} / ${last.part} / ${label}\n`);
    return;
  }
  const part = String(row.default_part || "").toUpperCase();
  let pkg = row.default_package || "";
  const inv = (inventoryRows || []).find((r) => String(r.part || "").toUpperCase() === part);
  const partsObj = ((dbTree.components || {})[row.default_component] || {}).parts || {};
  const pkgsObj = (partsObj[part] || {}).packages || {};
  const diskPkgs = liveKeys(pkgsObj).filter((p) => {
    const ops = (pkgsObj[p] || {}).operators || {};
    return ops[label];
  });
  if (diskPkgs.length) {
    if (!diskPkgs.includes(pkg)) pkg = diskPkgs[0];
  } else if (inv && inv.package) {
    pkg = inv.package;
  }
  const vers = versionsForSel({
    component: row.default_component,
    part,
    package: pkg,
    operator: label,
  });
  paintCampaign({
    component: row.default_component,
    part,
    package: pkg,
    operator: label,
    version: pickLatestVersion(vers),
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
  const header = ($("owner-select") && $("owner-select").value) || "";
  if (ownerIsObserver(header) || header === "all") {
    throw new Error("Pick a person (not All / Kevin / ATE) before writing folders / DEMO / START");
  }
  const label = ($("db-operator") && $("db-operator").value) || writeOperatorLabel();
  if (!label || ownerIsObserver(label) || hiddenOperatorName(label) || label === "All" || label === "all" || label === "_unassigned") {
    throw new Error("Pick a person (not All / Kevin / ATE) before writing folders / DEMO / START");
  }
  return label;
}

let inventoryRows = [];
let categoryRows = [];
let campaignLabels = [];
let labelKindVocab = [];
let labelValueVocab = {};

function typeForFamily(family) {
  if (family === "switch" || family === "lim") return "analog_switch";
  return family || "";
}

function suiteForRow(row) {
  const suite = String((row && row.ate_suite) || "").trim();
  if (suite) return suite;
  const cat = categoryRows.find((c) => c.id === ((row && row.category) || ""));
  if (cat && cat.live && cat.family) return cat.family;
  return "";
}

function paintInventory(type) {
  const el = $("inv-select");
  if (!el) return;
  const want = typeForFamily(type || railType);
  const rows = inventoryRows.map((r, i) => ({ r, i })).filter(({ r }) => {
    if (!want) return true;
    return String(r.category || "") === want;
  });
  const nice = familyLabels[type || railType] || type || railType || "SKU";
  el.innerHTML = `<option value="">-- pick a ${nice} --</option>` + rows.map(({ r, i }) => {
    const st = r.status || "";
    const lot = r.lot || "";
    const klass = r.sheet_class || r.category || "";
    const bits = [r.part, klass, r.model || "", r.package || "", lot, st].filter(Boolean);
    return `<option value="${i}">${bits.join(" · ")}</option>`;
  }).join("");
  const hint = $("inv-type-hint");
  if (hint) {
    hint.textContent = `${rows.length} ${nice} SKU(s) on the tracking sheet.`;
  }
}

async function loadCategories() {
  try {
    const res = await rpc("list_categories");
    categoryRows = res.categories || [];
  } catch (_) {
    categoryRows = [];
  }
  const html = categoryRows.map((c) => {
    const tag = c.live ? "" : " (stub)";
    return `<option value="${c.id}">${c.run_ic || c.id}${tag}</option>`;
  }).join("");
  const el = $("np-category");
  if (el) {
    el.innerHTML = html;
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
          railType = row.family === "switch" ? "switch" : (row.id === "analog_switch" ? "switch" : (row.family || railType));
          paintInventory(railType);
          await switchFamily(row.family);
        } catch (e) {
          log(`Category family: ${e.message}\n`);
        }
      } else {
        log(`RUN-IC class ${row.run_ic || row.id} is stub -- folders only, no suite.\n`);
      }
    };
  }
  if ($("board-class")) $("board-class").innerHTML = html;
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
  paintInventory(railType);
  refreshPersonSkuCombo();
  el.onchange = () => {
    const row = inventoryRows[Number(el.value)];
    if (!row) return;
    if ($("np-category")) {
      // Tracking-sheet class only. ate_suite must not steal Level Shifters -> Logic.
      $("np-category").value = row.category || "opamp";
    }
    if ($("np-part")) $("np-part").value = row.part || "";
    if ($("np-package")) $("np-package").value = row.package || "";
    if ($("np-model")) $("np-model").value = row.model || row.part || "";
    const qty = Number(row.qty);
    if ($("np-sample") && Number.isFinite(qty) && qty >= 1) {
      $("np-sample").value = String(Math.trunc(qty));
    }
    const suite = String(row.ate_suite || "").trim();
    const cat = categoryRows.find((c) => c.id === (row.category || ""));
    if (suite) {
      log(`Tracking class: ${row.sheet_class || row.category}. Live suite: ${suite}.\n`);
      switchFamily(suite).catch((e) => log(`ate_suite: ${e.message}\n`));
    } else if (cat && cat.live && cat.family) {
      switchFamily(cat.family).catch((e) => log(`Category family: ${e.message}\n`));
    } else if (cat) {
      log(`RUN-IC class ${cat.run_ic || cat.id} is stub -- folders only, no suite.\n`);
    }
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

function selectedInstrumentNeed() {
  const need = new Set();
  const ids = selectedTests();
  for (const id of ids) {
    const t = (allTests || []).find((x) => x.id === id);
    for (const k of (t && t.required_instruments) || []) {
      need.add(String(k).toUpperCase());
    }
  }
  return need;
}

function paintTileNeeds() {
  const need = selectedInstrumentNeed();
  document.querySelectorAll(".tile").forEach((t) => {
    const k = String(t.dataset.k || "").toUpperCase();
    const connected = t.classList.contains("on") || t.classList.contains("sim");
    t.classList.toggle("idle", need.size > 0 && !need.has(k) && !connected);
  });
  const hint = $("run-need-hint");
  if (!hint) return;
  if (!need.size) {
    hint.textContent = "Tick tests. START runs only those ids. IOZ = PSU+DMM. Green = USB on the bus.";
    return;
  }
  hint.textContent = "This START: " + [...need].join("+") + ". Other green tiles stay connected (unused, not off).";
}

function tileMapFromStatus(st) {
  if (!st) return {};
  if (st.sim) return st.mapping || {};
  return Object.assign({}, st.pnp || {}, st.usb || {}, st.mapping || {});
}

function testNeedsAwg(t) {
  return (t.required_instruments || []).includes("AWG");
}

function stimPrefix(t) {
  const stim = (t.stimulus && t.stimulus.wave) ? String(t.stimulus.wave).toUpperCase() : "";
  if (!stim) return "";
  if (testNeedsAwg(t) || ["SQU", "SIN", "PULS", "RAMP", "NOIS"].includes(stim)) {
    return "AWG " + stim;
  }
  return stim;
}

function setTiles(mapping) {
  const sim = Object.values(mapping || {}).some((v) =>
    String(v).toUpperCase().startsWith("SIM::")
  );
  document.querySelectorAll(".tile").forEach((t) => {
    const k = t.dataset.k;
    const on = !!(mapping && mapping[k]);
    t.classList.toggle("on", on && !sim);
    t.classList.toggle("sim", on && sim);
    t.classList.toggle("off", !on);
  });
  paintTileNeeds();
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
      : (!c.n_map
        ? `Map coverage empty: no sheet_map tests at ${c.sheet_map || "this campaign"}. ${dmm}`
        : `Map coverage OK: ${c.n_map} sheet_map tests registered. ${dmm}`);
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
    if ($("header-bin")?.classList.contains("stopping")) return st;
    if (pendingPrompt) {
      setRunPill("wait");
      return st;
    }
    if (st.busy) {
      setRunPill("running");
    } else {
      const cur = ($("header-bin")?.textContent || "").toUpperCase();
      if (cur === "STOPPING" || cur === "WAIT" || cur === "RUNNING" || cur === "RUN") {
        if (!runPollActive || cur === "WAIT" || cur === "STOPPING") setRunPill("ready");
      }
    }
    return st;
  } catch (_) {
    return null;
  }
}

function switchPage(name) {
  const page = $(`page-${name}`);
  const tab = document.querySelector(`.tab[data-page="${name}"]`);
  if (!page || !tab) return;
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  page.classList.add("active");
  tab.classList.add("active");
  if (pendingPrompt && name !== "run") {
    dismissOperatorModal();
  }
  if (name === "results") {
    loadLayoutPreview().catch(() => {});
    loadRunLedger().catch(() => {});
    loadProgressBoard().catch(() => {});
  }
  if (name === "detect") {
    refreshCampaignTests().catch(() => {});
    refreshDetectedPanel({ preserveWrap: true }).catch(() => {});
  }
  if (name === "recipe") {
    ensureRecipeCanvas();
    refreshRecipeList().catch(() => {});
  }
  if (name === "settings") {
    paintSettingsPcHint();
  }
  paintRunStrip();
}

function selectedDuts() {
  const picked = [...document.querySelectorAll(".dut-cb:checked")].map((c) => Number(c.value));
  if (picked.length) return picked.sort((a, b) => a - b);
  return [Number($("unit").value) || 1];
}

const PROBE_CH_LETTERS = "ABCDEFGH";

function probeChannelIds() {
  return PROBE_CH_LETTERS.split("").map((L) => "CH" + L);
}

function channelLetter(ch) {
  const id = String(ch || "CHA").toUpperCase();
  return id.replace(/^CH/, "") || "A";
}

function channelPromptLabel(ch) {
  return "Channel " + channelLetter(ch);
}

function selectedChannels() {
  const order = probeChannelIds();
  const boxes = [...document.querySelectorAll(".ch-cb")];
  const picked = boxes
    .filter((c) => c.checked && !c.disabled)
    .map((c) => String(c.value || "").toUpperCase());
  const ordered = order.filter((c) => picked.includes(c));
  if (ordered.length) return ordered;
  const firstOn = boxes.find((c) => !c.disabled);
  return [firstOn ? String(firstOn.value || "CHA").toUpperCase() : "CHA"];
}

function fallbackProbeChannels() {
  const fam = String(activeFamily || railType || "").toLowerCase();
  if (fam === "opamp") return ["CHA", "CHB"];
  return ["CHA"];
}

function nextProbeChannel(have) {
  const haveSet = new Set((have || []).map((c) => String(c).toUpperCase()));
  return probeChannelIds().find((id) => !haveSet.has(id)) || "";
}

function bindChannelPickEvents() {
  document.querySelectorAll(".ch-cb").forEach((inp) => {
    inp.addEventListener("change", () => {
      inp.dataset.userEdited = "1";
      const lab = inp.closest("label");
      if (lab) lab.classList.toggle("off", !inp.checked);
      paintWalkOrderLabels();
      paintWalkHint(selectedWalkOrder());
      renderRunPlans();
      persistRunPrefs().catch(() => {});
    });
  });
  document.querySelectorAll(".ch-chip-x").forEach((btn) => {
    btn.onclick = () => {
      const id = String(btn.dataset.ch || "").toUpperCase();
      const keep = selectedChannels().filter((c) => c !== id);
      if (!keep.length) return;
      applyProbeChannels(keep, { force: true });
      persistRunPrefs().catch(() => {});
    };
  });
  if ($("btn-add-channel")) {
    $("btn-add-channel").onclick = () => {
      const have = [...document.querySelectorAll(".ch-cb")].map((c) =>
        String(c.value || "").toUpperCase()
      );
      const nxt = nextProbeChannel(have);
      if (!nxt) return;
      const next = probeChannelIds().filter((c) => have.includes(c) || c === nxt);
      const keepOn = selectedChannels().concat([nxt]);
      applyProbeChannels(next, { force: true, checked: keepOn });
      persistRunPrefs().catch(() => {});
    };
  }
}

function applyProbeChannels(list, opts) {
  const force = !!(opts && opts.force);
  const want = (list && list.length ? list : fallbackProbeChannels()).map((c) =>
    String(c || "").toUpperCase()
  );
  const slots = probeChannelIds().filter((c) => want.includes(c));
  const live = slots.length ? slots : ["CHA"];
  const box = $("channel-picks");
  if (box) {
    const canDrop = live.length > 1;
    const canAdd = !!nextProbeChannel(live);
    box.innerHTML =
      `<span class="hint">Channels:</span>` +
      live
        .map((id) => {
          const L = channelLetter(id);
          const on = force && opts.checked
            ? (opts.checked || []).map((c) => String(c).toUpperCase()).includes(id)
            : true;
          const x = canDrop
            ? `<button type="button" class="ch-chip-x" data-ch="${id}" aria-label="Remove ${L}">x</button>`
            : "";
          return `<label class="check ch-chip${on ? "" : " off"}"><input type="checkbox" class="ch-cb" value="${id}" ${on ? "checked" : ""} /> ${L}${x}</label>`;
        })
        .join("") +
      (canAdd
        ? `<button type="button" class="btn ghost btn-compact" id="btn-add-channel" title="Add next probe channel">+</button>`
        : "");
    bindChannelPickEvents();
  }
  if (!force) {
    document.querySelectorAll(".ch-cb").forEach((cb) => {
      if (cb.dataset.userEdited === "1") return;
      cb.checked = true;
    });
  }
  const hint = $("channel-hint");
  if (hint) {
    const names = live.map(channelLetter).join(", ");
    hint.textContent = live.length === 1
      ? `Probe ${names} only. + adds another channel. Saved on this Version.`
      : `Tick ${names} for this run. + adds another. x removes. Saved on this Version.`;
  }
  paintWalkOrderLabels();
  paintWalkHint(selectedWalkOrder());
}

function selectedWalkOrder() {
  const el = $("walk-order");
  let raw = el ? String(el.value || "") : "";
  if (!raw) {
    try { raw = localStorage.getItem("ate.walkOrder") || ""; } catch (e) { raw = ""; }
  }
  return String(raw).toLowerCase().startsWith("dut") ? "dut" : "channel";
}

function walkChannelPhrase() {
  const letters = selectedChannels().map(channelLetter);
  if (!letters.length) return "A";
  if (letters.length === 1) return letters[0];
  return letters.slice(0, -1).join(", ") + " then " + letters[letters.length - 1];
}

function paintWalkOrderLabels() {
  const el = $("walk-order");
  if (!el) return;
  const v = selectedWalkOrder();
  const phrase = walkChannelPhrase();
  const n = selectedChannels().length;
  const chText = n <= 1
    ? `Channel first (${phrase} all DUTs)`
    : `Channel first (${selectedChannels().map(channelLetter)[0]} all DUTs, then ${selectedChannels().slice(1).map(channelLetter).join(", then ")})`;
  const dutText = n <= 1
    ? `DUT first (this socket ${phrase}, next DUT)`
    : `DUT first (this socket ${phrase}, next DUT)`;
  const chOpt = el.querySelector('option[value="channel"]');
  const dutOpt = el.querySelector('option[value="dut"]');
  if (chOpt) chOpt.textContent = chText;
  if (dutOpt) dutOpt.textContent = dutText;
  el.value = v;
}

function paintWalkHint(walk) {
  const hint = $("param-active-hint");
  if (!hint) return;
  const letters = selectedChannels().map(channelLetter);
  const n = letters.length;
  if (n <= 1) {
    const L = letters[0] || "A";
    hint.textContent = walk === "dut"
      ? `Order: same board -> this DUT on ${L} -> next DUT -> next category. Saved on this campaign.`
      : `Order: same board -> all DUTs on ${L} -> next category. Saved on this campaign.`;
    return;
  }
  hint.textContent = walk === "dut"
    ? `Order: same board -> this DUT ${walkChannelPhrase()} -> next DUT -> next category. Saved on this campaign.`
    : `Order: same board -> all DUTs on each of ${walkChannelPhrase()} -> next category. Saved on this campaign.`;
}

function applyWalkOrder(raw) {
  const v = String(raw || "channel").toLowerCase().startsWith("dut") ? "dut" : "channel";
  const el = $("walk-order");
  if (el) el.value = v;
  try { localStorage.setItem("ate.walkOrder", v); } catch (e) {}
  paintWalkOrderLabels();
  paintWalkHint(v);
}

async function persistRunPrefs() {
  const v = selectedWalkOrder();
  applyWalkOrder(v);
  renderRunPlans();
  try {
    await rpc("set_run_prefs", {
      walk_order: v,
      sample_size: currentDutCount(),
      probe_channels: selectedChannels(),
    });
  } catch (e) {}
}

async function persistWalkOrder() {
  await persistRunPrefs();
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

function catalogControlValues() {
  const extra = {};
  for (const c of paramCatalog.controls || []) {
    const id = c && c.id;
    if (!id) continue;
    const el = $(`cond-${id}`);
    if (!el) continue;
    const raw = el.value;
    if (raw === "" || raw == null) continue;
    const n = Number(raw);
    extra[id] = Number.isFinite(n) && String(raw).trim() !== "" && !/^[a-zA-Z]/.test(String(raw))
      ? n
      : raw;
  }
  return extra;
}

function testItemRoot(tid) {
  return document.querySelector(`#test-list .test-item[data-test-id="${tid}"]`);
}

function collectOneTestParams(tid) {
  const root = testItemRoot(tid);
  const out = {};
  if (!root) return out;
  root.querySelectorAll("[data-param]").forEach((el) => {
    const key = el.getAttribute("data-param");
    if (!key) return;
    if (el.type === "checkbox") {
      out[key] = el.checked ? 1 : 0;
      return;
    }
    if (el.value === "") return;
    if (key === "vcc_list" || key === "levels" || key === "rails_psu" || key === "rails_mode" || key === "icc_vcc_mode" || key === "vcc_mode" || key === "icc_vcc_list" || key === "screenshot_from" || key === "ioff_start") {
      out[key] = String(el.value).trim();
      return;
    }
    const n = Number(el.value);
    out[key] = Number.isFinite(n) ? n : el.value;
  });
  if (out.vcc_list) {
    out.vcc_list = String(out.vcc_list).split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
  }
  if (out.icc_vcc_list) {
    out.icc_vcc_list = String(out.icc_vcc_list).split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
  }
  if (tid === "icc" && out.vcc_mode && !out.icc_vcc_mode) out.icc_vcc_mode = out.vcc_mode;
  if (tid === "icc" && out.icc_vcc_mode && !out.vcc_mode) out.vcc_mode = out.icc_vcc_mode;
  if (out.levels) {
    out.levels = String(out.levels).split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
  }
  if (out.rails_mode || out.rails_psu) {
    out.rails_mode = out.rails_mode || "";
    out.rails_psu = out.rails_psu || "";
  }
  const specs = [];
  root.querySelectorAll(".spec-edit[data-spec-id]").forEach((wrap) => {
    const sid = wrap.getAttribute("data-spec-id");
    if (!sid) return;
    const row = { id: sid };
    wrap.querySelectorAll("[data-spec-field]").forEach((el) => {
      const field = el.getAttribute("data-spec-field");
      if (!field || el.value === "") return;
      if (field === "unit") {
        row.unit = el.value;
        return;
      }
      const n = Number(el.value);
      if (Number.isFinite(n)) row[field] = n;
    });
    specs.push(row);
  });
  if (specs.length) out.specs = specs;
  return out;
}

function collectTestParamMap(ids) {
  const out = {};
  for (const id of ids || []) {
    const block = collectOneTestParams(id);
    if (Object.keys(block).length) out[id] = block;
  }
  return out;
}

async function writeTestParams(tid) {
  const operator = requireWriteOperator();
  const sel = currentDbSelection();
  const block = collectOneTestParams(tid);
  const wrote = await rpc("set_test_params", {
    test_id: tid,
    params: block,
    component: sel.component,
    part: sel.part,
    package: sel.package,
    operator,
    version: sel.version,
    model: sel.model || undefined,
    year: sel.year || undefined,
  });
  const root = (wrote && wrote.root) || "";
  log(`Wrote ${tid} parameters to this Version (_manifest/test_params.yaml)\n` + (root ? `  ${root}\n` : ""));
}

function sweepValues() {
  const ids = selectedTests();
  for (const id of ids) {
    const t = (typeof allTests !== "undefined" ? allTests : []).find((row) => row.id === id) || { id };
    const meta = testSweepMeta(t);
    const block = collectOneTestParams(id);
    if (!meta.kind && block.vcc_start == null && block.freq_start == null) continue;
    return {
      vcc_start: Number.isFinite(Number(block.vcc_start)) ? Number(block.vcc_start) : 0,
      vcc_stop: Number.isFinite(Number(block.vcc_stop)) ? Number(block.vcc_stop) : 5,
      vcc_step: Number.isFinite(Number(block.vcc_step)) && Number(block.vcc_step) > 0 ? Number(block.vcc_step) : 0.5,
      freq_start: Number.isFinite(Number(block.freq_start)) && Number(block.freq_start) > 0 ? Number(block.freq_start) : 1,
      freq_stop: Number.isFinite(Number(block.freq_stop)) && Number(block.freq_stop) > 0 ? Number(block.freq_stop) : 10,
      freq_step: Number.isFinite(Number(block.freq_step)) && Number(block.freq_step) > 0 ? Number(block.freq_step) : 4,
    };
  }
  return {
    vcc_start: 0,
    vcc_stop: 5,
    vcc_step: 0.5,
    freq_start: 1,
    freq_stop: 10,
    freq_step: 4,
  };
}

function testSweepMeta(t) {
  const stim = (t && t.stimulus) || {};
  let kind = String(stim.sweep || "").toLowerCase();
  const id = String((t && t.id) || "").toLowerCase();
  if (!kind) {
    if (id === "cin" || id === "gbw" || id === "fmax") kind = "freq";
    else if (id === "ron") kind = "vcom";
    else if (id === "vth" || id === "vos_sweep" || id === "ac_vin_sweep") kind = "vin";
    else if (
      id.includes("sweep")
      || id === "delta_supply_current"
      || id === "iplus"
      || id === "leakage_off"
      || id === "leakage_on"
      || id === "input_leakage"
      || id === "cpd"
      || id === "vih_vil"
      || id === "input_thresholds"
    ) kind = "vcc";
  }
  return {
    id,
    label: (t && (t.label || t.id)) || id,
    kind,
    hint: stim.sweep_hint || stim.detail || "",
  };
}

function paintSweepPanel() {
  const ids = selectedTests();
  if (!$("param-active-hint")) return;
  $("param-active-hint").textContent = !ids.length
    ? "Select tests — standard defaults apply. Each Test program row has Parameters. Write saves this Version."
    : `${ids.length} test(s) ticked. Edit that row's Parameters. Write saves this Version.`;
}

function benchValues() {
  const d = mergeTestDefaults(selectedTests());
  const extra = catalogControlValues();
  const sweep = sweepValues();
  if (activeFamily !== "opamp") {
    const out = {
      vcc: condNum("vcc", d.vcc),
      freq_hz: d.freq_hz,
      amp_vpp: d.amp_vpp,
      n_repeats: d.n_repeats,
      ...extra,
      ...sweep,
    };
    const vccb = extra.vccb != null ? extra.vccb : condNum("vccb", d.vccb);
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
      ...sweep,
    };
  }
  return {
    vcc: d.vcc,
    freq_hz: d.freq_hz,
    amp_vpp: d.amp_vpp,
    n_repeats: d.n_repeats,
    ...sweep,
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
  const sel = currentDbSelection();
  const out = {
    ...bench,
    unit_index: duts[0],
    dut_indices: duts,
    channels: channels,
    channel: channels[0],
    walk_order: selectedWalkOrder(),
    reset_before_run: $("reset") ? $("reset").checked : false,
    part: sel.part || currentPartKey(),
    part_key: currentPartKey(),
    component: sel.component || "",
    package: sel.package || "",
    operator: sel.operator || "",
    version: sel.version || "",
    model: sel.model || "",
    year: $("db-year").value || undefined,
    run_label: runLabel,
    gain_profile: gbwOn ? profileKey : "default",
    current_limit_a: (paramCatalog.psu_golden && paramCatalog.psu_golden.current_limit_a) || 0.1,
    test_params: collectTestParamMap(ids),
  };
  return out;
}

function currentPartKey() {
  if (dbContext && dbContext.part_key) return String(dbContext.part_key);
  const raw = ($("db-part") && $("db-part").value) || "";
  return String(raw).trim().toLowerCase();
}

function selectedTests() {
  return [...document.querySelectorAll("#test-list .test-item input:checked")].map((i) => i.value);
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
    out.channels = probeChannelIds().filter((c) => channelUnion.has(c));
  }
  return out;
}

function applyTestDefaults(force) {
  const ids = selectedTests();
  const manual = isManualMode();
  if ($("param-advanced")) $("param-advanced").classList.toggle("hidden", !manual);
  paintSweepPanel();
  if (!ids.length) {
    paintSweepPanel();
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
  if ($("param-advanced")) $("param-advanced").classList.toggle("hidden", !manual);
  paintSweepPanel();
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
  const walk = selectedWalkOrder();
  if (walk === "dut") {
    for (const dut of duts) {
      html += `<details class="test-plan-nest">
      <summary>DUT ${dut} · ${chans.length > 1 ? chans.length + " channels" : "channel " + channelLetter(chans[0])}</summary>
      <div class="test-plan-body">`;
      for (const ch of chans) {
        const chName = "Ch " + channelLetter(ch);
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
  } else {
    for (const ch of chans) {
      const chName = "Ch " + channelLetter(ch);
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
    const part = currentPartKey();
    paramCatalog = await rpc("list_param_defaults", { part, family: activeFamily });
    if (!paramCatalog.controls) paramCatalog.controls = [];
    const ilim = Number((paramCatalog.psu_golden || {}).current_limit_a);
    const ma = Number.isFinite(ilim) ? Math.round(ilim * 1000) : 100;
    if ($("psu-golden-hint")) {
      $("psu-golden-hint").textContent =
        `Photo anchors: Results → Waveform layout (sheet_map.yaml). Iset=${ma} mA, OVP=Vset+0.3 V, OCP=${ma + 100} mA.`;
    }
    paintPsuWiring();
    renderDutPicks();
    applyTestDefaults(false);
  } catch (_) {
    paramCatalog = { tests: {}, gain_profiles: {}, psu_golden: { current_limit_a: 0.1 }, gbw_steps: [], gbw_run_labels: {}, controls: [], sample_size: 4 };
    paintPsuWiring();
    renderDutPicks();
  }
}

function renderConditions() {
  return;
}

function currentDutCount() {
  const el = $("dut-count");
  const typed = Number(el && el.value);
  if (Number.isFinite(typed) && typed >= 1) return Math.max(1, Math.min(16, Math.trunc(typed)));
  return Math.max(1, Math.min(16, Number(paramCatalog.sample_size) || 4));
}

function renderDutPicks() {
  const box = $("dut-picks");
  if (!box) return;
  const n = currentDutCount();
  if ($("dut-count")) $("dut-count").value = String(n);
  if ($("np-sample")) $("np-sample").value = String(n);
  if ($("unit")) $("unit").max = n;
  paramCatalog.sample_size = n;
  const prev = new Set([...document.querySelectorAll(".dut-cb:checked")].map((c) => String(c.value)));
  if (!prev.size) prev.add("1");
  let html = `<span class="hint">DUTs:</span>`;
  for (let i = 1; i <= n; i += 1) {
    const checked = prev.has(String(i)) ? "checked" : "";
    html += `<label class="check"><input type="checkbox" class="dut-cb" value="${i}" ${checked} /> ${i}</label>`;
  }
  box.innerHTML = html;
  box.querySelectorAll(".dut-cb").forEach((inp) => {
    inp.addEventListener("change", () => {
      renderRunPlans();
    });
  });
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

function parseDelayS(msg) {
  const text = String(msg || "");
  if (!/settle|dwell|delay/i.test(text)) return 0;
  const m = text.match(/(\d+(?:\.\d+)?)\s*s\b/i);
  return m ? Number(m[1]) || 0 : 0;
}

function noteActivity(status, message) {
  const msg = String(message || "").trim();
  const delayS = parseDelayS(msg);
  if (status === "waiting_operator") {
    lastActivity = { phase: "wait", text: msg || "Continue", delayS: 0, delayAt: 0 };
  } else if (status === "running" && delayS) {
    lastActivity = { phase: "delay", text: msg, delayS, delayAt: Date.now() };
  } else if (status === "running") {
    lastActivity = { phase: "run", text: msg || "measuring", delayS: 0, delayAt: 0 };
  } else if (status === "fail") {
    lastActivity = { phase: "fail", text: msg || "fail", delayS: 0, delayAt: 0 };
  } else if (status === "pass" && !pendingPrompt && !runPollActive) {
    lastActivity = { phase: "done", text: msg || "pass", delayS: 0, delayAt: 0 };
  }
  paintRunStrip();
}

function activityLine() {
  if (pendingPrompt) {
    const title = pendingPrompt.title || "Operator action";
    const hint = pendingPrompt.next_hint ? ` -- ${pendingPrompt.next_hint}` : "";
    return `${title}${hint}. Blocked until Continue or Abort.`;
  }
  if (lastActivity.phase === "delay" && lastActivity.delayS) {
    const left = Math.max(0, lastActivity.delayS - (Date.now() - lastActivity.delayAt) / 1000);
    return `${lastActivity.text} (${left.toFixed(0)}s left)`;
  }
  return lastActivity.text || "—";
}

function paintRunStrip() {
  const strip = $("run-strip");
  const phaseEl = $("run-strip-phase");
  const textEl = $("run-strip-text");
  const waiting = !!(pendingPrompt && pendingPrompt.id);
  const live = waiting || runPollActive || lastActivity.phase === "done" || lastActivity.phase === "fail";
  const runTab = document.querySelector('.tab[data-page="run"]');
  if (runTab) runTab.classList.toggle("wait", waiting);
  const gate = $("run-gate");
  if (gate) gate.classList.toggle("hidden", !waiting);
  ["run-strip-continue", "run-strip-abort", "run-strip-details"].forEach((id) => {
    const el = $(id);
    if (el) el.classList.toggle("hidden", !waiting);
  });
  if (!strip) {
    paintRunDock();
    return;
  }
  if (!live) {
    strip.classList.add("hidden");
    paintRunDock();
    return;
  }
  const phase = waiting ? "wait" : (lastActivity.phase || "run");
  strip.classList.remove("hidden", "wait", "delay", "run", "fail");
  strip.classList.add(phase === "fail" ? "wait" : phase);
  if (phaseEl) {
    phaseEl.textContent =
      phase === "wait" ? "WAIT" :
      phase === "delay" ? "DELAY" :
      phase === "fail" ? "FAIL" :
      phase === "done" ? "DONE" : "RUN";
  }
  if (textEl) textEl.textContent = activityLine();
  paintRunDock();
}

function paintRunDock() {
  const go = $("run-dock-go");
  const abort = $("run-dock-abort");
  if (!go) return;
  const waiting = !!(pendingPrompt && pendingPrompt.id);
  go.classList.add("accent");
  go.classList.remove("ghost");
  if (waiting) {
    go.textContent = "Continue";
    if (abort) abort.classList.remove("hidden");
  } else if (runPollActive) {
    go.textContent = lastActivity.phase === "delay" ? "DELAY" : "RUN";
    go.classList.remove("accent");
    go.classList.add("ghost");
    if (abort) abort.classList.remove("hidden");
  } else {
    go.textContent = "START";
    if (abort) abort.classList.add("hidden");
  }
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
  const label = $("gate-dock-label");
  if (label) label.textContent = "Waiting";

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
  paintRunStrip();
}

function openOperatorModal(payload) {
  if (!payload || !payload.id) return;
  gateHeld = false;
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
  paintRunStrip();
}

function showModal(payload) {
  if (!payload || !payload.id) return;
  if (pendingPrompt && pendingPrompt.id !== payload.id) gateHeld = false;
  updateGateDock(payload);
  pendingPrompt = payload;
  if (gateHeld) {
    paintRunStrip();
    return;
  }
  openOperatorModal(payload);
}

function dismissOperatorModal() {
  if (!pendingPrompt) return;
  gateHeld = true;
  $("modal").classList.add("hidden");
  setRunPill("wait");
  updateGateDock(pendingPrompt);
  paintRunStrip();
}

function hideModal() {
  gateHeld = false;
  pendingPrompt = null;
  gateQueue = [];
  updateGateDock(null);
  $("modal").classList.add("hidden");
  paintRunStrip();
}

async function syncPendingGate({ autoOpen = true } = {}) {
  try {
    const p = await rpc("get_pending_prompt");
    if (p) {
      if (pendingPrompt && pendingPrompt.id !== p.id) gateHeld = false;
      const prevId = pendingPrompt && pendingPrompt.id;
      updateGateDock(p);
      pendingPrompt = p;
      const modalHidden = $("modal").classList.contains("hidden");
      if (autoOpen && !gateHeld && (modalHidden || prevId !== p.id)) {
        openOperatorModal(p);
      }
      paintRunStrip();
      return p;
    }
    if (pendingPrompt) hideModal();
    else updateGateDock(null);
    return null;
  } catch (_) {
    return null;
  }
}

async function respondContinue() {
  if (!pendingPrompt) {
    const p = await syncPendingGate({ autoOpen: false });
    if (!p) return false;
  }
  await rpc("operator_respond", { prompt_id: pendingPrompt.id, continue: true });
  hideModal();
  lastActivity = { phase: "run", text: "Continue -- next procedure", delayS: 0, delayAt: 0 };
  paintRunStrip();
  return true;
}

async function respondAbort() {
  if (!pendingPrompt) {
    const p = await syncPendingGate({ autoOpen: false });
    if (!p) return false;
  }
  await rpc("operator_respond", { prompt_id: pendingPrompt.id, continue: false });
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
  const shown = rows.filter((e) => e.kind !== "dut_change");
  bar.innerHTML = (shown.length ? shown : rows).map((e) => {
    const st = e.status || "pending";
    const lab = String(e.label || "");
    const chName = e.channel ? String(e.channel) : "";
    const ch = (chName && !lab.includes(chName)) ? ` [${chName}]` : "";
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
  if (waiting || pendingPrompt) {
    banner.className = "next-banner wait";
    const label = (waiting && waiting.label) || (pendingPrompt && pendingPrompt.title) || "operator";
    const hint = (waiting && waiting.next_hint) || (pendingPrompt && pendingPrompt.next_hint) || "";
    banner.textContent = `WAIT: ${label}` +
      (hint ? ` -- ${hint}` : " -- blocked until Continue or Abort");
  } else if (lastActivity.phase === "delay") {
    banner.className = "next-banner delay";
    banner.textContent = `DELAY: ${activityLine()}`;
  } else if (tl.current && tl.current.status === "running") {
    banner.className = "next-banner run";
    banner.textContent = `RUN: ${tl.current.label}` +
      (next ? ` · Next: ${next.label}` : "");
  } else if (next) {
    banner.className = "next-banner";
    banner.textContent = `NEXT: ${next.label}` +
      (next.next_hint ? ` -- ${next.next_hint}` : "");
  } else if (tl.finished_at) {
    banner.className = "next-banner";
    banner.textContent = `DONE · finished ${fmtTs(tl.finished_at)}`;
    lastActivity = { phase: "done", text: `finished ${fmtTs(tl.finished_at)}`, delayS: 0, delayAt: 0 };
  } else {
    banner.className = "next-banner";
    banner.textContent = "Next: —";
  }
  paintRunStrip();

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

function textBlobMatch(q, ...bits) {
  const needle = String(q || "").trim().toLowerCase();
  if (!needle) return true;
  return bits.join(" ").toLowerCase().includes(needle);
}

function applyListSearch(rootSel, itemSel, q) {
  const root = document.querySelector(rootSel);
  if (!root) return;
  const needle = String(q || "").trim().toLowerCase();
  root.querySelectorAll(itemSel).forEach((el) => {
    const hit = !needle || String(el.textContent || "").toLowerCase().includes(needle);
    el.classList.toggle("hidden", !hit);
  });
}

function applyTestListSearch() {
  applyListSearch("#test-list", ".test-item", $("test-list-search") && $("test-list-search").value);
  const q = String(($("test-list-search") && $("test-list-search").value) || "").trim();
  document.querySelectorAll("#test-list .fixture-group").forEach((g) => {
    const any = [...g.querySelectorAll(".test-item")].some((el) => !el.classList.contains("hidden"));
    g.classList.toggle("hidden", !!(q && !any));
  });
}

function applyCampaignTestSearch() {
  applyListSearch("#campaign-tests", ".test-item", $("campaign-test-search") && $("campaign-test-search").value);
}

function productGuessFromFile(file) {
  const up = String(file || "").replace(/\\/g, "/").toUpperCase();
  let best = "";
  for (const p of inventoryPartChoices()) {
    const token = String(p || "").toUpperCase();
    if (token.length >= 4 && up.includes(token) && token.length > best.length) best = token;
  }
  const m = up.match(/RS[0-9A-Z]+/g) || [];
  for (const t of m) {
    if (t.length > best.length) best = t;
  }
  return best;
}

function detectFamilyKey() {
  let fam = (activeFamily || "logic").toLowerCase();
  if (fam === "lim") fam = "switch";
  return fam;
}

function sameDetectFamily(guess) {
  const g = String(guess || "").toLowerCase();
  if (!g) return true;
  const fam = detectFamilyKey();
  if (g === "lim") return fam === "switch";
  return g === fam;
}

function escapeAttr(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function liveKeys(obj) {
  return Object.keys(obj || {}).filter((k) => k && !k.startsWith("_") && !k.startsWith("."));
}

const comboStore = {};
const COMBO_REMOVABLE = new Set(["setup-label-value", "db-tag-input"]);
let comboMenu = null;
let comboOpenId = "";
let comboHi = -1;
let comboPicks = [];
let combosReady = false;
let comboDirty = false;

function comboMenuEl() {
  if (comboMenu) return comboMenu;
  comboMenu = document.createElement("div");
  comboMenu.id = "ate-combo-menu";
  comboMenu.className = "combo-menu hidden";
  comboMenu.setAttribute("role", "listbox");
  document.body.appendChild(comboMenu);
  return comboMenu;
}

function syncComboChrome(el) {
  if (!el) return;
  const wrap = el.closest(".combo");
  const clear = wrap && wrap.querySelector(".combo-clear");
  if (clear) clear.classList.toggle("hidden", !String(el.value || "").trim());
}

function fillCombo(el, values, selected, opts) {
  if (!el) return;
  const uniq = [];
  const seen = new Set();
  for (const v of values || []) {
    const s = String(v || "").trim();
    if (!s || seen.has(s)) continue;
    if (el.id === "db-operator" && hiddenOperatorName(s)) continue;
    seen.add(s);
    uniq.push(s);
  }
  const keep = (selected != null && String(selected).trim())
    ? String(selected).trim()
    : String(el.value || "").trim();
  const blocked = el.id === "db-operator" && hiddenOperatorName(keep);
  const listKeep = !(opts && opts.listKeep === false);
  if (keep && !seen.has(keep) && listKeep && !blocked) uniq.unshift(keep);
  if (el.id) comboStore[el.id] = uniq;
  if (keep && !blocked) el.value = keep;
  else if (blocked) el.value = uniq[0] || "";
  syncComboChrome(el);
  if (comboOpenId && el.id === comboOpenId) renderComboMenu();
}

function closeComboMenu() {
  comboOpenId = "";
  comboHi = -1;
  comboPicks = [];
  if (comboMenu) comboMenu.classList.add("hidden");
}

function comboFiltered(input) {
  const q = String(input.value || "").trim().toLowerCase();
  const all = comboStore[input.id] || [];
  if (!comboDirty || !q) return all.slice();
  return all.filter((v) => String(v).toLowerCase().includes(q));
}

function renderComboMenu() {
  const input = comboOpenId ? $(comboOpenId) : null;
  const menu = comboMenuEl();
  if (!input) {
    closeComboMenu();
    return;
  }
  const wrap = input.closest(".combo") || input;
  const rect = wrap.getBoundingClientRect();
  const q = String(input.value || "").trim();
  const rows = comboFiltered(input);
  const exact = (comboStore[input.id] || []).some((v) => String(v).toLowerCase() === q.toLowerCase());
  comboPicks = [];
  if (input.id === "first-run-who") {
    const keep = q && !firstRunOwnerKnown(q);
    comboPicks.push({
      add: true,
      value: keep ? q : FIRST_RUN_ADD,
      label: keep ? ("+ Add " + q) : FIRST_RUN_ADD,
    });
    rows.forEach((v) => {
      if (v !== FIRST_RUN_ADD) comboPicks.push({ add: false, value: v });
    });
  } else {
    if (q && !exact) comboPicks.push({ add: true, value: q });
    rows.forEach((v) => comboPicks.push({ add: false, value: v }));
  }
  if (comboHi >= comboPicks.length) comboHi = comboPicks.length - 1;
  menu.innerHTML = "";
  if (!comboPicks.length) {
    const empty = document.createElement("div");
    empty.className = "combo-empty";
    empty.textContent = "type to add";
    menu.appendChild(empty);
  } else {
    comboPicks.forEach((pick, i) => {
      const row = document.createElement("div");
      row.className = "combo-opt" + (i === comboHi ? " hi" : "");
      const lab = document.createElement("button");
      lab.type = "button";
      lab.className = pick.add ? "combo-add" : "combo-opt-lab";
      lab.textContent = pick.label || (pick.add ? ("Add " + pick.value) : pick.value);
      lab.onmousedown = (ev) => {
        ev.preventDefault();
        applyComboPick(input, pick.value);
      };
      row.appendChild(lab);
      if (!pick.add && COMBO_REMOVABLE.has(input.id)) {
        const x = document.createElement("button");
        x.type = "button";
        x.className = "combo-opt-x";
        x.textContent = "x";
        x.title = "Remove";
        x.onmousedown = (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          removeComboOption(input, pick.value);
        };
        row.appendChild(x);
      }
      menu.appendChild(row);
    });
  }
  const need = Math.min(240, Math.max(36, comboPicks.length * 28 + 12));
  let top = rect.bottom + 2;
  if (top + need > window.innerHeight - 8 && rect.top > need + 8) {
    top = Math.max(4, rect.top - need - 2);
  }
  menu.style.left = Math.max(4, rect.left) + "px";
  menu.style.top = top + "px";
  menu.style.width = Math.max(rect.width, 160) + "px";
  menu.classList.remove("hidden");
}

function openCombo(input) {
  if (!input || !input.id) return;
  comboOpenId = input.id;
  comboHi = -1;
  comboDirty = false;
  renderComboMenu();
}

function toggleCombo(input) {
  if (comboOpenId === input.id) closeComboMenu();
  else openCombo(input);
}

function applyComboPick(input, value) {
  if (!input) return;
  if (input.id === "db-tag-input") {
    addCampaignTagFromText(value);
    input.value = "";
    syncComboChrome(input);
    closeComboMenu();
    return;
  }
  if (input.id === "person-sku-input") {
    addPersonSku(value);
    input.value = "";
    syncComboChrome(input);
    closeComboMenu();
    return;
  }
  if (input.id === "campaign-board") {
    setCampaignBoard(value);
    closeComboMenu();
    return;
  }
  if (input.id === "setup-label-value") {
    const kind = (($("setup-label-kind") && $("setup-label-kind").value) || "board").trim();
    addSetupLabel(kind, value);
    input.value = "";
    syncComboChrome(input);
    closeComboMenu();
    return;
  }
  if (input.id === "first-run-who") {
    if (value === FIRST_RUN_ADD || !firstRunOwnerKnown(value)) {
      const keep = (value && value !== FIRST_RUN_ADD) ? value : input.value;
      enterFirstRunAddName(keep);
      closeComboMenu();
      return;
    }
    exitFirstRunAddName();
    input.value = value;
    syncComboChrome(input);
    closeComboMenu();
    syncFirstRunProductsVisibility();
    paintFirstRunProducts();
    return;
  }
  if (input.id === "first-run-product") {
    addFirstRunProduct(value);
    const exact = trackingSkuRows().some((r) => {
      const bits = [r.part, r.package, r.model].filter(Boolean).join(" · ");
      return bits === value;
    });
    input.value = exact ? "" : value;
    syncComboChrome(input);
    closeComboMenu();
    paintFirstRunProducts();
    return;
  }
  input.value = value;
  syncComboChrome(input);
  closeComboMenu();
  input.dispatchEvent(new Event("change", { bubbles: true }));
  if (input.id === "db-operator") {
    const typed = String(input.value || "").trim();
    if (
      typed
      && typed.toLowerCase() !== "all"
      && !ownerIsObserver(typed)
      && !hiddenOperatorName(typed)
      && !operatorKnown(typed)
    ) {
      openAddOperatorModal(typed, currentDbSelection());
    }
  }
  if (input.id === "db-package") {
    const typed = String(input.value || "").trim();
    const known = (comboStore["db-package"] || []).some(
      (v) => String(v).toLowerCase() === typed.toLowerCase()
    );
    if (typed && !known) openCampaignPlus("package", typed);
  }
}

function removeComboOption(input, value) {
  const v = String(value || "");
  comboStore[input.id] = (comboStore[input.id] || []).filter((x) => x !== v);
  if (input.value === v) input.value = "";
  syncComboChrome(input);
  if (input.id === "db-tag-input") {
    const tok = v;
    campaignTags = (campaignTags || []).filter((t) => t !== tok && t !== v);
    campaignLabels = (campaignLabels || []).filter((lab) => labelToken(lab) !== tok && labelToken(lab) !== v);
    if (tok.startsWith("board:")) {
      const b = tok.slice(6);
      campaignBoards = (campaignBoards || []).filter((x) => x !== b);
      boardVocab = (boardVocab || []).filter((x) => x !== b);
    }
    if (tok.includes(":")) {
      const i = tok.indexOf(":");
      const kind = tok.slice(0, i);
      const val = tok.slice(i + 1);
      if (labelValueVocab[kind]) {
        labelValueVocab[kind] = labelValueVocab[kind].filter((x) => x !== val);
      }
    }
    paintTagsEditor();
    saveCampaignLabels().catch((e) => log(`Labels: ${e.message}\n`));
  }
  if (input.id === "setup-label-value") {
    const kind = (($("setup-label-kind") && $("setup-label-kind").value) || "tag").trim();
    if (labelValueVocab[kind]) {
      labelValueVocab[kind] = labelValueVocab[kind].filter((x) => x !== v);
    }
    campaignLabels = (campaignLabels || []).filter((lab) => !(lab.kind === kind && lab.value === v));
    campaignTags = (campaignTags || []).filter((t) => t !== labelToken({ kind, value: v }));
    paintTagsEditor();
    saveCampaignLabels().catch((e) => log(`Labels: ${e.message}\n`));
  }
  renderComboMenu();
}

function onComboKey(input, ev) {
  const tagger = input.id === "db-tag-input";
  if (ev.key === "Escape") {
    closeComboMenu();
    return;
  }
  if (ev.key === "ArrowDown") {
    ev.preventDefault();
    if (comboOpenId !== input.id) openCombo(input);
    else {
      comboHi = Math.min(comboPicks.length - 1, comboHi + 1);
      renderComboMenu();
    }
    return;
  }
  if (ev.key === "ArrowUp") {
    ev.preventDefault();
    if (comboOpenId !== input.id) openCombo(input);
    else {
      comboHi = Math.max(0, comboHi - 1);
      renderComboMenu();
    }
    return;
  }
  if (tagger && (ev.key === " " || ev.key === ",") && String(input.value).trim()) {
    ev.preventDefault();
    addCampaignTagFromText(input.value);
    input.value = "";
    syncComboChrome(input);
    closeComboMenu();
    return;
  }
  if (ev.key === "Enter") {
    ev.preventDefault();
    ev.stopImmediatePropagation();
    if (input.id === "setup-label-value") {
      if (comboOpenId === input.id && comboHi >= 0 && comboPicks[comboHi]) {
        applyComboPick(input, comboPicks[comboHi].value);
      }
      if ($("btn-setup-add-label")) $("btn-setup-add-label").click();
      return;
    }
    if (comboOpenId === input.id && comboHi >= 0 && comboPicks[comboHi]) {
      applyComboPick(input, comboPicks[comboHi].value);
      return;
    }
    const typed = String(input.value || "").trim();
    if (tagger && typed) {
      addCampaignTagFromText(typed);
      input.value = "";
      syncComboChrome(input);
      closeComboMenu();
      return;
    }
    if (typed) {
      applyComboPick(input, typed);
      if (input.id === "db-operator" && !operatorKnown(typed)) {
        openAddOperatorModal(typed, currentDbSelection());
      }
    }
  }
}

function bindCombo(wrap) {
  if (!wrap || wrap.dataset.comboBound) return;
  wrap.dataset.comboBound = "1";
  const input = wrap.querySelector("input");
  const caret = wrap.querySelector(".combo-caret");
  const clear = wrap.querySelector(".combo-clear");
  if (!input) return;
  if (!input.id) input.id = "combo-" + Math.random().toString(36).slice(2, 8);
  if (caret) {
    caret.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      toggleCombo(input);
      input.focus();
    });
  }
  if (clear) {
    clear.innerHTML = '<span aria-hidden="true">x</span>';
    clear.setAttribute("aria-label", "Clear");
    clear.addEventListener("mousedown", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      input.value = "";
      if (input.id === "first-run-who") {
        delete input.dataset.addName;
        const whoWrap = $("first-run-who-wrap");
        if (whoWrap) whoWrap.classList.remove("first-run-typing");
      }
      syncComboChrome(input);
      closeComboMenu();
      input.dispatchEvent(new Event("change", { bubbles: true }));
      input.focus();
    });
  }
  input.addEventListener("mousedown", () => {
    if (comboOpenId !== input.id) openCombo(input);
  });
  input.addEventListener("input", () => {
    comboDirty = true;
    syncComboChrome(input);
    if (comboOpenId === input.id) renderComboMenu();
    else openCombo(input);
    if (input.id === "first-run-who") {
      const q = String(input.value || "").trim();
      if (q && q !== FIRST_RUN_ADD && !firstRunOwnerKnown(q)) {
        input.dataset.addName = "1";
        const wrap = $("first-run-who-wrap");
        if (wrap) wrap.classList.add("first-run-typing");
      } else if (firstRunOwnerKnown(q)) {
        exitFirstRunAddName();
      }
      syncFirstRunProductsVisibility();
      paintFirstRunProducts();
    }
    if (input.id === "first-run-product") paintFirstRunProducts();
  });
  input.addEventListener("keydown", (ev) => onComboKey(input, ev));
}

function initCombos() {
  document.querySelectorAll(".combo").forEach(bindCombo);
  if (combosReady) return;
  combosReady = true;
  document.addEventListener("mousedown", (ev) => {
    if (!comboOpenId) return;
    const t = ev.target;
    if (t && t.closest && t.closest("#ate-combo-menu")) return;
    const wrap = t && t.closest && t.closest(".combo");
    const input = wrap && wrap.querySelector("input");
    if (input && input.id === comboOpenId) return;
    closeComboMenu();
  });
  window.addEventListener("resize", closeComboMenu);
}

function addCampaignTagFromText(raw) {
  const t = String(raw || "").trim();
  if (!t || t.startsWith("(")) return false;
  let kind = "tag";
  let value = t;
  if (t.includes(":")) {
    const i = t.indexOf(":");
    kind = t.slice(0, i).trim() || "tag";
    value = t.slice(i + 1).trim();
  }
  if (!value) return false;
  addSetupLabel(kind, value);
  return true;
}

function tagComboValues() {
  const out = [];
  const seen = new Set((campaignTags || []).map((t) => String(t).toLowerCase()));
  const add = (tok) => {
    const s = String(tok || "").trim();
    if (!s || s.startsWith("board:") || seen.has(s.toLowerCase())) return;
    seen.add(s.toLowerCase());
    out.push(s);
  };
  for (const [kind, vals] of Object.entries(labelValueVocab || {})) {
    if (String(kind) === "board") continue;
    for (const v of vals || []) {
      add(kind === "tag" ? v : `${kind}:${v}`);
    }
  }
  return out;
}

function operatorFromPic(pic) {
  const raw = String(pic || "").trim();
  if (!raw || raw.toLowerCase() === "rs") return "";
  if (PERSON_CANON[personFold(raw)]) return displayPerson(raw);
  const row = ownerRowByName(raw);
  if (!row || row.id === "all") return "";
  return displayPerson(row.label || row.id);
}

function ingestDbTree(tree) {
  const src = (tree && typeof tree === "object") ? tree : { components: {} };
  const byOp = {};
  for (const cnode of Object.values(src.components || {})) {
    for (const [part, pnode] of Object.entries((cnode && cnode.parts) || {})) {
      for (const pkgNode of Object.values((pnode && pnode.packages) || {})) {
        for (const op of Object.keys((pkgNode && pkgNode.operators) || {})) {
          if (!op || op.startsWith(".") || op === "_unassigned") continue;
          const k = String(op).toLowerCase();
          if (!byOp[k]) byOp[k] = {};
          byOp[k][String(part).toUpperCase()] = true;
        }
      }
    }
  }
  diskPartsByOperator = byOp;
  dbTree = src;
}

function findOwnerRow(who) {
  const raw = String(who || "").trim().toLowerCase();
  if (!raw) return null;
  return (ownersList || []).find((o) => (
    String(o.id || "").toLowerCase() === raw
    || String(o.label || "").toLowerCase() === raw
  )) || null;
}

function partScopeIsMine() {
  const el = $("part-scope");
  if (el) return el.value !== "all";
  try {
    return (localStorage.getItem(PART_SCOPE_KEY) || "mine") !== "all";
  } catch (_) {
    return true;
  }
}

function restorePartScope() {
  const el = $("part-scope");
  if (!el) return;
  let v = "mine";
  try {
    v = localStorage.getItem(PART_SCOPE_KEY) || "mine";
  } catch (_) { /* ignore */ }
  el.value = (v === "all") ? "all" : "mine";
}

function minePartCodes(who) {
  const set = {};
  const add = (p) => {
    const u = String(p || "").trim().toUpperCase();
    if (u) set[u] = true;
  };
  const row = findOwnerRow(who) || findOwnerRow(writeOperatorLabel());
  if (row) {
    (row.parts || []).forEach(add);
  }
  const label = (row && (row.label || row.id)) || String(who || "").trim();
  for (const r of inventoryRows || []) {
    const pic = operatorFromPic(r.pic);
    if (pic && label && sameOperator(pic, label)) add(r.part);
    if (pic && row && sameOperator(pic, displayPerson(row.label || row.id))) add(r.part);
  }
  return Object.keys(set);
}

function skuHandledBy(part, who) {
  const want = String(part || "").toUpperCase();
  if (!want || !who) return false;
  return minePartCodes(who).includes(want);
}

function paintPartScopeHint() {
  const el = $("part-scope-hint");
  if (!el) return;
  const who = writeOperatorLabel() || (($("db-operator") && $("db-operator").value) || "");
  if (!partScopeIsMine()) {
    el.textContent = "Part list: All tracking / disk (type to filter).";
    return;
  }
  const n = minePartCodes(who).length;
  el.textContent = who
    ? `Part list: Mine for ${who} (${n} SKU code${n === 1 ? "" : "s"}). Switch All tracking to pick another.`
    : "Part list: Mine (pick a person).";
}

function componentForCategory(catId) {
  const row = (categoryRows || []).find((c) => c.id === catId);
  if (row && row.component) return row.component;
  return componentFromFamily(catId) || "";
}

function mergeInventoryIntoTree() {
  for (const row of inventoryRows || []) {
    const component = componentForCategory(row.category) || "";
    const part = String(row.part || "").trim().toUpperCase();
    if (!component || !part) continue;
    const pkg = row.package || "SOT23";
    if (!dbTree.components) dbTree.components = {};
    if (!dbTree.components[component]) dbTree.components[component] = { parts: {} };
    if (!dbTree.components[component].parts[part]) {
      dbTree.components[component].parts[part] = { packages: {} };
    }
    const pkgs = dbTree.components[component].parts[part].packages;
    if (!pkgs[pkg]) pkgs[pkg] = { operators: {} };
  }
}

function campaignFromInventory(family) {
  const want = typeForFamily(family);
  const rows = (inventoryRows || []).filter((r) => String(r.category || "") === want);
  const mine = new Set(minePartCodes(writeOperatorLabel()));
  let row = null;
  if (partScopeIsMine() && mine.size) {
    row = rows.find((r) => mine.has(String(r.part || "").toUpperCase()) && suiteForRow(r))
      || rows.find((r) => mine.has(String(r.part || "").toUpperCase()));
  }
  row = row || rows.find((r) => suiteForRow(r)) || rows[0];
  if (!row) return null;
  return {
    component: componentForCategory(row.category) || componentFromFamily(family),
    part: String(row.part || "").toUpperCase(),
    package: row.package || "SOT23",
    operator: writeOperatorLabel() || operatorFromPic(row.pic) || "Eugene",
    version: "Version_1",
    model: row.model || row.part || "",
    year: ($("db-year") && $("db-year").value) || "2026",
  };
}

function versionsForSel(sel) {
  const partsObj = ((dbTree.components || {})[sel.component] || {}).parts || {};
  const pkgsObj = (partsObj[sel.part] || {}).packages || {};
  const opsObj = (pkgsObj[sel.package] || {}).operators || {};
  return ((opsObj[sel.operator] || {}).versions || []).filter(Boolean);
}

const CAMPAIGN_KEY = "ate_last_campaign";
const CAMPAIGN_BY_FAMILY_KEY = "ate_last_campaign_by_family";
const CAMPAIGN_BY_OWNER_KEY = "ate_last_campaign_by_owner";
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
  try {
    const oid = readSavedOwner();
    if (oid && oid !== "all" && !ownerIsObserver(oid)) {
      const by = JSON.parse(localStorage.getItem(CAMPAIGN_BY_OWNER_KEY) || "{}");
      by[oid] = payload;
      localStorage.setItem(CAMPAIGN_BY_OWNER_KEY, JSON.stringify(by));
    }
  } catch (_) { /* ignore */ }
}

function readSavedCampaignForOwner(id) {
  try {
    const oid = String(id || "").trim();
    if (!oid || oid === "all") return null;
    const by = JSON.parse(localStorage.getItem(CAMPAIGN_BY_OWNER_KEY) || "{}");
    const hit = by[oid];
    return hit && hit.part ? hit : null;
  } catch (_) {
    return null;
  }
}

function campaignForThisPc(saved, ctx) {
  const meId = readSavedOwner();
  const meRow = ownersList.find((o) => o.id === meId);
  const meLabel = (meRow && meRow.label) || "";
  const withMe = (sel) => ({
    ...DEFAULT_CAMPAIGN,
    ...sel,
    operator: meLabel || sel.operator || "",
  });
  if (!meId || meId === "all" || ownerIsObserver(meId)) {
    return {
      ...DEFAULT_CAMPAIGN,
      ...saved,
      operator: saved.operator || (ctx && ctx.operator) || "",
    };
  }
  const byMe = readSavedCampaignForOwner(meId);
  if (byMe && byMe.part) return withMe(byMe);
  if (sameOperator(saved.operator, meLabel) || sameOperator(saved.operator, meId)) {
    return withMe(saved);
  }
  const ctxOp = ctx && ctx.operator;
  if (sameOperator(ctxOp, meLabel) || sameOperator(ctxOp, meId)) {
    return withMe({
      component: ctx.component || saved.component,
      part: ctx.part || saved.part,
      package: ctx.package || saved.package,
      version: ctx.version || saved.version,
      model: ctx.model || saved.model,
      year: ctx.year || saved.year,
    });
  }
  return withMe({
    component: (meRow && meRow.default_component) || saved.component,
    part: String((meRow && meRow.default_part) || saved.part || "").toUpperCase(),
    package: (meRow && meRow.default_package) || saved.package,
    version: "Version_1",
    model: String((meRow && meRow.default_part) || saved.part || "").toUpperCase(),
    year: saved.year,
  });
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
  if (sel.operator && !needsFirstRun() && !ownerIsObserver(sel.operator) && !hiddenOperatorName(sel.operator)) {
    syncOwnerSelectFromFolder(sel.operator);
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

function refreshDbCascades(preserve, changedId) {
  mergeInventoryIntoTree();
  const comps = liveKeys(dbTree.components);
  const sel = preserve || currentDbSelection();
  const component = sel.component || comps[0] || "";
  fillCombo($("db-component"), comps, component);

  const partsObj = ((dbTree.components || {})[component] || {}).parts || {};
  let parts = liveKeys(partsObj);
  if (partScopeIsMine()) {
    const mine = new Set(minePartCodes(writeOperatorLabel() || sel.operator));
    parts = parts.filter((p) => mine.has(String(p).toUpperCase()));
  }
  let part = sel.part || parts[0] || "";
  if (changedId === "db-component" && parts.length && !parts.includes(part)) part = parts[0];
  fillCombo($("db-part"), parts, part);
  paintPartScopeHint();

  const pkgsObj = (partsObj[part] || {}).packages || {};
  const packages = liveKeys(pkgsObj);
  let pkg = sel.package || packages[0] || "";
  if ((changedId === "db-component" || changedId === "db-part") && packages.length && !packages.includes(pkg)) {
    pkg = packages[0];
  }
  fillCombo($("db-package"), packages, pkg, { listKeep: false });

  const opsObj = (pkgsObj[pkg] || {}).operators || {};
  const operators = Object.keys(opsObj).filter((k) => k && !k.startsWith(".") && k !== "_unassigned" && !hiddenOperatorName(k));
  const preferOp = sel.operator && sel.operator !== "_unassigned" && !hiddenOperatorName(sel.operator)
    ? sel.operator
    : writeOperatorLabel();
  let operator = pickLiveOperator(operators, preferOp) || sel.operator || "";
  if (hiddenOperatorName(operator)) operator = pickLiveOperator(operators, writeOperatorLabel()) || "";
  if (
    sel.operator
    && sel.operator !== "_unassigned"
    && !hiddenOperatorName(sel.operator)
    && !operators.includes(sel.operator)
  ) {
    operator = sel.operator;
  }
  if ((changedId === "db-component" || changedId === "db-part" || changedId === "db-package")
      && operators.length && !operators.includes(operator)) {
    operator = pickLiveOperator(operators, writeOperatorLabel());
  }
  fillCombo($("db-operator"), operators, operator, { listKeep: false });

  const versions = versionsForSel({ component, part, package: pkg, operator }) || ["Version_1"];
  const versionList = versions.length ? versions : ["Version_1"];
  let version = sel.version || versionList[0];
  if (changedId && changedId !== "db-version" && versionList.length && !versionList.includes(version)) {
    version = pickLatestVersion(versionList);
  }
  fillCombo($("db-version"), versionList, version);
}

function renderDbHints(ctx) {
  dbContext = ctx;
  if (!ctx) return;
  $("db-breadcrumb").textContent =
    `${ctx.component} / ${ctx.part} / ${ctx.package} / ${ctx.operator || "?"} / ${ctx.version} · ${ctx.model}`;
  $("db-model").value = ctx.model || "";
  if (!$("db-year").value && ctx.year) $("db-year").value = ctx.year;
  let photo = ctx.photo_example || "";
  if (/\/ORT\//i.test(photo) && railType && railType !== "opamp") {
    photo += " (OpAmp default -- Apply campaign)";
  }
  $("db-path-hint").textContent = `Photos: ${photo}`;
  $("db-excel-hint").textContent = `Lab report: ${ctx.lab_report}`;
  $("results-db-hint").textContent =
    `Lab report: ${ctx.lab_report} · sessions: ${ctx.sessions}`;
  if ($("central-db-hint") && ctx.test_database_root) {
    $("central-db-hint").textContent =
      `Central DB (${ctx.cloud_kind || "local"}): ${ctx.test_database_root}`;
  }
  const n = Number(ctx.sample_size) || 4;
  if ($("dut-count")) $("dut-count").value = String(Math.max(1, Math.min(16, n)));
  if ($("unit")) $("unit").max = n;
  paramCatalog.sample_size = n;
  renderDutPicks();
  applyWalkOrder(ctx.walk_order || (function () {
    try { return localStorage.getItem("ate.walkOrder") || "channel"; } catch (e) { return "channel"; }
  })());
  applyProbeChannels(ctx.probe_channels || fallbackProbeChannels());
  refreshTagsUI();
}

async function pollEvents() {
  try {
    const events = await rpc("get_events");
    for (const ev of events || []) {
      if (ev.type === "log") log(ev.payload?.text || "");
      if (ev.type === "timeline") renderTimeline(ev.payload);
      if (ev.type === "progress") {
        noteActivity(ev.payload.status, ev.payload.message || ev.payload.substep || "");
        if (ev.payload.status === "waiting_operator" || pendingPrompt) {
          setRunPill("wait");
        } else if (ev.payload.status === "running") {
          setRunPill("running");
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
      await syncPendingGate({ autoOpen: !gateHeld });
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
    const part = currentPartKey();
    fixtureCatalog = await rpc("list_fixture_modes", { part });
  } catch (_) {
    fixtureCatalog = [];
  }
  renderGainBoards(fixtureCatalog);
}

async function loadDb() {
  ingestDbTree(await rpc("list_db_tree"));
  const info = await rpc("get_db_context");
  const ctx = info.context || {};
  const saved = readSavedCampaign();
  const sel = campaignForThisPc(saved, ctx);
  paintCampaign(sel);
  renderDbHints({ ...saved, ...ctx, ...sel });
  if (!needsFirstRun()) {
    try {
      await applyDb();
    } catch (e) {
      log(`Campaign restore warn: ${e.message}\n`);
    }
  }
  if (info.guide?.orchestration) {
    log("DB guide:\n" + info.guide.orchestration.map((s) => `  ${s}`).join("\n") + "\n");
  }
}

let campaignTags = [];
let campaignBoards = [];
let boardVocab = [];

function renderTagChips(el, tags, { removable = false, compact = false } = {}) {
  if (!el) return;
  el.innerHTML = "";
  const list = tags || [];
  const expanded = el.dataset.expanded === "1";
  const showAll = !compact || expanded || list.length <= 1;
  const visible = showAll ? list : list.slice(-1);
  for (const t of visible) {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = t;
    chip.setAttribute("aria-label", t);
    if (removable) {
      const x = document.createElement("button");
      x.type = "button";
      x.className = "tag-chip-x";
      x.innerHTML = '<span aria-hidden="true">x</span>';
      x.setAttribute("aria-label", `Remove ${t}`);
      x.title = "Remove";
      x.onclick = () => {
        campaignTags = campaignTags.filter((v) => v !== t);
        campaignLabels = (campaignLabels || []).filter((lab) => labelToken(lab) !== t);
        if (t.startsWith("board:")) {
          const b = t.slice(6);
          campaignBoards = campaignBoards.filter((v) => v !== b);
        }
        paintTagsEditor();
        saveCampaignLabels().catch((e) => log(`Labels: ${e.message}\n`));
      };
      chip.appendChild(x);
    }
    el.appendChild(chip);
  }
  if (compact && list.length > 1 && !expanded) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "tag-chip tag-chip-more";
    more.textContent = `+${list.length - 1} more`;
    more.title = "Show all tags";
    more.onclick = () => {
      el.dataset.expanded = "1";
      paintTagsEditor();
    };
    el.appendChild(more);
  }
  if (compact && expanded && list.length > 1) {
    const hide = document.createElement("button");
    hide.type = "button";
    hide.className = "tag-chip tag-chip-more";
    hide.textContent = "hide";
    hide.onclick = () => {
      el.dataset.expanded = "0";
      paintTagsEditor();
    };
    el.appendChild(hide);
  }
  if (!list.length) {
    const empty = document.createElement("span");
    empty.className = "hint";
    empty.textContent = "none";
    el.appendChild(empty);
  }
}

function labelToken(lab) {
  const k = String((lab && lab.kind) || "tag");
  const v = String((lab && lab.value) || "");
  return k === "tag" ? v : `${k}:${v}`;
}

function fillLabelValueSelect() {
  const kindEl = $("setup-label-kind");
  const valEl = $("setup-label-value");
  if (!valEl) return;
  const kindRaw = (kindEl && kindEl.value) || "board";
  const kind = String(kindRaw).trim().toLowerCase().replace(/\s+/g, "_");
  const vals = (labelValueVocab[kind] || labelValueVocab[kindRaw] || []).slice();
  if (kind === "board") {
    for (const b of boardVocab || []) {
      if (b && !vals.includes(b)) vals.push(b);
    }
  }
  fillCombo(valEl, vals, valEl.value || "");
  updateLabelKindHint();
}

const KIND_HELP = {
  board: "Board = fixture PCB for this package. Open Value and pick (LOGIC-SC70-REV1). It saves. Chip x removes.",
  board_type: "Board type is the class (Logic / G11 / BUFFER), not a folder name.",
  tag: "Free token. Space in the Tags box also adds one.",
  task: "What this campaign is for (SKU note).",
};
const KIND_VALUE_PH = {
  board: "LOGIC-SC70-REV1",
  board_type: "Logic",
  tag: "project:RS1G07",
  task: "RS1G07-char",
};

function updateLabelKindHint() {
  const raw = String(($("setup-label-kind") && $("setup-label-kind").value) || "board");
  const kind = raw.trim().toLowerCase().replace(/\s+/g, "_");
  const hint = $("label-kind-hint");
  if (hint) hint.textContent = KIND_HELP[kind] || KIND_HELP.board;
  const val = $("setup-label-value");
  if (val) val.placeholder = KIND_VALUE_PH[kind] || KIND_VALUE_PH.board;
}

function fillLabelKindSelect() {
  const el = $("setup-label-kind");
  if (!el) return;
  const kinds = labelKindVocab.length ? labelKindVocab : [
    { id: "board", label: "Board" },
    { id: "board_type", label: "Board type" },
    { id: "tag", label: "Tag" },
    { id: "task", label: "Task" },
  ];
  const ids = kinds.map((k) => k.id || k);
  fillCombo(el, ids, el.value || ids[0] || "board");
  fillLabelValueSelect();
  fillLabelScopeSelect();
  updateLabelKindHint();
}

function fillLabelScopeSelect() {
  const el = $("label-scope");
  if (!el) return;
  const opts = ["this campaign", "this class", "all products"];
  const cur = el.value && opts.includes(el.value) ? el.value : (el.value || "this campaign");
  fillCombo(el, opts, cur);
}

function labelRememberScope() {
  const raw = String(($("label-scope") && $("label-scope").value) || "campaign").trim().toLowerCase();
  if (raw.includes("class") || raw === "family") return "family";
  if (raw.includes("all")) return "all";
  return "campaign";
}

function paintTagsEditor() {
  const freeTags = (campaignTags || []).filter((t) => !String(t).startsWith("board:"));
  renderTagChips($("db-tag-chips"), freeTags, { removable: true, compact: true });
  renderTagChips($("tags-editor-chips"), freeTags, { removable: true, compact: false });
  const setup = $("setup-label-chips");
  if (setup) {
    setup.innerHTML = "";
    setup.classList.add("hidden");
  }
  paintCampaignBoard();
}

function campaignBoardValue() {
  if (campaignBoards && campaignBoards.length) return String(campaignBoards[0] || "");
  const fromLab = (campaignLabels || []).find((x) => String(x.kind || "") === "board");
  return fromLab ? String(fromLab.value || "") : "";
}

function paintCampaignBoard() {
  const el = $("campaign-board");
  if (!el) return;
  const cur = campaignBoardValue();
  const opts = (boardVocab && boardVocab.length) ? boardVocab.slice() : [];
  if (cur && !opts.some((x) => String(x).toLowerCase() === cur.toLowerCase())) {
    opts.unshift(cur);
  }
  fillCombo(el, opts, cur || "");
  if (cur) el.value = cur;
  else el.value = "";
  syncComboChrome(el);
  if ($("board-pick-hint")) {
    const fam = railType || "this class";
    $("board-pick-hint").textContent = cur
      ? `Board ${cur} · shared in central _ate for ${fam} only (not other product classes).`
      : `Pick a board for ${fam}. One per campaign. New names save to #Test_Database/_ate for this class.`;
  }
}

function setCampaignBoard(raw) {
  const v = String(raw || "").trim();
  if (!v || v.startsWith("(")) return;
  campaignBoards = [v];
  campaignLabels = (campaignLabels || []).filter((x) => String(x.kind || "") !== "board");
  campaignLabels.push({ kind: "board", value: v });
  campaignTags = (campaignTags || []).filter((t) => !String(t).startsWith("board:"));
  campaignTags.push(`board:${v}`);
  if (!boardVocab.includes(v)) boardVocab = [v].concat(boardVocab || []);
  paintTagsEditor();
  saveCampaignLabels().catch((e) => alert(e.message));
}

function clearCampaignBoard() {
  campaignBoards = [];
  campaignLabels = (campaignLabels || []).filter((x) => String(x.kind || "") !== "board");
  campaignTags = (campaignTags || []).filter((t) => !String(t).startsWith("board:"));
  paintTagsEditor();
  saveCampaignLabels().catch((e) => alert(e.message));
}

async function refreshTagsUI() {
  try {
    const data = await rpc("list_tags");
    campaignTags = Array.isArray(data.tags) ? data.tags.slice() : [];
    campaignBoards = Array.isArray(data.boards) ? data.boards.slice() : [];
    if (campaignBoards.length > 1) campaignBoards = [campaignBoards[campaignBoards.length - 1]];
    campaignLabels = Array.isArray(data.labels) ? data.labels.slice() : [];
    boardVocab = Array.isArray(data.boards_vocab) ? data.boards_vocab.slice() : [];
    labelKindVocab = Array.isArray(data.kinds) ? data.kinds.slice() : [];
    labelValueVocab = (data.label_values && typeof data.label_values === "object") ? data.label_values : {};
    const tagIn = $("db-tag-input");
    if (tagIn) {
      if (document.activeElement === tagIn) {
        comboStore["db-tag-input"] = tagComboValues();
        if (comboOpenId === "db-tag-input") renderComboMenu();
      } else {
        fillCombo(tagIn, tagComboValues(), "");
        tagIn.value = "";
        syncComboChrome(tagIn);
      }
    }
    fillLabelScopeSelect();
    paintTagsEditor();
    if ($("tags-path-hint")) {
      const board = campaignBoardValue();
      $("tags-path-hint").textContent =
        `TAGS.txt: ${data.tags_txt || "—"} · board: ${board || "(none)"} · ${railType || "family"}`;
    }
  } catch (e) {
    if ($("tags-path-hint")) $("tags-path-hint").textContent = `Tags: ${e.message}`;
  }
}

function operatorKnown(label) {
  const want = String(label || "").trim().toLowerCase();
  if (!want) return false;
  if (ownersList.some((o) =>
    String(o.label || "").toLowerCase() === want || String(o.id || "").toLowerCase() === want
  )) {
    return true;
  }
  const sel = currentDbSelection();
  return campaignKnown({ ...sel, operator: String(label || "").trim() });
}

let pendingAddOperator = "";
let addingOperator = false;
let campaignPlusKind = "operator";

function existingPackagesForPlus() {
  const sel = currentDbSelection();
  const seen = new Set();
  const out = [];
  const add = (p) => {
    const s = String(p || "").trim();
    if (!s || seen.has(s.toLowerCase())) return;
    seen.add(s.toLowerCase());
    out.push(s);
  };
  const part = sel.part || "";
  for (const comp of Object.keys(dbTree.components || {})) {
    const pkgs = ((((dbTree.components[comp] || {}).parts || {})[part] || {}).packages) || {};
    liveKeys(pkgs).forEach(add);
  }
  (inventoryRows || []).forEach((r) => {
    if (String(r.part || "").toUpperCase() === String(part || "").toUpperCase()) add(r.package);
  });
  return out.sort((a, b) => String(a).localeCompare(String(b)));
}

function existingOperatorsForPlus() {
  const seen = new Set();
  const out = [];
  const add = (name) => {
    const s = String(name || "").trim();
    if (!s || hiddenOperatorName(s) || seen.has(s.toLowerCase())) return;
    seen.add(s.toLowerCase());
    out.push(s);
  };
  (ownersList || []).forEach((o) => {
    if (!o || o.id === "all" || hiddenOwnerRow(o)) return;
    add(o.label || o.id);
  });
  const sel = currentDbSelection();
  const partsObj = ((dbTree.components || {})[sel.component] || {}).parts || {};
  const pkgsObj = (partsObj[sel.part] || {}).packages || {};
  Object.keys(pkgsObj).forEach((pkg) => {
    Object.keys((pkgsObj[pkg] || {}).operators || {}).forEach(add);
  });
  return out.sort((a, b) => String(a).localeCompare(String(b)));
}

function campaignPlusCategory(sel) {
  return typeForFamily(familyFromComponent(sel.component) || activeFamily || railType);
}

function openCampaignPlus(kind, preset) {
  campaignPlusKind = kind === "package" ? "package" : "operator";
  const sel = currentDbSelection();
  if ($("campaign-plus-kind")) {
    $("campaign-plus-kind").textContent = campaignPlusKind === "package" ? "Package" : "Operator";
  }
  if ($("campaign-plus-title")) {
    $("campaign-plus-title").textContent = campaignPlusKind === "package"
      ? "Pick or add package"
      : "Pick or add operator";
  }
  if ($("campaign-plus-body")) {
    $("campaign-plus-body").textContent = campaignPlusKind === "package"
      ? "Default list is packages already on this part (disk + tracking). Type a new name only to create a folder."
      : "Default Setup list is people with a folder on this package. Kevin / ATE stay out. Pick an existing person or type a new name.";
  }
  const names = campaignPlusKind === "package" ? existingPackagesForPlus() : existingOperatorsForPlus();
  const selEl = $("campaign-plus-existing");
  if (selEl) {
    selEl.innerHTML = `<option value="">(pick existing)</option>`
      + names.map((n) => `<option value="${String(n).replace(/"/g, "&quot;")}">${escText(n)}</option>`).join("");
  }
  if ($("campaign-plus-new")) $("campaign-plus-new").value = String(preset || "").trim();
  if ($("campaign-plus-path")) {
    $("campaign-plus-path").textContent =
      `${sel.component || ""} / ${sel.part || ""} / ${sel.package || ""} / ${sel.operator || ""}`;
  }
  if ($("campaign-plus-modal")) $("campaign-plus-modal").classList.remove("hidden");
}

function closeCampaignPlus() {
  if ($("campaign-plus-modal")) $("campaign-plus-modal").classList.add("hidden");
}

async function confirmCampaignPlus() {
  const typed = String(($("campaign-plus-new") && $("campaign-plus-new").value) || "").trim();
  const picked = String(($("campaign-plus-existing") && $("campaign-plus-existing").value) || "").trim();
  const name = typed || picked;
  if (!name) throw new Error("Pick an existing name or type a new one");
  const sel = currentDbSelection();
  if (campaignPlusKind === "package") {
    const operator = requireWriteOperator();
    await rpc("ensure_product", {
      category: campaignPlusCategory(sel),
      part: sel.part,
      package: name,
      model: sel.model || sel.part,
      operator,
      sample_size: Number(($("dut-count") && $("dut-count").value) || 4),
      open_folder: false,
    });
    ingestDbTree(await rpc("list_db_tree"));
    closeCampaignPlus();
    paintCampaign({
      ...sel,
      package: name,
      operator,
      version: sel.version || "Version_1",
    });
    addingOperator = true;
    try { await applyDb(); } finally { addingOperator = false; }
    notice(`Package ${name} ready under ${operator}`);
    return;
  }
  if (hiddenOperatorName(name) || ownerIsObserver(name)) {
    throw new Error("Kevin / ATE / All cannot be campaign operators");
  }
  if (operatorKnown(name)) {
    await rpc("ensure_product", {
      category: campaignPlusCategory(sel),
      part: sel.part,
      package: sel.package,
      model: sel.model || sel.part,
      operator: name,
      sample_size: Number(($("dut-count") && $("dut-count").value) || 4),
      open_folder: false,
    });
    ingestDbTree(await rpc("list_db_tree"));
    closeCampaignPlus();
    paintCampaign({ ...sel, operator: name });
    addingOperator = true;
    try { await applyDb(); } finally { addingOperator = false; }
    notice(`Added ${name} on ${sel.part} ${sel.package}`);
    return;
  }
  closeCampaignPlus();
  openAddOperatorModal(name, currentDbSelection());
}

function addSkuKey(part, pkg) {
  return `${String(part || "").toUpperCase()}|${String(pkg || "").trim()}`;
}

function trackingSkuRows() {
  const seen = new Set();
  const out = [];
  for (const r of inventoryRows || []) {
    const part = String(r.part || "").trim().toUpperCase();
    const pkg = String(r.package || "").trim();
    if (!part) continue;
    const k = addSkuKey(part, pkg);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push({
      part,
      package: pkg,
      category: String(r.category || ""),
      model: String(r.model || ""),
      sheet_class: String(r.sheet_class || ""),
      status: String(r.status || ""),
      pic: String(r.pic || ""),
    });
  }
  return out;
}

function selectedAddOperatorSkus() {
  return [...document.querySelectorAll("#add-operator-products .add-sku-cb:checked")]
    .map((cb) => ({
      part: String(cb.dataset.part || "").toUpperCase(),
      package: String(cb.dataset.package || "").trim(),
      category: String(cb.dataset.category || ""),
      model: String(cb.dataset.model || ""),
    }))
    .filter((r) => r.part);
}

function skuFamilyLabel(cat) {
  const id = String(cat || "");
  if (id === "analog_switch") return familyLabels.switch || "Analog SW";
  return familyLabels[id] || id || "SKU";
}

function paintAddOperatorProducts(sel) {
  const box = $("add-operator-products");
  if (!box) return;
  const s = sel || currentDbSelection();
  const curPart = String(s.part || "").toUpperCase();
  const curPkg = String(s.package || "").trim();
  const rows = trackingSkuRows();
  if (curPart && !rows.some((r) => r.part === curPart && r.package === curPkg)) {
    rows.unshift({
      part: curPart,
      package: curPkg,
      category: typeForFamily(activeFamily || railType),
      model: String(s.model || curPart),
      sheet_class: "This campaign",
      status: "",
    });
  }
  const curFam = typeForFamily(activeFamily || railType);
  const primary = [];
  const other = [];
  for (const r of rows) {
    const fam = r.category || "other";
    const isCur = r.part === curPart && (!curPkg || !r.package || r.package === curPkg);
    if (fam === curFam || isCur || r.sheet_class === "This campaign") primary.push(r);
    else other.push(r);
  }
  const tick = (r) => r.part === curPart && (!curPkg || !r.package || r.package === curPkg);
  const rowHtml = (r) => {
    const bits = [r.part, r.package, r.model].filter(Boolean).join(" · ");
    return `<label class="check"><input type="checkbox" class="add-sku-cb" data-part="${escText(r.part)}" data-package="${escText(r.package)}" data-category="${escText(r.category)}" data-model="${escText(r.model)}" ${tick(r) ? "checked" : ""} /> ${escText(bits)}</label>`;
  };
  const groupHtml = (list) => {
    const by = new Map();
    for (const r of list) {
      const g = r.category || "other";
      if (!by.has(g)) by.set(g, []);
      by.get(g).push(r);
    }
    let html = "";
    for (const [g, listG] of by) {
      html += `<div class="sku-family">${escText(skuFamilyLabel(g))}</div>` + listG.map(rowHtml).join("");
    }
    return html;
  };
  box.innerHTML = groupHtml(primary) + (other.length
    ? `<details><summary>Other tracking SKUs</summary>${groupHtml(other)}</details>`
    : "");
  if (!box.innerHTML) {
    box.innerHTML = `<p class="hint">No tracking SKUs. Apply a campaign Part first, or add a row to inventory.yaml (no website scrape).</p>`;
  }
}

function openAddOperatorModal(label, sel) {
  const name = String(label || "").trim();
  if (!name || ownerIsObserver(name) || name.toLowerCase() === "all") {
    notice("Type a person name in Operator folder (not All / Kevin)");
    return;
  }
  const s = sel || currentDbSelection();
  pendingAddOperator = name;
  if ($("db-operator")) $("db-operator").value = name;
  if ($("add-operator-title")) $("add-operator-title").textContent = `Add ${name}?`;
  if ($("add-operator-body")) {
    $("add-operator-body").textContent =
      `Tick what ${name} handles. Tracking sheet only -- not the RUN-IC website.`;
  }
  paintAddOperatorProducts(s);
  if ($("add-operator-all-skus")) $("add-operator-all-skus").checked = false;
  syncAddOperatorAllSkus();
  if ($("add-operator-path")) {
    const ver = s.version || "Version_1";
    const cur = s.part
      ? `${s.component || ""}/${s.part}/${s.package || ""}/${name}/${ver}`
      : `${name}/${ver}`;
    $("add-operator-path").textContent =
      `Ticks only (this campaign is pre-ticked). Check All SKUs only when you mean every tracking row. Example ${cur.replace(/^\/+/, "")}.`;
  }
  if ($("add-operator-modal")) $("add-operator-modal").classList.remove("hidden");
}

function syncAddOperatorAllSkus() {
  const all = $("add-operator-all-skus") && $("add-operator-all-skus").checked;
  const box = $("add-operator-products");
  if (box) box.style.opacity = all ? "0.45" : "1";
  if (box) box.style.pointerEvents = all ? "none" : "";
}

function closeAddOperatorModal() {
  pendingAddOperator = "";
  if ($("add-operator-modal")) $("add-operator-modal").classList.add("hidden");
}

async function confirmAddOperator() {
  const name = pendingAddOperator || String(($("db-operator") && $("db-operator").value) || "").trim();
  if (!name) throw new Error("Type a person name first");
  const allSkus = !($("add-operator-all-skus")) || $("add-operator-all-skus").checked;
  const skus = selectedAddOperatorSkus();
  if (!allSkus && !skus.length) throw new Error("Tick the product this person handles");
  const nDut = Number(($("dut-count") && $("dut-count").value) || 4);
  const payload = {
    label: name,
    sample_size: nDut,
    with_workbook: true,
  };
  if (!allSkus) payload.only_parts = [...new Set(skus.map((r) => r.part))];
  else payload.all_skus = true;
  const prov = await rpc("provision_operator", payload);
  await loadOwners();
  const row = ownersList.find((o) =>
    String(o.label || "").toLowerCase() === name.toLowerCase()
  );
  if (row && row.id && $("owner-select")) {
    $("owner-select").value = row.id;
    saveOwner(row.id);
  }
  if ($("db-operator")) $("db-operator").value = (row && row.label) || name;
  const sel = currentDbSelection();
  const firstRow = (prov.rows || []).find((r) => r && r.ok) || {};
  const keep = (!allSkus && skus.find((r) => r.part === String(sel.part || "").toUpperCase() && (!sel.package || r.package === sel.package)))
    || skus[0]
    || { part: firstRow.part || sel.part, package: firstRow.package || sel.package, category: firstRow.category, model: firstRow.model };
  const keepComp = componentForCategory(keep.category) || sel.component || "";
  const keepFam = familyFromComponent(keepComp) || String(keep.category || "");
  if (keep.part) {
    await rpc("upsert_owner", {
      label: (row && row.label) || name,
      update_defaults: true,
      default_part: String(keep.part || "").toLowerCase(),
      default_package: keep.package || sel.package || "",
      default_component: keepComp,
      default_family: keepFam,
      task: String(keep.part || ""),
    });
    await loadOwners();
  }
  paintCampaign({
    component: componentForCategory(keep.category) || sel.component || "",
    part: keep.part,
    package: keep.package || sel.package || "",
    operator: (row && row.label) || name,
    version: sel.version || "Version_1",
    model: keep.model || keep.part,
    year: ($("db-year") && $("db-year").value) || "2026",
  });
  closeAddOperatorModal();
  addingOperator = true;
  try {
    await applyDb();
  } finally {
    addingOperator = false;
  }
  const n = Number(prov.ok_count || prov.count || 0);
  const logs = (prov.logs && prov.logs.xlsx) ? " · log xlsx in _ate" : "";
  notice(`Added ${name} · ${n} SKU folders + golden workbooks${logs}`);
}

async function provisionPersonFromSetup() {
  const label = requireWriteOperator();
  const nDut = Number(($("dut-count") && $("dut-count").value) || 4);
  const prov = await rpc("provision_operator", {
    label,
    sample_size: nDut,
    with_workbook: true,
    all_skus: true,
  });
  await loadOwners();
  paintPersonSkuChips();
  const n = Number(prov.ok_count || prov.count || 0);
  notice(`${label}: ${n} tracking SKUs + golden workbooks (see _ate log)`);
}

async function applyDb() {
  const sel = currentDbSelection();
  const typed = String(sel.operator || "").trim();
  if (
    !addingOperator &&
    typed &&
    !operatorKnown(typed) &&
    !ownerIsObserver(typed) &&
    typed.toLowerCase() !== "all"
  ) {
    openAddOperatorModal(typed, sel);
    return;
  }
  if (typed && operatorKnown(typed) && !ownerIsObserver(typed)) {
    syncOwnerSelectFromFolder(typed);
  }
  const operator = requireWriteOperator();
  let busy = runPollActive;
  if (!busy) {
    try {
      const st = await rpc("session_status");
      busy = !!(st && st.busy);
    } catch (_) { /* worker may be starting */ }
  }
  if (busy) {
    notice("Run in progress -- campaign locked. Logic/RS1GT34 will not switch to AnalogSwitch until DONE.");
    log("Campaign locked (runner busy) -- UI fields local only\n");
    return;
  }
  const existing = versionsForSel({ ...sel, operator });
  if (sel.version && !existing.includes(sel.version)) {
    try {
      await rpc("ensure_version", {
        component: sel.component,
        part: sel.part,
        package: sel.package,
        operator,
        version: sel.version,
        copy_from_version: (dbContext && dbContext.version) || existing[existing.length - 1] || "",
        sample_size: Number((dbContext && dbContext.sample_size) || 4),
        open_folder: false,
        apply: false,
      });
      ingestDbTree(await rpc("list_db_tree"));
      mergeInventoryIntoTree();
    } catch (e) {
      const msg = String((e && e.message) || e);
      if (!/already exists/i.test(msg)) log(`Version: ${msg}\n`);
    }
  }
  const res = await rpc("set_db_context", {
    component: sel.component,
    part: sel.part,
    package: sel.package,
    operator,
    version: sel.version,
    model: sel.model || undefined,
    year: sel.year || undefined,
  });
  if (res.busy_locked) {
    notice(res.family_error || "Run in progress -- campaign locked");
    if (res.context && res.context.part) {
      paintCampaign({
        component: res.context.component,
        part: res.context.part,
        package: res.context.package,
        operator: res.context.operator,
        version: res.context.version,
        model: res.context.model || res.context.part,
        year: res.context.year || sel.year,
      });
    }
    renderDbHints(res.context);
    return;
  }
  renderDbHints(res.context);
  saveCampaign({ ...sel, operator, ...(res.context || {}) });
  log(`Campaign applied: ${res.context.root}\n`);
  if (res.created?.length) {
    log(`Created ${res.created.length} folder(s) under DUT tree\n`);
  }
  if (res.family_error) {
    log(`${res.family_error}\n`);
  }
  if ("family" in res) updateFamilyChrome(res.family);
  await loadOwners();
  await loadParamDefaults();
  await loadFixtureCatalog();
  await loadTests();
  await loadMappedCoverage();
  await refreshDetectedPanel();
  await refreshCampaignTests();
  await refreshTagsUI();
  syncOwnerSelectFromFolder(operator);
}

function fillDetectFamilySelect() {
  const el = $("detect-family");
  if (!el) return;
  let fam = (activeFamily || "logic").toLowerCase();
  if (fam === "lim") fam = "switch";
  fillSelect(el, [fam], fam);
  el.disabled = true;
}

function closeTestsMenu() {
  const m = $("tests-menu-modal");
  if (m) m.classList.add("hidden");
}

function openTestsMenu() {
  requireWriteOperator();
  const m = $("tests-menu-modal");
  if (m) m.classList.remove("hidden");
}

function goTestsPage(section) {
  closeTestsMenu();
  switchPage("detect");
  const map = {
    gaps: "panel-version-gaps",
    scan: "panel-detect-scan",
    enable: "panel-campaign-tests",
    prompt: "panel-ate-prompt",
    write: "panel-write-test",
  };
  const el = $(map[section] || "panel-campaign-tests");
  if (el && el.scrollIntoView) el.scrollIntoView({ block: "start" });
}

function campaignPromptSlots() {
  const sel = currentDbSelection();
  const tid = String(
    ($("prompt-test-id") && $("prompt-test-id").value)
    || ($("path-b-id") && $("path-b-id").value)
    || ""
  ).trim();
  return {
    path: String(($("prompt-path") && $("prompt-path").value) || "b"),
    operator: writeOperatorLabel() || "",
    family: activeFamily || "logic",
    part: sel.part || "",
    package: sel.package || "",
    version: sel.version || "Version_1",
    test_id: tid,
  };
}

async function fillAtePrompt() {
  const res = await rpc("cursor_prompt", campaignPromptSlots());
  if ($("prompt-preview")) $("prompt-preview").value = res.text || "";
  return res.text || "";
}

async function copyAtePrompt() {
  const text = await fillAtePrompt();
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    const ta = $("prompt-preview");
    if (ta) {
      ta.focus();
      ta.select();
      document.execCommand("copy");
    }
  }
  log("Copied Cursor prompt (Path " + String(campaignPromptSlots().path).toUpperCase() + ")\n");
}

async function loadPathBTemplate() {
  const tid = String(($("path-b-id") && $("path-b-id").value) || "").trim();
  const res = await rpc("path_b_template", {
    test_id: tid,
    label: String(($("path-b-label") && $("path-b-label").value) || ""),
    family: activeFamily || "logic",
  });
  if ($("path-b-id") && res.id) $("path-b-id").value = res.id;
  if ($("path-b-edit")) $("path-b-edit").value = res.text || "";
  if ($("path-b-hint")) $("path-b-hint").textContent = res.file || "ate/tests/<family>/<id>.py";
  if ($("prompt-test-id") && res.id) $("prompt-test-id").value = res.id;
}

async function savePathBFile() {
  requireWriteOperator();
  const tid = String(($("path-b-id") && $("path-b-id").value) || "").trim();
  if (!tid) {
    alert("Type a test id (lowercase slug)");
    return;
  }
  const sel = currentDbSelection();
  const res = await rpc("save_path_b_test", {
    test_id: tid,
    label: String(($("path-b-label") && $("path-b-label").value) || ""),
    text: String(($("path-b-edit") && $("path-b-edit").value) || ""),
    family: activeFamily || "logic",
    part: sel.part || "",
    enable_part: sel.part || "",
  });
  log(`Saved Path B ${res.id} -> ${res.file}\nIdle-restart worker (~20 s) then DEMO ${res.id}.\n`);
  if ($("path-b-hint")) {
    $("path-b-hint").textContent = `Saved ${res.file}. Idle-restart worker, then DEMO ${res.id}.`;
  }
  await refreshCampaignTests();
  await loadTests();
}

async function openPathBEditor(tid) {
  requireWriteOperator();
  const id = String(tid || "").trim();
  if ($("path-b-id")) $("path-b-id").value = id;
  if ($("prompt-test-id")) $("prompt-test-id").value = id;
  const t = (allTests || []).find((x) => x.id === id);
  const file = t && t.source && t.source.file;
  goTestsPage("write");
  if (file) {
    const res = await rpc("snippet_source", { file, fn: (t.source && t.source.fn) || "" });
    if ($("path-b-edit")) $("path-b-edit").value = res.text || "";
    if ($("path-b-hint")) $("path-b-hint").textContent = res.file || file;
    if ($("snippet-edit")) {
      $("snippet-edit").value = res.text || "";
      $("snippet-edit").dataset.file = file;
    }
    log(`Loaded source ${String(res.file || file).replace(/\\/g, "/").split("/").slice(-2).join("/")}\n`);
    return;
  }
  await loadPathBTemplate();
}

let campaignTestsGen = 0;

function campaignTestOrderIds() {
  const box = $("campaign-tests");
  if (!box) return [];
  return Array.from(box.querySelectorAll(".test-item"))
    .map((row) => {
      const cb = row.querySelector(".campaign-test-cb");
      return cb && cb.checked ? cb.value : null;
    })
    .filter(Boolean);
}

function initCampaignTestReorder() {
  const box = $("campaign-tests");
  if (!box || box._reorderBound) return;
  box._reorderBound = true;
  let dragEl = null;
  box.addEventListener("dragstart", (e) => {
    const handle = e.target.closest(".campaign-drag-handle");
    if (!handle) {
      e.preventDefault();
      return;
    }
    dragEl = handle.closest(".test-item");
    if (!dragEl) {
      e.preventDefault();
      return;
    }
    dragEl.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  box.addEventListener("dragend", () => {
    if (dragEl) dragEl.classList.remove("dragging");
    dragEl = null;
  });
  box.addEventListener("dragover", (e) => {
    if (!dragEl) return;
    e.preventDefault();
    const row = e.target.closest(".test-item");
    if (!row || row === dragEl) return;
    const rect = row.getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    if (after) row.after(dragEl);
    else row.before(dragEl);
  });
}

async function refreshCampaignTests() {
  const box = $("campaign-tests");
  const hint = $("campaign-tests-hint");
  const gaps = $("version-gaps");
  const gapsHint = $("version-gaps-hint");
  if (!box) return;
  const gen = ++campaignTestsGen;
  try {
    const res = await rpc("list_campaign_tests");
    if (gen !== campaignTestsGen) return;
    box.innerHTML = "";
    if (!res.ok) {
      const p = document.createElement("p");
      p.className = "hint";
      p.textContent = res.error || "Pick a person (not All).";
      box.appendChild(p);
      if (hint) hint.textContent = res.error || "";
      if (gaps) gaps.innerHTML = "";
      return;
    }
    const rows = res.available || [];
    if (!rows.length) {
      const p = document.createElement("p");
      p.className = "hint";
      p.textContent = "No tests in this category. Wrap a golden on this page or add a TestSpec.";
      box.appendChild(p);
    } else {
      rows.forEach((t) => {
        const div = document.createElement("div");
        div.className = "test-item campaign-test-row";
        const handle = document.createElement("span");
        handle.className = "campaign-drag-handle";
        handle.textContent = "::";
        handle.title = "Drag to reorder (Save this Version keeps list order)";
        handle.setAttribute("draggable", "true");
        handle.setAttribute("aria-hidden", "true");
        const lab = document.createElement("label");
        lab.style.display = "flex";
        lab.style.gap = "8px";
        lab.style.alignItems = "flex-start";
        lab.style.width = "100%";
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "campaign-test-cb";
        cb.value = t.id;
        cb.checked = !!t.on;
        const span = document.createElement("span");
        const strong = document.createElement("strong");
        strong.textContent = t.id;
        span.appendChild(strong);
        span.appendChild(document.createTextNode(" -- " + (t.label || t.id)));
        const mode = document.createElement("span");
        mode.className = "hint";
        mode.textContent = t.fixture_mode || "";
        span.appendChild(document.createElement("br"));
        span.appendChild(mode);
        div.appendChild(handle);
        lab.appendChild(cb);
        lab.appendChild(span);
        div.appendChild(lab);
        box.appendChild(div);
      });
      initCampaignTestReorder();
    }
    if (hint) {
      hint.textContent =
        `${res.operator || ""} / ${res.part || ""} / ${res.version || ""} · ${res.current_from || ""} · ${res.family || ""}`;
    }
    if (gaps) {
      gaps.innerHTML = "";
      const missing = res.missing || [];
      const skipped = res.skipped_operators || [];
      const vers = res.versions || [];
      const p = document.createElement("p");
      p.className = "hint";
      p.textContent = missing.length
        ? `Missing vs my versions / part yaml: ${missing.join(", ")}`
        : "No gaps vs this person's versions or the part yaml.";
      gaps.appendChild(p);
      vers.forEach((v) => {
        const row = document.createElement("p");
        row.className = "hint";
        row.textContent = `${v.version}: ${(v.enabled_tests || []).join(", ") || "(none)"}`;
        gaps.appendChild(row);
      });
      if (skipped.length) {
        const row = document.createElement("p");
        row.className = "hint";
        row.textContent = "Not merged (other people / skip): " +
          skipped.map((s) => `${s.operator} (${s.reason})`).join(", ");
        gaps.appendChild(row);
      }
    }
    if (gapsHint) {
      gapsHint.textContent = "Other people's tests are not copied.";
    }
    applyCampaignTestSearch();
  } catch (e) {
    box.innerHTML = "";
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = e.message;
    box.appendChild(p);
  }
}

async function refreshDetectedPanel(opts) {
  const box = $("detected-tests");
  const hint = $("detect-hint");
  if (!box) return;
  syncDetectAuthorLock();
  fillDetectFamilySelect();
  try {
    const res = await rpc("list_detected_tests", {
      family: activeFamily,
      operator: writeOperatorLabel() || (($("db-operator") && $("db-operator").value) || ""),
      author: detectAuthorParam(),
      allow_others: othersGoldensAllowed(),
    });
    const mapRow = (r, matched) => ({
      ...r,
      matched: !!matched,
      product: r.product || productGuessFromFile(r.file),
    });
    detectedCache = [
      ...(res.detected || []).map((r) => mapRow(r, false)),
      ...(res.located || []).map((r) => mapRow(r, true)),
    ];
    fillDetectProductSelect();
    paintDetectedRows(res, box, hint);
  } catch (e) {
    detectedCache = [];
    box.innerHTML = "";
    if (hint) hint.textContent = `Detect scan: ${e.message}`;
  }
}

function detectDupGroup(id) {
  const c = String(id || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  const groups = [
    ["input_threshold", "input_thresholds", "vih_vil", "vih", "vil"],
  ];
  for (const g of groups) {
    if (g.some((x) => x.replace(/[^a-z0-9]/g, "") === c)) return g[0];
  }
  return "";
}

function filterDetectDupes(rows) {
  const out = [];
  const seen = new Set();
  for (const r of rows) {
    const g = detectDupGroup(r.id);
    const prod = String(r.product || "").toUpperCase();
    const key = g ? `${g}::${prod}` : "";
    if (key && seen.has(key)) continue;
    if (key) seen.add(key);
    out.push(r);
  }
  return out;
}

function fillDetectProductSelect() {
  const el = $("detect-product");
  if (!el) return;
  const keep = String(el.value || "");
  const campaign = String(($("db-part") && $("db-part").value) || "").trim().toUpperCase();
  const products = [];
  const seen = new Set();
  for (const r of detectedCache) {
    if (!sameDetectFamily(r.family_guess)) continue;
    const p = String(r.product || "").trim().toUpperCase();
    if (!p || seen.has(p)) continue;
    seen.add(p);
    products.push(p);
  }
  products.sort();
  el.innerHTML = `<option value="">All in this category</option>` +
    products.map((p) => `<option value="${escText(p)}">${escText(p)}</option>`).join("");
  if (keep && [...el.options].some((o) => o.value === keep)) {
    el.value = keep;
  } else if (campaign && seen.has(campaign)) {
    el.value = campaign;
  } else {
    el.value = "";
  }
}

function paintDetectedRows(scanMeta, box, hint) {
  const root = box || $("detected-tests");
  const hintEl = hint || $("detect-hint");
  if (!root) return;
  const q = String(($("detect-search") && $("detect-search").value) || "").trim();
  const product = String(($("detect-product") && $("detect-product").value) || "").trim().toUpperCase();
  const famRows = detectedCache.filter((r) => sameDetectFamily(r.family_guess));
  const rows = filterDetectDupes(famRows.filter((r) => {
    if (product && String(r.product || "").toUpperCase() !== product) return false;
    const shortFile = String(r.file || "").replace(/\\/g, "/").split("/").slice(-2).join("/");
    return textBlobMatch(q, r.id, r.fn, r.label, shortFile, r.product, r.family_guess, r.trigger, r.blocked_reason, r.author);
  }));
  root.innerHTML = "";
  if (!detectedCache.length) {
    root.innerHTML = '<p class="hint">No test_* snippets found (or golden roots missing).</p>';
  } else if (!rows.length) {
    root.innerHTML = '<p class="hint">No snippet rows match this category / product / search. Switch Product to All in this category.</p>';
  } else {
    rows.slice(0, 80).forEach((r) => {
      const div = document.createElement("div");
      div.className = "test-item";
      const matched = !!r.matched;
      const inputBridge = !!r.input_bridge && !matched;
      const blocked = !!r.blocked && !matched && !inputBridge;
      const shortFile = String(r.file || "").replace(/\\/g, "/").split("/").slice(-2).join("/");
      const prod = r.product ? ` · ${r.product}` : "";
      const who = r.author ? ` · ${r.author}` : "";
      const tag = matched
        ? `${r.trigger || "trigger"}${prod}${who}`
        : (blocked ? `blocked${prod}${who}` : (inputBridge ? `continue-bridge${prod}${who}` : `ready${prod}${who}`));
      const reason = matched
        ? "already in registry"
        : (blocked ? (r.blocked_reason || "blocked") : (inputBridge ? "input() -> Continue on START; original kept" : "trigger-ready"));
      div.innerHTML =
        `<label style="display:flex;gap:8px;align-items:flex-start;width:100%">` +
        `<input type="checkbox" class="detect-cb" data-id="${r.id}" data-fn="${r.fn || ""}" ` +
        `data-file="${encodeURIComponent(r.file || "")}" data-bridge="${inputBridge ? "1" : ""}" ` +
        `data-author="${escText(r.author || "")}" ` +
        `${blocked ? "disabled" : ""} />` +
        `<span><strong>${r.id}</strong> <span class="hint">(${tag})</span><br/>` +
        `<span class="hint">${shortFile}:${r.lineno || "?"} -- ${reason}</span></span></label>`;
      root.appendChild(div);
    });
  }
  const missing = ((scanMeta && scanMeta.roots) || []).filter((x) => !x.exists).map((x) => x.label || x.path);
  const locatedN = detectedCache.filter((r) => r.matched).length;
  if (hintEl && scanMeta) {
    hintEl.textContent =
      `Scanned ${scanMeta.scanned_files || 0} files -> ${scanMeta.count || 0} unmatched` +
      (locatedN ? `, ${locatedN} located` : "") +
      (scanMeta.blocked_count ? ` (${scanMeta.blocked_count} blocked)` : "") +
      ` · showing ${rows.length} in ${detectFamilyKey()}` +
      (product ? ` / ${product}` : "") +
      (missing.length ? `. Missing golden: ${missing.join(", ")}` : ".");
  } else if (hintEl) {
    hintEl.textContent = `Showing ${rows.length} snippet row(s) in ${detectFamilyKey()}` +
      (product ? ` / ${product}` : "") + ".";
  }
}

function paramNumInput(key, label, value, step) {
  const v = value == null || value === "" ? "" : value;
  return `<label>${label}<input data-param="${key}" type="number" step="${step}" value="${v}" /></label>`;
}

function testParamEditorHtml(t) {
  const p = t.params || {};
  const d = t.defaults || (paramCatalog.tests && paramCatalog.tests[t.id]) || {};
  const meta = testSweepMeta(t);
  const fields = [];
  const notes = [];
  const stim = (t.stimulus && t.stimulus.wave) ? String(t.stimulus.wave).toUpperCase() : "";
  const awgWave = ["SQU", "SIN", "PULS", "RAMP", "NOIS"].includes(stim);
  const showAwgParams = testNeedsAwg(t) || awgWave;
  const awgOff = !showAwgParams;
  if (meta.kind === "freq") {
    fields.push(paramNumInput("freq_start", "Freq start (MHz)", p.freq_start ?? 1, 0.5));
    fields.push(paramNumInput("freq_stop", "Freq stop (MHz)", p.freq_stop ?? 10, 0.5));
    fields.push(paramNumInput("freq_step", "Freq step (MHz)", p.freq_step ?? 4, 0.5));
    fields.push(paramNumInput("vcc", "VCC (V)", p.vcc ?? d.vcc ?? 5, 0.1));
  } else if (meta.kind === "vcc" || meta.kind === "vcom" || meta.kind === "vin") {
    fields.push(paramNumInput("vcc_start", "VCC start (V)", p.vcc_start ?? d.vcc_start ?? 0, 0.01));
    fields.push(paramNumInput("vcc_stop", "VCC stop (V)", p.vcc_stop ?? d.vcc_stop ?? 5, 0.01));
    fields.push(paramNumInput("vcc_step", "VCC step (V)", p.vcc_step ?? d.vcc_step ?? 0.01, 0.01));
    if (t.id === "vih_vil" || t.id === "input_thresholds") {
      fields.push(paramNumInput("vin_step", "VIN trip step (V)", p.vin_step ?? d.vin_step ?? 0.01, 0.001));
      notes.push("Logic VCC 4.5-5.5: step 0.01 is valid. Voltage records 0.XXX then rounds. Current keeps full DMM (no round).");
    }
    if (meta.kind === "vcom") notes.push("VCOM 0 / half / V+ at each VCC step.");
    if (meta.id === "delta_supply_current") {
      notes.push("Delta Supply sweeps this VCC range. AWG CH1 then CH2 alternate at each step.");
    }
  } else {
    fields.push(paramNumInput("vcc", "VCC (V)", p.vcc ?? d.vcc ?? 5, 0.1));
  }
  const dcIds = ["icc", "delta_icc", "ii", "ioz", "input_threshold", "voh", "vol"];
  if (dcIds.includes(t.id)) {
    const modeKey = t.id === "icc" ? "icc_vcc_mode" : "vcc_mode";
    const modeVal = String(p[modeKey] || p.vcc_mode || p.icc_vcc_mode || (t.id === "icc" ? "named" : "") || "");
    const namedSel = modeVal === "named" ? " selected" : "";
    const stepSel = modeVal === "step" ? " selected" : "";
    const listSel = modeVal === "list" ? " selected" : "";
    fields.push(`<label>VCC plan<select data-param="${modeKey}"><option value="">default</option><option value="named"${namedSel}>named points</option><option value="step"${stepSel}>0.1 V step</option><option value="list"${listSel}>custom list</option></select></label>`);
    if (t.id === "icc" || meta.kind !== "vcc") {
      fields.push(paramNumInput("vcc_start", "VCC start (V)", p.vcc_start ?? d.vcc_start ?? 2.0, 0.1));
      fields.push(paramNumInput("vcc_stop", "VCC stop (V)", p.vcc_stop ?? d.vcc_stop ?? 5.5, 0.1));
      fields.push(paramNumInput("vcc_step", "VCC step (V)", p.vcc_step ?? p.icc_vcc_step ?? d.vcc_step ?? 0.1, 0.1));
    }
  }
  if (t.id === "ii") {
    notes.push("II Connected: DMM series the measured input. 2^n AWG combos at 0/5.5 (GT34=2, 1G08=4). Default named 2.0/3.3/5.5. Parameters step 0-5.6/0.1 is the golden sweep (VCC=0 is Ioff-like). No TRAC, no PSU-off between VCC. Stamp II_uA not IDD.");
  }
  if (t.id === "ioz") {
    notes.push("IOZ: OE inactive. PSU+DMM. Not IOFF (VCC=0). One body in logic_dc.py.");
  }
  if (t.id === "ioff" || t.id === "ioff_leakage") {
    const startVal = String(p.ioff_start || d.ioff_start || "ports").toLowerCase();
    const pick = (v) => (startVal === v ? " selected" : "");
    fields.push(`<label>DMM first pin<select data-param="ioff_start"><option value="ports"${pick("ports") || pick("")}>A then Y then VCC</option><option value="A"${pick("a")}>A first</option><option value="Y"${pick("y")}>Y first</option><option value="vcc"${pick("vcc")}>VCC first</option></select></label>`);
    notes.push("Ioff Connected: VCC=0 (unpowered). Output counts as a port. GT34 A+Y = 2 ports, 4 force combos 0/5.5. Measure n+1. Pick which pin is first (A / Y / VCC); the rest follow. PSU CH2 forces Y (not the 10 ohm load). Not IOZ.");
  }
  if (t.id === "icc" || t.id === "delta_icc" || t.id === "supply_current_sweep") {
    notes.push("ICC Connected: DMM in series with VCC. IO=0 -- disconnect 10 ohm Y-load, PSU CH2 OFF. GT34 default is datasheet 2.0-5.5 / 0.1 (36 VCC x 2 corners). Named 2.0/3.3/5.5 is a short overlay. Golden 0-5.6 is Parameters start=0 stop=5.6 (Ioff + over-recommended). Golden IDD: 2 s after each VCC, 1 s after VI, then average 5 DMM reads. ICCT is A=3.4 from 3.0-5.5 / 0.1 (datasheet spec row is 5.5 / 500 uA). Scope JPEG is optional -- ICC does not need MSO.");
    fields.push(paramNumInput("vcc_dwell_s", "VCC dwell (s)", p.vcc_dwell_s ?? d.vcc_dwell_s ?? "", 0.5));
    fields.push(paramNumInput("icc_samples", "DMM samples", p.icc_samples ?? d.icc_samples ?? "", 1));
  }
  if (t.id === "voh_load" || t.id === "vol_load") {
    const flag = t.id === "vol_load" ? "vol_100ua" : "voh_100ua";
    const on = Number(p[flag] ?? d[flag] ?? 0) ? " checked" : "";
    fields.push(`<label><input data-param="${flag}" type="checkbox"${on} /> Include 100 uA (needs current source/sink)</label>`);
    fields.push(paramNumInput("load_r_ohm", "Load R (ohm)", p.load_r_ohm ?? d.load_r_ohm ?? 10, 1));
    notes.push("Corners are the datasheet table (8/24/32 mA through the soldered resistor). Do not use VCC start/stop as a dense sweep. Tick 100 uA only after the current source can sink/source 100 uA.");
  }
  const vccListVal = Array.isArray(p.vcc_list) ? p.vcc_list.join(", ") : (p.vcc_list || "");
  fields.push(`<label>VCC list (optional)<input data-param="vcc_list" type="text" placeholder="1.65, 3.3, 3.5" value="${escText(vccListVal)}" title="Wins over start/stop/step when set" /></label>`);
  fields.push(`<label>Inputs n (2^n)<input data-param="logic_inputs" type="number" step="1" min="1" max="8" value="${escText(p.logic_inputs ?? d.logic_inputs ?? "")}" title="Corners = levels^n; AWG drives 2 CH" /></label>`);
  const levelsVal = Array.isArray(p.levels) ? p.levels.join(", ") : (p.levels || "");
  fields.push(`<label>Levels<input data-param="levels" type="text" placeholder="0, 5.5" value="${escText(levelsVal)}" title="Corner levels for product(levels, n)" /></label>`);
  const rails = p.rails || {};
  const railsMode = rails.mode || p.rails_mode || "";
  fields.push(`<label>Rails<select data-param="rails_mode"><option value="">--</option><option value="single"${railsMode === "single" ? " selected" : ""}>single</option><option value="dual"${railsMode === "dual" ? " selected" : ""}>dual</option></select></label>`);
  let railsPsu = p.rails_psu || "";
  if (!railsPsu && Array.isArray(rails.psu)) {
    railsPsu = rails.psu.map((r) => {
      const bits = [r.ch];
      if (r.name) bits.push(r.name);
      if (r.volts != null) bits.push(Number(r.volts).toFixed(r.digits != null ? Number(r.digits) : 3));
      return bits.join(":");
    }).join(", ");
  }
  fields.push(`<label>PSU CH volts<input data-param="rails_psu" type="text" placeholder="1:VCC:3.300, 2:VSS:-3.300" value="${escText(railsPsu)}" title="ch:name:volts or ch:volts" /></label>`);
  notes.push("VCC list wins over start/stop/step. Inputs n = 2^n AWG input corners (DG822 CH1/CH2 only). MSO stays 2 probes (CH1=stim CH2=Y) -- never extra scope channels. n>2 Continue rewire.");
  if (d.vccb != null || p.vccb != null) {
    fields.push(paramNumInput("vccb", "VCCB (V)", p.vccb ?? d.vccb, 0.1));
  }
  if (!awgOff && meta.kind !== "freq") {
    fields.push(paramNumInput("freq_hz", "Freq (Hz)", p.freq_hz ?? d.freq_hz ?? 500, 1));
  }
  if (!awgOff) {
    fields.push(paramNumInput("amp_vpp", "Amp Vpp", p.amp_vpp ?? d.amp_vpp ?? 0.004, 0.001));
    fields.push(paramNumInput("n_repeats", "Repeats", p.n_repeats ?? d.n_repeats ?? 1, 1));
  }
  const specRows = (t.specs || []).map((s) => {
    const sid = escText(s.id || "");
    const min = s.min != null ? s.min : "";
    const max = s.max != null ? s.max : "";
    const typ = s.typ != null ? s.typ : "";
    const unit = escText(s.unit || "");
    return `<div class="spec-edit" data-spec-id="${sid}">
      <span class="hint">${sid}</span>
      <label>min<input data-spec-field="min" type="number" step="any" value="${min}" /></label>
      <label>max<input data-spec-field="max" type="number" step="any" value="${max}" /></label>
      <label>typ<input data-spec-field="typ" type="number" step="any" value="${typ}" /></label>
      <label>unit<input data-spec-field="unit" type="text" value="${unit}" /></label>
    </div>`;
  }).join("");
  let src = "";
  if (t.source && t.source.kind === "wrap" && t.source.file) {
    const shortSrc = String(t.source.file).replace(/\\/g, "/").split("/").slice(-2).join("/");
    src = `<p class="hint">wrap ${escText(shortSrc)}:${t.source.lineno || "?"}</p>`;
  }
  fields.push(paramNumInput("settle_s", "Settle (s)", p.settle_s ?? d.settle_s ?? "", 0.1));
  fields.push(paramNumInput("timeout_s", "Timeout (s)", p.timeout_s ?? d.timeout_s ?? "", 0.5));
  fields.push(paramNumInput("dwell_s", "Dwell (s)", p.dwell_s ?? d.dwell_s ?? "", 0.1));
  const req = (t.required_instruments || []).map((x) => String(x).toUpperCase());
  const needsDmm = req.includes("DMM");
  const needsMso = req.includes("MSO") || req.includes("SCOPE");
  let shot = String(p.screenshot_from || d.screenshot_from || "").toLowerCase();
  if (!shot && p.include_screenshot) shot = needsMso ? "mso" : (needsDmm ? "dmm" : "none");
  if (!shot) shot = needsDmm && !needsMso ? "dmm" : "none";
  if ((shot === "mso" || shot === "scope") && !needsMso && needsDmm) shot = "dmm";
  const shotNone = shot === "" || shot === "none" ? " selected" : "";
  const shotMso = shot === "mso" || shot === "scope" ? " selected" : "";
  const shotDmm = shot === "dmm" ? " selected" : "";
  let shotOpts = `<option value="none"${shotNone}>none</option>`;
  if (needsMso) shotOpts += `<option value="mso"${shotMso}>MSO / scope</option>`;
  if (needsDmm) shotOpts += `<option value="dmm"${shotDmm}>DMM</option>`;
  if (!needsMso && !needsDmm) shotOpts += `<option value="mso"${shotMso}>MSO / scope</option>`;
  fields.push(`<label>Include screenshot<select data-param="screenshot_from">${shotOpts}</select></label>`);
  notes.push("Settle/dwell override USB waits (dwell wins on DMM delta steps). ICC/ICCT ignore 0.05 s settle_s -- they use VCC dwell 2 s / VI dwell 1 s / 5 samples unless you set VCC dwell or Dwell above.");
  notes.push("Include screenshot: pick the box on the bench. IOZ/ICC = DMM (HCOP leftover = reading card), never MSO. Timing = MSO JPEG. Write to save this Version.");
  if (String(t.id || "").toLowerCase() === "ioz") {
    notes.unshift("IOZ RS1G126: pin1 OE / pin2 A strap GND / pin3 GND / pin4 Y / pin5 VCC. PSU CH1=VCC pin5, CH2=Y pin4 through DMM DCI, CH3=OE pin1 inactive L. AWG off. MSO unplugged. Probe CHA (Setup tick B only if you recable). Screenshot select = DMM (Write).");
  }
  if (meta.hint) notes.unshift(meta.hint);
  const noteHtml = notes.map((n) => `<p class="hint">${escText(n)}</p>`).join("");
  const waveLine = stim
    ? (showAwgParams
      ? `<p class="hint">Stimulus AWG ${escText(stim)}${t.stimulus.detail ? " -- " + escText(t.stimulus.detail) : ""}</p>`
      : `<p class="hint">Stimulus ${escText(stim)}${t.stimulus.detail ? " -- " + escText(t.stimulus.detail) : ""}</p>`)
    : `<p class="hint">Stimulus: no AWG (PSU/DMM only)</p>`;
  return `<details class="test-spec-edit">
    <summary>Parameters (this Version) -- click to expand</summary>
    ${src}${waveLine}${noteHtml}
    <div class="param-grid">${fields.join("")}</div>
    ${specRows ? `<p class="hint">Limits / specifications (this Version)</p>${specRows}` : ""}
    <div class="test-spec-write-row">
      <button type="button" class="btn ghost test-param-write" data-test-id="${escText(t.id)}">Write</button>
      <button type="button" class="btn ghost test-edit-source" data-test-id="${escText(t.id)}">Edit source</button>
    </div>
  </details>`;
}

async function loadTests() {
  const tests = await rpc("list_tests");
  allTests = tests;
  const box = $("test-list");
  box.innerHTML = "";
  if (!tests.length) {
    const stub =
      activeFamily === "level"
        ? "No enabled tests for this Level part. Pick RS0204 for the dual-rail suite."
          : activeFamily === "logic"
          ? "Logic family loaded -- no enabled tests for this part/campaign."
          : (activeFamily === "lim" || activeFamily === "switch")
            ? "Analog Switch family loaded -- no enabled tests for this part/campaign."
            : activeFamily === "power"
              ? "Power / LDO family loaded -- no enabled tests for this part/campaign."
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
    const items = sortTestsForPlan(groups.get(mode) || []);
    const cat = fixtureCatalog.find((m) => m.mode === mode);
    const isResearch = (cat?.board_class || (mode === "G201" || mode === "G1001" ? "research" : "general")) === "research";
    const gainTxt = cat && cat.gain != null ? ` · gain ${formatGain(cat.gain)}` : "";
    const label = cat?.label || mode;
    const wrap = document.createElement("details");
    wrap.className = "fixture-group" + (isResearch ? " research" : "");
    wrap.open = true;
    wrap.innerHTML = `<summary class="fixture-group-title">${mode}${gainTxt} — ${label}</summary>`;
    const grid = document.createElement("div");
    grid.className = "fixture-group-tests";
    for (const t of items) {
      const id = `t-${t.id}`;
      const checked = !isResearch && preferred.has(t.id) ? "checked" : "";
      const tag = t.short_tag || t.id;
      const instr = (t.required_instruments || []).join("+") || "MSO+PSU+AWG";
      const specBits = (t.specs || []).map((s) => {
        const bits = [s.id || ""];
        if (s.min != null) bits.push(`min ${s.min}`);
        if (s.max != null) bits.push(`max ${s.max}`);
        if (s.typ != null) bits.push(`typ ${s.typ} ${s.unit || ""}`.trim());
        return bits.join(" ");
      }).join("; ");
      const info = (t.info && (t.info.description || t.info.title)) || t.notes || "";
      const specLine = specBits || "datasheet unspec -- Results: Fetch limits";
      const stim = (t.stimulus && t.stimulus.wave) ? String(t.stimulus.wave).toUpperCase() : "";
      const stimHead = stimPrefix(t);
      const stimLine = stim
        ? `${stim}${t.stimulus.detail ? " · " + t.stimulus.detail : ""}`
        : "";
      const extra = [stimLine, info, specLine].filter(Boolean).join(" · ");
      let srcLine = "";
      if (t.source && t.source.kind === "wrap" && t.source.file) {
        const shortSrc = String(t.source.file).replace(/\\/g, "/").split("/").slice(-2).join("/");
        srcLine = `<br/><span class="hint">wrap ${shortSrc}:${t.source.lineno || "?"}</span>`;
      }
      grid.innerHTML += `
        <div class="test-item" data-test-id="${t.id}">
          <label class="test-item-head" for="${id}" title="${extra.replace(/"/g, "&quot;")}">
            <input id="${id}" type="checkbox" value="${t.id}" ${checked} />
            <span><strong>${tag}</strong> — ${t.label}<br/><span class="mode-tag">${stimHead ? (stimHead + " · ") : ""}${specLine}</span><br/><span class="mode-tag">${t.fixture_mode} · ${instr}${isResearch ? " · research" : ""}</span>${stimLine ? `<br/><span class="hint">${stimLine}</span>` : (info ? `<br/><span class="hint">${info}</span>` : "")}${srcLine}</span>
          </label>
          ${testParamEditorHtml(t)}
        </div>`;
    }
    wrap.appendChild(grid);
    box.appendChild(wrap);
  }
  renderRunPlans();
  document.querySelectorAll("#test-list .test-item input").forEach((inp) => {
    inp.addEventListener("change", () => {
      renderRunPlans();
      applyTestDefaults(false);
      paintTileNeeds();
    });
  });
  document.querySelectorAll("#test-list .test-param-write").forEach((btn) => {
    btn.addEventListener("click", async (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      try {
        await writeTestParams(btn.getAttribute("data-test-id"));
      } catch (e) {
        alert(e.message);
      }
    });
  });
  document.querySelectorAll("#test-list .test-edit-source").forEach((btn) => {
    btn.addEventListener("click", async (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      try {
        await openPathBEditor(btn.getAttribute("data-test-id"));
      } catch (e) {
        alert(e.message);
      }
    });
  });
  applyTestDefaults(false);
  applyTestListSearch();
  paintTileNeeds();
  loadLogicDcPanel().catch(() => {});
}

let logicDcCache = null;
let logicDcButtonsBound = false;

function _logicDcJson(el, fallback) {
  const raw = String((el && el.value) || "").trim();
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

/* Customise Parameters: RS2G08 CHA then CHB -- do not skip rewire. No xyflow npm. */
function familyScaleHint(cls) {
  const c = String(cls || "").toLowerCase();
  if (c.includes("nand")) return "NAND family scale";
  if (c.includes("nor")) return "NOR family scale";
  if (c.includes("inv")) return "INV family scale";
  if (c.includes("xor")) return "XOR family scale";
  return "";
}
function isSchmittGrid(pm) {
  return !!(pm && pm.schmitt);
}
function logicDcLimitsRow(pm, tid) {
  if (pm && pm.is_open_drain) return "open-drain skip VOH";
  if (tid === "ioz" && pm && pm.has_oe) return "IOZ when OE inactive only";
  if (isSchmittGrid(pm)) return "VT+ / VT- (not plain VIH)";
  return "";
}
function wireLogicDcFlow(container) {
  const el = container || $("logic-dc-flow");
  if (!el) return;
  el.textContent = "Pin / wiring D&D canvas (#logic-dc-flow) -- vanilla DOM, no xyflow npm";
}
function collectVccGridFromUi(prev) {
  /* Customise Parameters: FIXED POINTS + RANGE SWEEPS (no xyflow). Keep prev.status. */
  prev = prev && typeof prev === "object" ? prev : {};
  const stim = ($("logic-dc-stimulus") && $("logic-dc-stimulus").value) || prev.stimulus || "PSU_MSO";
  const preview = String(($("logic-dc-vcc-list") && $("logic-dc-vcc-list").value) || "")
    .split(",")
    .map((x) => Number(String(x).trim()))
    .filter((n) => Number.isFinite(n));
  const grid = {
    stimulus: stim,
    fixed_points: Array.isArray(prev.fixed_points) ? prev.fixed_points : [],
    ranges: Array.isArray(prev.ranges) ? prev.ranges : [],
    pass_mode: prev.pass_mode || {},
    status: prev.status,
  };
  return grid;
}

function refreshVccPreview(grid) {
  const el = $("logic-dc-vcc-preview");
  if (!el) return;
  const pts = [];
  for (const fp of (grid && grid.fixed_points) || []) {
    if (fp && fp.vcc != null) pts.push(fp.vcc);
  }
  for (const band of (grid && grid.ranges) || []) {
    if (band && band.start != null) pts.push(band.start);
    if (band && band.stop != null) pts.push(band.stop);
  }
  el.textContent = "merged vcc_list: " + (pts.length ? pts.join(", ") : "--");
}

function iccStepPoints(start, stop, step) {
  const lo = Number(start);
  const hi = Number(stop);
  const st = Math.abs(Number(step) || 0.1);
  if (!Number.isFinite(lo) || !Number.isFinite(hi) || st <= 0) return [];
  const pts = [];
  const n = Math.round((hi - lo) / st);
  for (let i = 0; i <= n; i += 1) pts.push(Math.round((lo + i * st) * 1e6) / 1e6);
  if (!pts.length || Math.abs(pts[pts.length - 1] - hi) > 1e-6) pts.push(Math.round(hi * 1e6) / 1e6);
  return pts;
}

function refreshIccVccPreview(payload) {
  const el = $("logic-dc-icc-vcc-preview");
  if (!el) return;
  const mode = String(($("logic-dc-icc-vcc-mode") && $("logic-dc-icc-vcc-mode").value) || "named");
  const rec = (payload && payload.recipe) || {};
  const start = Number(rec.icc_vcc_start != null ? rec.icc_vcc_start : 2.0);
  const stop = Number(rec.icc_vcc_stop != null ? rec.icc_vcc_stop : 5.5);
  const step = Number(rec.icc_vcc_step != null ? rec.icc_vcc_step : 0.1);
  let pts = [];
  if (mode === "step") {
    pts = iccStepPoints(start, stop, step);
  } else {
    const raw = String(($("logic-dc-icc-vcc-list") && $("logic-dc-icc-vcc-list").value) || "");
    pts = raw.split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
    if (!pts.length && payload && payload.icc_vcc_plan && payload.icc_vcc_plan.volts) {
      pts = payload.icc_vcc_plan.volts;
    }
  }
  const corners = Number((payload && payload.icc_corners) || 2);
  el.textContent = "ICC will run: " + (pts.length ? pts.join(", ") : "--")
    + " (" + pts.length + " VCC x " + corners + " corners = " + (pts.length * corners) + " reads)";
}

function renderPinPortMap(rows) {
  const table = $("logic-dc-pin-map");
  if (!table) return;
  const body = table.querySelector("tbody");
  if (!body) return;
  const list = Array.isArray(rows) ? rows : [];
  body.innerHTML = list.length
    ? list.map((r) => `<tr><td>${escText(r.pin || "")}${r.number != null ? " pkg " + escText(r.number) : ""}</td><td>${escText(r.instrument || "")}</td><td>${escText(r.channel || "")}</td><td>${escText(r.role || "")}${r.note ? " -- " + escText(r.note) : ""}</td></tr>`).join("")
    : "<tr><td colspan='4'>--</td></tr>";
}

function renderLogicDc(payload) {
  logicDcCache = payload || null;
  const panel = $("panel-logic-dc");
  if (!panel) return;
  const present = !!(payload && payload.present);
  panel.classList.toggle("hidden", !present);
  if (!present) return;
  const ui = payload;
  const tt = ui.truth_table || {};
  if ($("logic-dc-truth")) $("logic-dc-truth").value = JSON.stringify(tt, null, 2);
  if ($("logic-dc-isolation")) $("logic-dc-isolation").value = JSON.stringify(ui.isolation || {}, null, 2);
  if ($("logic-dc-pass-mode")) $("logic-dc-pass-mode").value = JSON.stringify(ui.pass_mode || {}, null, 2);
  if ($("logic-dc-vcc-list")) $("logic-dc-vcc-list").value = (ui.vcc_list || []).join(", ");
  if ($("logic-dc-gaps")) $("logic-dc-gaps").value = JSON.stringify(ui.gaps || [], null, 2);
  if ($("logic-dc-stable-eps-a")) {
    const a = (ui.recipe || {}).stable_eps_A;
    $("logic-dc-stable-eps-a").value = a == null ? "" : String(a);
  }
  if ($("logic-dc-stimulus")) $("logic-dc-stimulus").value = ui.stimulus || "PSU_MSO";
  if ($("logic-dc-dual-ch")) $("logic-dc-dual-ch").checked = !!ui.dual_channel_continue;
  const partEn = ui.enabled_tests || [];
  const catEn = ui.catalog_tests || ((allTests || []).map((t) => t.id));
  let enLine = "Enabled tests (SKU): " + (partEn.join(", ") || "--");
  if (catEn.length) enLine += " | this Version: " + catEn.join(", ");
  if (partEn.includes("ioz") && !catEn.includes("ioz")) {
    enLine += " -- catalog hid ioz; Tests page tick IOZ then Save this Version";
  }
  if ($("logic-dc-enabled")) $("logic-dc-enabled").textContent = enLine;
  const n = ui.icc_corners;
  const pins = ui.icc_pins || [];
  if ($("logic-dc-icc-corners")) {
    const nIn = pins.length;
    const corners = nIn ? 1 << nIn : 0;
    $("logic-dc-icc-corners").textContent =
      "ICC corners: " + (n != null ? n : "--") + " pins " + pins.join(",") +
      (nIn ? " (1 << nIn = " + corners + ")" : "");
  }
  if ($("logic-dc-dual-ch") && ui.dual_channel_continue) {
    const hint = $("logic-dc-hint");
    if (hint) {
      hint.textContent =
        "RS2G08 dual-channel Continue: CHA then CHB. Do not skip rewire.";
    }
  }
  const fam = familyScaleHint(ui.product_class || ui.runner || "");
  if (fam && $("logic-dc-hint")) {
    $("logic-dc-hint").textContent = ($("logic-dc-hint").textContent || "") + " " + fam;
  }
  if (ui.campaign_mismatch && $("logic-dc-hint")) {
    $("logic-dc-hint").textContent = ui.campaign_mismatch;
  }
  wireLogicDcFlow($("logic-dc-flow"));
  const rows = ui.icc_corner_rows || [];
  if ($("logic-dc-icc-table")) {
    $("logic-dc-icc-table").textContent = rows.length
      ? rows.map((r) => JSON.stringify(r)).join(" | ")
      : "fail-open if limits missing";
  }
  if ($("logic-dc-pin-wiring")) {
    const labs = ui.pin_wiring_labels || [];
    $("logic-dc-pin-wiring").textContent = "Pin / wiring: " + (labs.join("; ") || "--");
  }
  renderPinPortMap(ui.pin_port_map || []);
  const iccPlan = ui.icc_vcc_plan || {};
  if ($("logic-dc-icc-vcc-mode")) $("logic-dc-icc-vcc-mode").value = iccPlan.mode || (ui.recipe || {}).icc_vcc_mode || "named";
  if ($("logic-dc-icc-vcc-list")) {
    const lst = iccPlan.list || (ui.recipe || {}).icc_vcc_list || [];
    $("logic-dc-icc-vcc-list").value = Array.isArray(lst) ? lst.join(", ") : String(lst || "");
  }
  const testBox = $("logic-dc-test-vcc");
  if (testBox) {
    const plans = ui.vcc_plans || [];
    testBox.innerHTML = plans.filter((pl) => pl && pl.id && pl.id !== "icc").map((pl) => {
      const mode = pl.mode || "grid";
      const locked = pl.id === "delta_icc";
      const volts = (pl.volts || pl.list || []).join(", ");
      return `<label>${escText(pl.id)} VCC
        <select data-vcc-plan-id="${escText(pl.id)}" data-vcc-plan-field="mode"${locked ? " disabled" : ""}>
          <option value="grid"${mode === "grid" ? " selected" : ""}>grid / default</option>
          <option value="named"${mode === "named" ? " selected" : ""}>named</option>
          <option value="step"${mode === "step" ? " selected" : ""}>0.1 step</option>
          <option value="list"${mode === "list" ? " selected" : ""}>custom</option>
        </select>
        <input data-vcc-plan-id="${escText(pl.id)}" data-vcc-plan-field="list" value="${escText(volts)}"${locked ? " disabled" : ""} />
      </label>` + (locked ? `<p class="hint">ICCT locked: VCC 5.5, one input 3.4 V, max 500 uA</p>` : "");
    }).join("");
  }
  refreshIccVccPreview(ui);
  const box = $("logic-dc-card-fields");
  if (box) {
    const fields = ui.card_fields || [];
    box.innerHTML = fields.map((f) => {
      const key = f.key || "";
      const val = f.value == null ? "" : (typeof f.value === "object" ? JSON.stringify(f.value) : String(f.value));
      return `<label>${key}<input data-card-field="${key}" value="${escText(val)}" /></label>`;
    }).join("");
  }
  const grid = ui.vcc_grid || ui.vcc_plan || {};
  const fp = $("logic-dc-fixed-points");
  if (fp) {
    fp.innerHTML = ((grid.fixed_points) || []).map((p) => `<span class="chip">FIXED ${p.vcc}</span>`).join(" ") || "<span class='hint'>none</span>";
  }
  const rs = $("logic-dc-range-sweeps");
  if (rs) {
    rs.innerHTML = ((grid.ranges) || []).map((b) => `<span class="chip">RANGE ${b.start}-${b.stop} step ${b.step}</span>`).join(" ") || "<span class='hint'>none</span>";
  }
  refreshVccPreview(grid);
  const psuMso = String(ui.stimulus || grid.stimulus || "").toUpperCase() === "PSU_MSO";
  const freqLab = $("freq-label");
  if (freqLab) freqLab.classList.toggle("hidden", psuMso);
}

async function loadLogicDcPanel() {
  const panel = $("panel-logic-dc");
  if (!panel) return;
  if (!logicDcButtonsBound) {
    logicDcButtonsBound = true;
    if ($("btn-save-logic-dc")) $("btn-save-logic-dc").onclick = () => saveLogicDcPanel();
    if ($("btn-save-test-params")) $("btn-save-test-params").onclick = () => saveLogicDcOverlay();
    if ($("logic-dc-icc-vcc-mode")) $("logic-dc-icc-vcc-mode").onchange = () => refreshIccVccPreview(logicDcCache);
    if ($("logic-dc-icc-vcc-list")) $("logic-dc-icc-vcc-list").oninput = () => refreshIccVccPreview(logicDcCache);
  }
  const sel = currentDbSelection();
  const part = sel.part || "";
  if (!part || String(activeFamily || "").toLowerCase() !== "logic") {
    renderLogicDc({ present: false });
    return;
  }
  try {
    const payload = await rpc("get_product_model", { part, part_key: part });
    try {
      const camp = await rpc("list_campaign_tests");
      if (camp && camp.ok) {
        payload.enabled_tests = camp.part_yaml || payload.enabled_tests || [];
        payload.catalog_tests = camp.current || [];
        payload.current_from = camp.current_from || "";
      }
    } catch (_) {}
    try {
      const st = await rpc("session_status");
      const ctxPart = String((st && st.db && (st.db.part_key || st.db.part)) || "")
        .toLowerCase()
        .replace(/[^a-z0-9]/g, "");
      const selPart = String(part || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      if (ctxPart && selPart && ctxPart !== selPart) {
        payload.campaign_mismatch =
          "Worker campaign is " + (st.db.part || ctxPart) +
          " -- Apply campaign for " + part +
          " or the Run list stays the other SKU (IOZ missing is often that mix)";
      }
    } catch (_) {}
    renderLogicDc(payload);
  } catch (e) {
    renderLogicDc({ present: false });
    if ($("logic-dc-hint")) $("logic-dc-hint").textContent = String(e.message || e);
  }
}

async function saveLogicDcPanel() {
  const sel = currentDbSelection();
  const part = sel.part || "";
  const prev = logicDcCache || {};
  const deleted_fields = [];
  document.querySelectorAll("[data-card-field]").forEach((el) => {
    if (el && el.value === "" && el.getAttribute("data-card-field")) {
      /* keep empty as edit, not auto-delete */
    }
  });
  const patch = {
    truth_table: _logicDcJson($("logic-dc-truth"), prev.truth_table),
    isolation: _logicDcJson($("logic-dc-isolation"), prev.isolation),
    pass_mode: _logicDcJson($("logic-dc-pass-mode"), prev.pass_mode),
    gaps: _logicDcJson($("logic-dc-gaps"), prev.gaps),
    vcc_list: String(($("logic-dc-vcc-list") && $("logic-dc-vcc-list").value) || ""),
    "recipe.stable_eps_A": (($("logic-dc-stable-eps-a") && $("logic-dc-stable-eps-a").value) || "").trim() || null,
    "recipe.dual_channel_continue": !!( $("logic-dc-dual-ch") && $("logic-dc-dual-ch").checked ),
    "recipe.icc_vcc_mode": (($("logic-dc-icc-vcc-mode") && $("logic-dc-icc-vcc-mode").value) || "named"),
    "recipe.icc_vcc_step": 0.1,
    vcc_grid: collectVccGridFromUi(prev.vcc_grid || prev.vcc_plan || {}),
    vcc_plan: collectVccGridFromUi(prev.vcc_grid || prev.vcc_plan || {}),
    deleted_fields,
  };
  const iccListSave = String(($("logic-dc-icc-vcc-list") && $("logic-dc-icc-vcc-list").value) || "")
    .split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
  if (iccListSave.length) patch["recipe.icc_vcc_list"] = iccListSave;
  const saved = await rpc("save_product_model", { part, part_key: part, patch });
  renderLogicDc(saved);
  log("Saved Logic DC product_model (cannot promote Datasheet-signed)\n");
}

async function saveLogicDcOverlay() {
  const sel = currentDbSelection();
  const operator = requireWriteOperator();
  const prev = logicDcCache || {};
  const grid = collectVccGridFromUi(prev.vcc_grid || prev.vcc_plan || {});
  const eps = (($("logic-dc-stable-eps-a") && $("logic-dc-stable-eps-a").value) || "").trim();
  const iccMode = (($("logic-dc-icc-vcc-mode") && $("logic-dc-icc-vcc-mode").value) || "named");
  const iccList = String(($("logic-dc-icc-vcc-list") && $("logic-dc-icc-vcc-list").value) || "")
    .split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
  const campaign = {
    component: sel.component,
    part: sel.part,
    package: sel.package,
    operator,
    version: sel.version,
  };
  await rpc("save_test_params", {
    test_id: "_logic_dc",
    params: {
      vcc_grid: grid,
      vcc_plan: grid,
      sample_size: prev.sample_size,
      stable_eps_A: eps === "" ? null : Number(eps),
    },
    ...campaign,
  });
  const iccParams = {
    icc_vcc_mode: iccMode,
    vcc_mode: iccMode,
    icc_vcc_step: 0.1,
    icc_vcc_start: 2.0,
    icc_vcc_stop: 5.5,
  };
  if (iccList.length) iccParams.icc_vcc_list = iccList;
  if (iccMode === "list" && iccList.length) iccParams.vcc_list = iccList;
  await rpc("save_test_params", {
    test_id: "icc",
    params: iccParams,
    ...campaign,
  });
  const seen = new Set();
  for (const selEl of document.querySelectorAll("[data-vcc-plan-id][data-vcc-plan-field='mode']")) {
    const tid = selEl.getAttribute("data-vcc-plan-id");
    if (!tid || seen.has(tid)) continue;
    seen.add(tid);
    const mode = String(selEl.value || "").trim();
    const listEl = document.querySelector(`[data-vcc-plan-id="${tid}"][data-vcc-plan-field="list"]`);
    const list = String((listEl && listEl.value) || "").split(/[,;]+/).map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
    if (!mode || mode === "grid") continue;
    const block = { vcc_mode: mode };
    if (mode === "list" && list.length) block.vcc_list = list;
    if (mode === "step") {
      block.vcc_start = 2.0;
      block.vcc_stop = 5.5;
      block.vcc_step = 0.1;
    }
    await rpc("save_test_params", { test_id: tid, params: block, ...campaign });
  }
  log("Saved Version overlay (_manifest/test_params.yaml) including ICC VCC plan\n");
}

function sessionOpenLine(st) {
  const have = Object.keys(st.mapping || {});
  const pnp = Object.keys(st.pnp || {});
  const want = ["PSU", "AWG", "DMM", "MSO"];
  const miss = want.filter((k) => !have.includes(k));
  let line = `Session open (${st.visa_backend || "visa"}): ${have.join(", ") || "--"}`;
  if (miss.length) {
    const onPnp = miss.filter((k) => pnp.includes(k));
    const gone = miss.filter((k) => !pnp.includes(k));
    if (onPnp.length) {
      line += ` -- USB present, not in session: ${onPnp.join(", ")} (Discover then Open Session)`;
    }
    if (gone.length) {
      line += ` -- not on bus: ${gone.join(", ")}`;
      if (gone.includes("AWG")) {
        line += " (Windows USBTMC Unknown -- close Ultra Sigma, unplug/replug DG822, Discover)";
      }
    }
  }
  return line;
}

async function refreshSession() {
  try {
    const st = await rpc("session_status");
    sessionOpen = !!st.open;
    setTiles(tileMapFromStatus(st));
    $("btn-start").disabled = !sessionOpen;
    const pnpKeys = Object.keys(st.pnp || {});
    $("session-hint").textContent = sessionOpen
      ? (st.sim
        ? `SIM session (no USB): ${Object.keys(st.mapping || {}).join(", ")}` +
          (st.sim_bus
            ? ` · last AWG ${st.sim_bus.func || "?"} ${st.sim_bus.out || "OFF"} · PSU ${st.sim_bus.psu_on ? (st.sim_bus.psu_v + " V") : "OFF"}`
            : "")
        : sessionOpenLine(st))
      : (pnpKeys.length
        ? `USB on bus: ${pnpKeys.join(", ")}. Discover then Open Session.`
        : "Init = Discover then Open Session (USB), or Open SIM / DEMO. + Session is JSON only.");
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
    const sameRail = family === railType;
    railType = family;
    if (!(inventoryRows || []).length) {
      await loadInventory();
    } else {
      paintInventory(family);
    }
    if ($("np-category")) {
      const catId = typeForFamily(family);
      if (catId) $("np-category").value = catId;
    }
    try {
      mergeInventoryIntoTree();
      const component = componentFromFamily(family);
      const fromInv = campaignFromInventory(family);
      const last = readSavedByFamily(family);
      const lastMineOk = !partScopeIsMine()
        || minePartCodes(writeOperatorLabel()).includes(String((last && last.part) || "").toUpperCase());
      const lastFamOk = !!(last && familyFromComponent(last.component) === family && last.component === component);
      const lastOk = !!(lastFamOk && lastMineOk && liveKeys(
        (((dbTree.components || {})[last.component] || {}).parts) || {}
      ).includes(last.part));
      const sel = lastOk
        ? last
        : (fromInv || firstCampaignInComponent(component));
      const wantComp = (sel && sel.component) || component;
      const shownFam = familyFromComponent(($("db-component") && $("db-component").value) || "");
      if (sameRail && shownFam === family && $("db-component") && $("db-component").value === wantComp && sel && $("db-part") && $("db-part").value === sel.part) {
        paintBrand(railType);
        return;
      }
      if (sel) {
        if ($("np-part")) $("np-part").value = sel.part || "";
        if ($("np-package")) $("np-package").value = sel.package || "";
        if ($("np-model")) $("np-model").value = sel.model || sel.part || "";
        paintCampaign(sel);
        await applyDb();
      } else {
        const firstInv = (inventoryRows || []).find((r) => String(r.category || "") === typeForFamily(family));
        const suite = suiteForRow(firstInv) || family;
        await switchFamily(suite);
      }
      paintBrand(railType);
      await refreshTagsUI();
    } catch (e) {
      alert(e.message);
    }
  });
}

["db-component", "db-part", "db-package", "db-operator", "db-version"].forEach((id) => {
  const el = $(id);
  if (!el) return;
  el.addEventListener("change", async () => {
    if (!String(($("db-component") && $("db-component").value) || "").trim()) return;
    if (!String(($("db-part") && $("db-part").value) || "").trim()) return;
    refreshDbCascades(currentDbSelection(), id);
    if ((id === "db-component" || id === "db-part") && $("db-model")) {
      $("db-model").value = "";
    }
    // Component change also switches family suite in the same click
    if (id === "db-component") {
      const fam = familyFromComponent(($("db-component") && $("db-component").value) || "");
      if (fam) {
        railType = fam;
        paintInventory(fam);
        paintBrand(fam);
      }
      if (fam && fam !== activeFamily) {
        try {
          await switchFamily(fam);
        } catch (e) {
          log(`Family switch: ${e.message}\n`);
        }
      }
    }
    const sel = currentDbSelection();
    if (sel.operator) syncOwnerSelectFromFolder(sel.operator);
    if ($("db-breadcrumb") && sel.component) {
      $("db-breadcrumb").textContent =
        `${sel.component} / ${sel.part} / ${sel.package} / ${sel.operator || "?"} / ${sel.version}` +
        (sel.model ? ` · ${sel.model}` : "");
    }
    if (!campaignKnown(sel)) {
      log("Typed new campaign path -- click Apply campaign to create folders\n");
      return;
    }
    log("Campaign path updated -- click Apply campaign to load tests / folders\n");
  });
});

$("btn-apply-db").onclick = async () => {
  try {
    await applyDb();
  } catch (e) {
    alert(e.message);
  }
};

if ($("btn-add-operator")) {
  $("btn-add-operator").onclick = () => {
    const name = String(($("db-operator") && $("db-operator").value) || "").trim();
    openAddOperatorModal(name, currentDbSelection());
  };
}
if ($("btn-plus-operator")) {
  $("btn-plus-operator").onclick = (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    closeComboMenu();
    openCampaignPlus("operator", "");
  };
}
if ($("btn-plus-package")) {
  $("btn-plus-package").onclick = (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    closeComboMenu();
    openCampaignPlus("package", "");
  };
}
if ($("campaign-plus-go")) {
  $("campaign-plus-go").onclick = async () => {
    try {
      await confirmCampaignPlus();
    } catch (e) {
      notice(e.message);
    }
  };
}
if ($("campaign-plus-cancel")) {
  $("campaign-plus-cancel").onclick = () => closeCampaignPlus();
}
if ($("campaign-plus-modal")) {
  $("campaign-plus-modal").addEventListener("click", (e) => {
    if (e.target === $("campaign-plus-modal")) closeCampaignPlus();
  });
}
if ($("add-operator-go")) {
  $("add-operator-go").onclick = async () => {
    try {
      await confirmAddOperator();
    } catch (e) {
      notice(e.message);
    }
  };
}
if ($("add-operator-cancel")) {
  $("add-operator-cancel").onclick = () => closeAddOperatorModal();
}
if ($("add-operator-all-skus")) {
  $("add-operator-all-skus").addEventListener("change", syncAddOperatorAllSkus);
}
if ($("btn-provision-person")) {
  $("btn-provision-person").onclick = async () => {
    try {
      await provisionPersonFromSetup();
    } catch (e) {
      notice(e.message);
    }
  };
}
if ($("add-operator-modal")) {
  $("add-operator-modal").addEventListener("click", (e) => {
    if (e.target === $("add-operator-modal")) closeAddOperatorModal();
  });
}

async function savePersonFromSetup() {
  const label = requireWriteOperator();
  const sel = currentDbSelection();
  const codes = (personSkuCodes && personSkuCodes.length)
    ? personSkuCodes.slice()
    : (sel.part ? [sel.part] : []);
  const res = await rpc("assign_owner_products", {
    label,
    parts: codes,
    replace_parts: true,
    sample_size: 4,
  });
  ownersList = res.owners || ownersList;
  if (res.owner && res.owner.id) saveOwner(res.owner.id);
  await loadOwners();
  syncOwnerSelectFromFolder(label);
  syncPersonSkusFromOwner(label);
  const row = (res.owner || {});
  const matched = (res.matched || []).map((m) => m.part || m.part_key).filter(Boolean);
  const unmatched = res.unmatched || [];
  const roots = res.roots || [];
  let hint =
    `${res.action || "saved"} ${row.label || label}` +
    (matched.length ? ` · parts ${matched.join(", ")}` : "") +
    (roots.length ? ` · folders ${roots.length}` : "");
  if (unmatched.length) hint += ` · unmatched ${unmatched.join(", ")} (not created)`;
  if ($("person-hint")) $("person-hint").textContent = hint;
  log(`Person assign: ${hint}\n`);
}

if ($("btn-save-person")) {
  $("btn-save-person").onclick = async () => {
    try {
      await savePersonFromSetup();
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-forget-person")) {
  $("btn-forget-person").onclick = async () => {
    try {
      const label = (($("db-operator") && $("db-operator").value) || writeOperatorLabel() || "").trim();
      if (!label || ownerIsObserver(label) || label.toLowerCase() === "all") {
        throw new Error("Pick a person on Setup (not All / Kevin) to remove");
      }
      const phrase = String(($("forget-phrase") && $("forget-phrase").value) || "");
      const wipe = !!( $("forget-wipe-folders") && $("forget-wipe-folders").checked );
      const want = `FORGET ${label}`;
      if (phrase !== want) {
        throw new Error(`Type ${want} in Phrase`);
      }
      if (wipe) {
        const typed = String(($("forget-folder-name") && $("forget-folder-name").value) || "").trim();
        if (typed !== label) {
          throw new Error(`Wipe needs the folder name typed exactly: ${label}`);
        }
        if (!confirm(`Delete all ${label} folders? Cannot undo.`)) return;
      }
      const res = await rpc("remove_owner", {
        owner: label,
        confirm_text: phrase,
        delete_folders: wipe,
      });
      ownersList = res.owners || [];
      personSkuCodes = [];
      paintPersonSkuChips();
      await loadOwners();
      const fallback = ownersList.find((o) => o.id === "eugene") || ownersList.find((o) => o.id !== "all");
      if ($("owner-select") && fallback) {
        $("owner-select").value = fallback.id;
        saveOwner(fallback.id);
      }
      if ($("db-operator") && fallback) {
        $("db-operator").value = fallback.label || fallback.id;
      }
      const n = Number(res.folder_count || (res.folders_deleted || []).length || 0);
      const leftover = res.folder_errors || [];
      let msg = wipe
        ? `Removed ${label} · folders deleted ${n}`
        : `Forgot ${label} in yaml. Folders stay.`;
      if (leftover.length) msg += ` · leftover ${leftover.length} (OneDrive lock)`;
      if ($("person-hint")) $("person-hint").textContent = msg;
      if ($("forget-hint")) $("forget-hint").textContent = msg;
      if ($("forget-phrase")) $("forget-phrase").value = "";
      if ($("forget-folder-name")) $("forget-folder-name").value = "";
      if ($("forget-wipe-folders")) $("forget-wipe-folders").checked = false;
      paintSettingsPcHint();
      notice(msg);
      log(`${msg}\n`);
    } catch (e) {
      alert(e.message);
    }
  };
}

function paintSettingsPcHint() {
  const el = $("settings-pc-hint");
  if (!el) return;
  const id = readSavedOwner() || "(none)";
  const label = writeOperatorLabel() || id;
  el.textContent = `This PC: ${label} (id ${id}). Shared DB stays OneDrive.`;
}

if ($("btn-reset-pc-person")) {
  $("btn-reset-pc-person").onclick = () => {
    try { localStorage.removeItem(OWNER_KEY); } catch (_) {}
    if ($("owner-select")) $("owner-select").value = "all";
    paintSettingsPcHint();
    if ($("first-run-modal")) $("first-run-modal").classList.remove("hidden");
    notice("This PC name cleared. Type your name on first-run.");
  };
}

function inventoryPartChoices() {
  const seen = new Set();
  const out = [];
  for (const row of inventoryRows || []) {
    const p = String(row.part || "").trim().toUpperCase();
    if (!p || seen.has(p)) continue;
    seen.add(p);
    out.push(p);
  }
  out.sort();
  return out;
}

function refreshPersonSkuCombo() {
  fillCombo($("person-sku-input"), inventoryPartChoices(), "");
  if ($("person-sku-input")) $("person-sku-input").value = "";
  syncComboChrome($("person-sku-input"));
}

function paintPersonSkuChips() {
  const el = $("person-sku-chips");
  if (!el) return;
  el.innerHTML = "";
  const list = personSkuCodes || [];
  for (const code of list) {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = code;
    const x = document.createElement("button");
    x.type = "button";
    x.className = "tag-chip-x";
    x.innerHTML = '<span aria-hidden="true">x</span>';
    x.setAttribute("aria-label", `Unassign ${code}`);
    x.title = "Unassign (yaml only)";
    x.onclick = () => unassignPersonSku(code).catch((e) => alert(e.message));
    chip.appendChild(x);
    el.appendChild(chip);
  }
  if (!list.length) {
    const empty = document.createElement("span");
    empty.className = "hint";
    empty.textContent = "none yet -- pick codes then Save person";
    el.appendChild(empty);
  }
}

function addPersonSku(raw) {
  const code = String(raw || "").trim().toUpperCase();
  if (!code) return;
  const key = code.toLowerCase().replace(/[^a-z0-9]+/g, "");
  if ((personSkuCodes || []).some((c) => c.toLowerCase().replace(/[^a-z0-9]+/g, "") === key)) {
    paintPersonSkuChips();
    return;
  }
  personSkuCodes = (personSkuCodes || []).concat([code]);
  paintPersonSkuChips();
}

function syncPersonSkusFromOwner(label) {
  const name = String(label || "").trim().toLowerCase();
  const row = (ownersList || []).find((o) => {
    const id = String(o.id || "").toLowerCase();
    const lab = String(o.label || "").toLowerCase();
    return id === name || lab === name;
  });
  const parts = (row && row.parts) || [];
  personSkuCodes = parts.map((p) => String(p || "").trim().toUpperCase()).filter(Boolean);
  paintPersonSkuChips();
}

async function unassignPersonSku(code) {
  const label = requireWriteOperator();
  const res = await rpc("assign_owner_products", {
    label,
    parts: [],
    unassign: [code],
    replace_parts: false,
  });
  ownersList = res.owners || ownersList;
  syncPersonSkusFromOwner(label);
  if ($("person-hint")) {
    $("person-hint").textContent =
      `Unassigned ${code} from ${label} (yaml only). Folders stay.`;
  }
  log(`Unassigned ${code} from ${label} (folders stay)\n`);
}

if ($("person-sku-input")) {
  $("person-sku-input").addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    const v = String($("person-sku-input").value || "").trim();
    if (!v) return;
    if (ev.key === " " && !v.includes(" ")) return;
    ev.preventDefault();
    addPersonSku(v);
    $("person-sku-input").value = "";
    syncComboChrome($("person-sku-input"));
    closeComboMenu();
  });
}

async function saveCampaignLabels() {
  const payload = (campaignLabels && campaignLabels.length)
    ? { labels: campaignLabels, remember_scope: labelRememberScope() }
    : { tags: campaignTags, boards: campaignBoards, remember_scope: labelRememberScope() };
  const res = await rpc("save_tags", payload);
  campaignTags = res.tags || campaignTags;
  campaignBoards = res.boards || campaignBoards;
  campaignLabels = Array.isArray(res.labels) ? res.labels : campaignLabels;
  paintTagsEditor();
  if (res.excel_status === "ok") {
    log(`Tags in Excel ${res.excel_cell || res.excel}\n`);
  } else if (res.excel_status === "locked") {
    log("Excel locked - close the lab workbook to stamp tags\n");
  }
  return res;
}

function addSetupLabel(kind, value) {
  const k = String(kind || "tag").trim();
  const v = String(value || "").trim();
  if (!k || !v || v.startsWith("(")) return;
  if (k === "board") {
    setCampaignBoard(v);
    return;
  }
  const lab = { kind: k, value: v };
  const tok = labelToken(lab);
  if ((campaignLabels || []).some((x) => labelToken(x) === tok)) return;
  campaignLabels = (campaignLabels || []).concat([lab]);
  if (!campaignTags.includes(tok)) campaignTags.push(tok);
  paintTagsEditor();
  saveCampaignLabels().catch((e) => alert(e.message));
}

if ($("campaign-board")) {
  $("campaign-board").addEventListener("change", () => {
    const v = String($("campaign-board").value || "").trim();
    if (!v) {
      clearCampaignBoard();
      return;
    }
    setCampaignBoard(v);
  });
  $("campaign-board").addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    ev.preventDefault();
    const v = String($("campaign-board").value || "").trim();
    if (v) setCampaignBoard(v);
  });
}

if ($("setup-label-kind")) {
  $("setup-label-kind").onchange = () => {
    fillLabelValueSelect();
    updateLabelKindHint();
  };
}
if ($("btn-setup-add-label")) {
  $("btn-setup-add-label").onclick = () => {
    let kind = (($("setup-label-kind") && $("setup-label-kind").value) || "board").trim();
    let value = (($("setup-label-value") && $("setup-label-value").value) || "").trim();
    if (value.includes(":")) {
      const i = value.indexOf(":");
      kind = value.slice(0, i).trim() || kind;
      value = value.slice(i + 1).trim();
    }
    addSetupLabel(kind, value);
    if ($("setup-label-value")) $("setup-label-value").value = "";
  };
}
if ($("btn-tag-add-board")) {
  $("btn-tag-add-board").onclick = () => {
    const b = ($("tag-board-select") && $("tag-board-select").value) || "";
    if (!b || b.startsWith("(")) return;
    addSetupLabel("board", b);
  };
}
if ($("btn-tag-add-free")) {
  $("btn-tag-add-free").onclick = () => {
    const t = (($("tag-free") && $("tag-free").value) || "").trim();
    if (!t) return;
    addCampaignTagFromText(t);
    if ($("tag-free")) $("tag-free").value = "";
  };
}
if ($("tag-free")) {
  $("tag-free").addEventListener("keydown", (ev) => {
    if ((ev.key === " " || ev.key === "," || ev.key === "Enter") && String($("tag-free").value || "").trim()) {
      ev.preventDefault();
      addCampaignTagFromText($("tag-free").value);
      $("tag-free").value = "";
    }
  });
}
if ($("btn-tags-save")) {
  $("btn-tags-save").onclick = async () => {
    try {
      const res = await rpc("save_tags", {
        tags: campaignTags,
        boards: campaignBoards,
        labels: campaignLabels,
        remember_scope: labelRememberScope(),
      });
      campaignTags = res.tags || campaignTags;
      campaignBoards = res.boards || campaignBoards;
      campaignLabels = Array.isArray(res.labels) ? res.labels : campaignLabels;
      paintTagsEditor();
      if ($("tags-path-hint")) {
        $("tags-path-hint").textContent =
          res.excel_status === "ok"
            ? `Saved TAGS.txt: ${res.tags_txt} · Excel ${res.excel_cell}`
            : `Saved TAGS.txt: ${res.tags_txt}`;
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
if ($("btn-tags-clear")) {
  $("btn-tags-clear").onclick = async () => {
    if (!confirm("Clear free tags on this campaign? Board stays. TAGS.txt updates.")) return;
    try {
      const board = campaignBoardValue();
      campaignTags = board ? [`board:${board}`] : [];
      campaignBoards = board ? [board] : [];
      campaignLabels = board ? [{ kind: "board", value: board }] : [];
      await saveCampaignLabels();
      log(board ? `Tags cleared (board ${board} kept)\n` : "Tags cleared\n");
    } catch (e) {
      alert(e.message);
    }
  };
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
      campaignLabels = Array.isArray(res.labels) ? res.labels : campaignLabels;
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

async function refreshCloudDbHint() {
  try {
    const st = await rpc("cloud_db_status");
    if ($("central-db-hint") && st.root) {
      const ok = st.exists ? "ready" : "not on this PC yet";
      $("central-db-hint").textContent =
        `Central DB (${st.cloud_kind || "local"}, ${ok}): ${st.root}`;
    }
    if (st.pick_needed) {
      notice(
        "Central #Test_Database is not on this PC. Click Choose folder and pick the OneDrive shortcut (or any folder to save). The console stays open."
      );
    }
    return st;
  } catch (_) {
    return null;
  }
}

async function pickCloudDbFolder() {
  try {
    const res = await rpc("pick_cloud_db");
    if (res.cancelled) return;
    await refreshCloudDbHint();
    await loadDb();
    mergeInventoryIntoTree();
    refreshDbCascades(currentDbSelection());
    hideNotice();
    log("Cloud DB folder: " + (res.folder || res.root || "?") + "\n");
  } catch (e) {
    notice(e.message || String(e));
  }
}

if ($("btn-open-central")) {
  $("btn-open-central").onclick = async () => {
    try {
      const res = await rpc("open_central_db");
      if (res && res.missing) {
        notice(res.note || "Central folder missing. Click Choose folder.");
      }
    } catch (e) {
      notice(e.message);
    }
  };
}

if ($("btn-pick-cloud-db")) {
  $("btn-pick-cloud-db").onclick = () => pickCloudDbFolder();
}

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
    const n = Object.keys(m || {}).length;
    if (!n) {
      log("Discover {}: no USB *IDN (PnP Unknown / timeout skipped). Close Ultra Sigma, USB+power, Discover again.\n");
      const st = await rpc("session_status");
      if (st && st.sim) {
        setTiles({});
        notice(
          "No USB *IDN. SIM session is still open (fake tiles were not USB). " +
            "Plug the live MSO/PSU/AWG/DMM, close Ultra Sigma, Discover, then Open Session (not DEMO)."
        );
      } else {
        setTiles((st && st.pnp) || {});
        notice(
          "No USB instruments. PnP-OK tiles stay lit when Windows Status=OK. Close Ultra Sigma, Discover again. " +
            "No USB: DEMO (SIM)."
        );
      }
      return;
    }
    setTiles(m);
    const miss = ["MSO", "PSU", "AWG", "DMM"].filter((k) => !m[k]);
    log(`Discovered ${JSON.stringify(m)}\n`);
    if (miss.length) {
      log("Not detected (no *IDN / PnP Unknown): " + miss.join(", ") + "\n");
    }
    await loadMappedCoverage();
  } catch (e) {
    notice(e.message);
  }
};

$("btn-open").onclick = async () => {
  try {
    const m = await rpc("open_session");
    setTiles(m);
    sessionOpen = true;
    $("btn-start").disabled = false;
    log(`Session open ${JSON.stringify(m)}\n`);
    const miss = ["MSO", "PSU", "AWG", "DMM"].filter((k) => !m[k]);
    if (!Object.keys(m || {}).length) {
      notice(
        "Session open with no USB *IDN. Discover again or Open SIM."
      );
    } else if (miss.length) {
      log(
        "not on bus (START fails only if a test needs them): " +
          miss.join(", ") +
          "\n"
      );
    }
    await refreshSession();
    await loadMappedCoverage();
    if (!m.DMM) {
      log("DMM not in session -- OpAmp VOL and Logic IDD/VOUT/cap_load will fail until Discover finds it\n");
    }
  } catch (e) {
    await refreshSession();
    notice(e.message);
  }
};

if ($("btn-open-sim")) {
  $("btn-open-sim").onclick = async () => {
    try {
      requireWriteOperator();
      const m = await rpc("open_session", { sim: true });
      setTiles(m);
      sessionOpen = true;
      $("btn-start").disabled = false;
      log(`SIM session ${JSON.stringify(m)}\n`);
      await refreshSession();
    } catch (e) {
      notice(e.message);
    }
  };
}

function shotFolderKey() {
  const ids = selectedTests();
  if (ids.includes("slew")) return "SlewRate";
  if (ids.includes("settling")) return "SettlingTime";
  if (ids.includes("gbw")) return "GBW";
  if (ids.includes("ort")) return "ORT";
  const first = ids[0];
  if (!first) return "ORT";
  const row = (allTests || []).find((t) => t.id === first);
  return (row && row.lab_sheet) || first;
}

function paintDemoTimeline(res) {
  const steps = res.steps || [];
  const n = steps.length;
  const now = new Date().toISOString();
  const entries = steps.map((s, i) => ({
    id: `demo-${i}`,
    kind: "test",
    label: `${s.fixture_mode ? s.fixture_mode + " · " : ""}${s.label || s.test_id}`,
    status: "done",
    test_id: s.test_id,
    finished_at: now,
    message: `DEMO mock ${(s.instruments || []).join("+") || "none"}`,
  }));
  renderTimeline({
    entries,
    done_count: n,
    total_count: n,
    progress_pct: n ? 100 : 0,
    finished_at: now,
    session_id: String(res.session || "").split(/[\\/]/).pop() || "demo",
  });
}

$("btn-shot").onclick = async () => {
  try {
    const r = await rpc("screenshot", { test_key: shotFolderKey() });
    log(`Screenshot: ${r.path}\n`);
    alert(`JPEG saved:\n${r.path}`);
  } catch (e) {
    alert(e.message);
  }
};

$("btn-folder").onclick = async () => {
  try {
    const duts = selectedDuts();
    await rpc("open_screenshots", {
      test_key: shotFolderKey(),
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
      ingestDbTree(await rpc("list_db_tree"));
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

if ($("detect-author")) {
  $("detect-author").addEventListener("change", () => refreshDetectedPanel());
}
if ($("detect-allow-others")) {
  $("detect-allow-others").addEventListener("change", () => {
    syncDetectAuthorLock();
    refreshDetectedPanel();
  });
}

function othersGoldensAllowed() {
  return !!($("detect-allow-others") && $("detect-allow-others").checked);
}

function detectAuthorParam() {
  if (!othersGoldensAllowed()) return "";
  return String(($("detect-author") && $("detect-author").value) || "");
}

function syncDetectAuthorLock() {
  const sel = $("detect-author");
  if (!sel) return;
  const on = othersGoldensAllowed();
  sel.disabled = !on;
  if (!on) sel.value = "";
}

async function openGoldenBank() {
  const ta = $("snippet-edit");
  const file = (ta && ta.dataset.file) || "";
  const res = await rpc("open_golden_bank", { file });
  log(
    `Golden bank: ${res.opened || res.folder || "goldens/"}\n` +
    `Guide: ${res.tutorial || "goldens/TUTORIAL.md"} · ${res.index || "goldens/INDEX.md"}\n`
  );
}

async function loadTickedSnippet() {
  const cb = document.querySelector("#detected-tests .detect-cb:checked");
  if (!cb) {
    alert("Tick one snippet row, then Load");
    return;
  }
  const file = decodeURIComponent(cb.dataset.file || "");
  const res = await rpc("snippet_source", { file, fn: cb.dataset.fn || "" });
  const ta = $("snippet-edit");
  if (ta) ta.value = res.text || "";
  if (ta) ta.dataset.file = file;
  log(`Loaded original ${String(res.file || file).replace(/\\/g, "/").split("/").slice(-2).join("/")} -- goldens/TUTORIAL.md\n`);
}

async function saveTickedSnippet() {
  const ta = $("snippet-edit");
  const file = (ta && ta.dataset.file) || "";
  if (!file) {
    alert("Load a snippet first");
    return;
  }
  const res = await rpc("save_snippet_source", {
    file,
    text: ta.value || "",
    operator: writeOperatorLabel() || "",
    allow_others: othersGoldensAllowed(),
  });
  log(`Saved original ${res.file || file}${res.note ? " -- " + res.note : ""}\n`);
  await refreshDetectedPanel({ preserveWrap: true });
}

if ($("btn-load-snippet")) {
  $("btn-load-snippet").onclick = async () => {
    try {
      await loadTickedSnippet();
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-save-snippet")) {
  $("btn-save-snippet").onclick = async () => {
    try {
      requireWriteOperator();
      await saveTickedSnippet();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-open-golden-bank")) {
  $("btn-open-golden-bank").onclick = async () => {
    try {
      await openGoldenBank();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-refresh-detected")) {
  $("btn-refresh-detected").onclick = async () => {
    try {
      await refreshDetectedPanel({ preserveWrap: true });
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-edit-tests")) {
  $("btn-edit-tests").onclick = () => {
    try {
      openTestsMenu();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("tests-menu-close")) {
  $("tests-menu-close").onclick = () => closeTestsMenu();
}
if ($("tests-menu-enable")) {
  $("tests-menu-enable").onclick = () => goTestsPage("enable");
}
if ($("tests-menu-write")) {
  $("tests-menu-write").onclick = () => goTestsPage("write");
}
if ($("tests-menu-prompt")) {
  $("tests-menu-prompt").onclick = () => goTestsPage("prompt");
}
if ($("tests-menu-gaps")) {
  $("tests-menu-gaps").onclick = () => goTestsPage("gaps");
}
if ($("tests-menu-scan")) {
  $("tests-menu-scan").onclick = () => goTestsPage("scan");
}
if ($("tests-menu-modal")) {
  $("tests-menu-modal").addEventListener("click", (e) => {
    if (e.target === $("tests-menu-modal")) closeTestsMenu();
  });
}

if ($("btn-save-campaign-tests")) {
  $("btn-save-campaign-tests").onclick = async () => {
    try {
      requireWriteOperator();
      const ids = campaignTestOrderIds();
      const res = await rpc("set_campaign_enabled_tests", { test_ids: ids, family: activeFamily });
      log(`Saved this Version tests: ${(res.enabled_tests || []).join(", ") || "(none)"}\n`);
      await refreshCampaignTests();
      await loadTests();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-fill-prompt")) {
  $("btn-fill-prompt").onclick = async () => {
    try {
      await fillAtePrompt();
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-copy-prompt")) {
  $("btn-copy-prompt").onclick = async () => {
    try {
      await copyAtePrompt();
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("prompt-path")) {
  $("prompt-path").addEventListener("change", () => {
    fillAtePrompt().catch(() => {});
  });
}
if ($("btn-path-b-template")) {
  $("btn-path-b-template").onclick = async () => {
    try {
      await loadPathBTemplate();
    } catch (e) {
      alert(e.message);
    }
  };
}
if ($("btn-save-path-b")) {
  $("btn-save-path-b").onclick = async () => {
    try {
      await savePathBFile();
    } catch (e) {
      alert(e.message);
    }
  };
}

if ($("btn-add-missing-tests")) {
  $("btn-add-missing-tests").onclick = async () => {
    try {
      requireWriteOperator();
      const res = await rpc("add_missing_campaign_tests");
      log(`Added from my versions: ${(res.added || []).join(", ") || "(none)"}\n`);
      await refreshCampaignTests();
      await loadTests();
    } catch (e) {
      alert(e.message);
    }
  };
}

async function wrapSelectedDetected() {
  const fam = activeFamily || "logic";
  const part = ($("db-part") && $("db-part").value) || "";
  const cbs = Array.from(document.querySelectorAll("#detected-tests .detect-cb:checked"));
  if (!cbs.length) {
    alert("Tick one or more trigger-ready rows");
    return;
  }
  for (const cb of cbs) {
    const file = decodeURIComponent(cb.dataset.file || "");
    const fn = cb.dataset.fn || "";
    const id = cb.dataset.id || "";
    if (cb.dataset.bridge === "1") {
      await rpc("enable_tests_on_part", {
        dest_part: part,
        test_ids: [id],
        family: fam,
      });
      log(`Enabled ${id} on this Version (original file, Continue not stdin)\n`);
      continue;
    }
    const res = await rpc("wrap_detected_test", {
      file,
      fn,
      test_id: id,
      family: fam,
      enable_part: part,
      operator: writeOperatorLabel() || "",
      allow_others: othersGoldensAllowed(),
    });
    const snip = res.snippet || {};
    const snipFile = String(snip.file || file || "").replace(/\\/g, "/").split("/").slice(-2).join("/");
    const snipLine = snip.lineno || "?";
    const mode = res.mode || "trigger";
    log(`Trigger ${res.id} at ${snipFile}:${snipLine} (${mode})\n`);
    if (res.loaded_family) updateFamilyChrome(res.loaded_family);
  }
  await loadTests();
  await refreshDetectedPanel({ preserveWrap: true });
}

// Click on detected panel: double-click row or use wrap via refresh button area
if ($("detected-tests")) {
  const wrapBtn = document.createElement("button");
  wrapBtn.type = "button";
  wrapBtn.id = "btn-wrap-detected";
  wrapBtn.className = "btn accent";
  wrapBtn.textContent = "Remember + enable on this Version";
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
      let ids = selectedTests();
      if (!ids.length) {
        document.querySelectorAll("#test-list .test-item input").forEach((i) => { i.checked = true; });
        renderRunPlans();
        ids = selectedTests();
      }
      if (!ids.length) return notice("Select at least one test");
      const pre = await rpc("bench_preflight");
      log(`Preflight ${JSON.stringify(pre)}\n`);
      if (pre.mode === "usb") {
        notice(
          "USB instruments answered *IDN. Use Discover -> Open Session -> START. " +
            "DEMO is fake SCPI. PSU output is not assumed ON until START."
        );
        return;
      }
      await applyDb();
      const m = await rpc("open_session", { sim: true });
      setTiles(m);
      sessionOpen = true;
      $("btn-start").disabled = false;
      log(`DEMO SIM session ${JSON.stringify(m)}\n`);
      await startInstrumentRun(ids, { autoContinue: true });
    } catch (e) {
      notice(e.message);
    }
  };
}

$("btn-start").onclick = () => clickStartOrContinue();

function campaignAlreadyApplied() {
  if (!dbContext) return false;
  const sel = currentDbSelection();
  const same = (a, b) => String(a || "").trim().toLowerCase() === String(b || "").trim().toLowerCase();
  return (
    same(dbContext.component, sel.component) &&
    same(dbContext.part, sel.part) &&
    same(dbContext.package, sel.package) &&
    same(dbContext.operator, sel.operator) &&
    same(dbContext.version, sel.version)
  );
}

async function clickStartOrContinue() {
  if (pendingPrompt) {
    switchPage("run");
    try {
      await respondContinue();
    } catch (e) {
      notice(e.message);
    }
    return;
  }
  if (runPollActive) {
    switchPage("run");
    try {
      const st0 = await rpc("session_status");
      if (st0 && st0.busy) {
        notice("Run already in progress -- Continue is on the right, or Abort. DELAY is settle, not a dead START.");
        paintRunDock();
        return;
      }
      runPollActive = false;
    } catch (_) {
      runPollActive = false;
    }
  }
  const ids = selectedTests();
  if (!ids.length) return notice("Select at least one test");
  const duts = selectedDuts();
  if (!duts.length) return notice("Select at least one DUT");
  if (!sessionOpen) return notice("Open Session or Open SIM first");
  try {
    requireWriteOperator();
  } catch (e) {
    return notice(e.message);
  }
  if (!campaignAlreadyApplied()) {
    log("START pins Setup campaign on the run (no Apply reload)\n");
  }
  try {
    const st = await rpc("session_status");
    if (st && st.sim) {
      const pre = await rpc("bench_preflight");
      log(`Preflight ${JSON.stringify(pre)}\n`);
      if (pre.mode === "usb") {
        notice(
          "USB answered *IDN but SIM session is still open (fake 3.7 MV/s, no live MSO). " +
            "Discover -> Open Session, then START. DEMO is the auto-walk."
        );
        return;
      }
    }
  } catch (e) {
    notice(e.message);
    return;
  }
  await startInstrumentRun(ids);
}

async function startInstrumentRun(ids, opts) {
  if (!sessionOpen) return notice("Open Session or Open SIM first");
  if (runPollActive) {
    try {
      const st0 = await rpc("session_status");
      if (!st0 || !st0.busy) runPollActive = false;
    } catch (_) {
      runPollActive = false;
    }
  }
  if (runPollActive) return notice("Run already in progress");
  switchPage("run");
  $("timeline").innerHTML = "";
  $("history").innerHTML = "";
  $("step-status-bar").innerHTML = "";
  substepState = {};
  activeSubstepTestId = "";
  lastScrollId = "";
  gateQueue = [];
  gateHeld = false;
  lastActivity = { phase: "run", text: "Building plan", delayS: 0, delayAt: 0 };
  updateGateDock(null);
  paintRunStrip();
  $("progress-bar").style.width = "0%";
  $("progress-meta").textContent = "starting…";
  $("next-banner").textContent = "Building plan…";
  setRunPill("running");
  runPollActive = true;
  const before = await rpc("session_status");
  const epoch0 = before.run_epoch || 0;
  try {
    const p = params();
    if (opts && opts.autoContinue) p.auto_continue = true;
    await rpc("run_sequence_async", { test_ids: ids, params: p });
    await waitForRunComplete(epoch0);
    const results = await rpc("get_last_run_results");
    let allOk = true;
    for (const r of results || []) {
      allOk = allOk && r.success;
    }
    let pdfPath = "";
    try {
      const exp = await rpc("export_datalog", params());
      pdfPath = exp.pdf || exp.html || exp.markdown || "";
      log(`STS datalog: ${pdfPath}\n`);
    } catch (e) {
      log(`STS export failed: ${e.message}\n`);
    }
    try {
      const filled = await rpc("fill_workbook", params());
      log(`Excel fill: ${JSON.stringify(filled)}\n`);
    } catch (e) {
      log(`Excel fill skipped: ${e.message}\n`);
    }
    const doc = await paintSessionReport(pdfPath);
    const hdr = (doc && doc.header) || {};
    const total = hdr.total || (results || []).length;
    const passN = hdr.pass || 0;
    const failN = hdr.fail || 0;
    const st = hdr.status || (allOk ? "completed" : "failed");
    if ($("next-banner")) {
      $("next-banner").textContent =
        `Complete: ${st} · Total ${total}  Pass ${passN}  Fail ${failN}`;
    }
    lastActivity = {
      phase: allOk ? "done" : "fail",
      text: `Complete: ${st} · Total ${total}  Pass ${passN}  Fail ${failN}`,
      delayS: 0,
      delayAt: 0,
    };
    paintRunStrip();
    try {
      const tl = await rpc("get_timeline");
      if (tl) renderTimeline(tl);
    } catch (_) { /* ignore */ }
    setRunPill(allOk ? "pass" : "fail");
    switchPage("results");
  } catch (e) {
    setRunPill("fail");
    if ($("next-banner")) $("next-banner").textContent = `Failed: ${e.message}`;
    log(`Run failed: ${e.message}\n`);
    notice(e.message);
  } finally {
    runPollActive = false;
  }
}

async function waitForRunComplete(epoch0) {
  const startEpoch = Number(epoch0) || 0;
  let idlePolls = 0;
  for (let i = 0; i < 14400; i++) {
    const st = await rpc("session_status");
    const epoch = Number(st.run_epoch || 0);
    if (epoch > startEpoch && !st.busy) {
      if (st.run_error) throw new Error(st.run_error);
      try { await pollEvents(); } catch (_) { /* keep waiting */ }
      return st;
    }
    if (!st.busy && epoch <= startEpoch) {
      idlePolls += 1;
      if (idlePolls >= 10) {
        throw new Error("Worker restarted during run -- Ctrl+F5 then DEMO");
      }
    } else {
      idlePolls = 0;
    }
    try { await pollEvents(); } catch (_) { /* worker may be mid-emit */ }
    await new Promise((r) => setTimeout(r, 250));
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
    gateHeld = false;
    lastActivity = { phase: "idle", text: "", delayS: 0, delayAt: 0 };
    updateGateDock(null);
    paintRunStrip();
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
  try {
    await respondAbort();
  } catch (e) {
    alert(e.message);
  }
};

if ($("modal-later")) {
  $("modal-later").onclick = () => dismissOperatorModal();
}
if ($("modal")) {
  $("modal").addEventListener("click", (e) => {
    if (e.target === $("modal")) dismissOperatorModal();
  });
}

function bindContinueButtons() {
  const go = async () => {
    try {
      await respondContinue();
    } catch (e) {
      alert(e.message);
    }
  };
  const stop = async () => {
    try {
      await respondAbort();
    } catch (e) {
      alert(e.message);
    }
  };
  const open = () => {
    if (pendingPrompt) openOperatorModal(pendingPrompt);
    else syncPendingGate({ autoOpen: true });
  };
  ["run-continue", "run-strip-continue"].forEach((id) => {
    if ($(id)) $(id).onclick = go;
  });
  ["run-abort", "run-strip-abort", "run-dock-abort"].forEach((id) => {
    if ($(id)) $(id).onclick = stop;
  });
  ["run-details", "run-strip-details"].forEach((id) => {
    if ($(id)) $(id).onclick = open;
  });
  if ($("run-dock-go")) $("run-dock-go").onclick = () => clickStartOrContinue();
}
bindContinueButtons();

if ($("gate-dock-btn")) {
  $("gate-dock-btn").onclick = async () => {
    const p = pendingPrompt || await syncPendingGate({ autoOpen: true });
    if (p) openOperatorModal(p);
    else if (!pendingPrompt) alert("No pending operator action -- test may still be running (check RUN bin).");
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
let runLedgerScope = "part";
let runLedgerBound = false;

function runWhen(s) {
  return String(s || "").replace("T", " ").slice(0, 19);
}

function fmtSpec(v) {
  if (v === null || v === undefined || v === "") return "";
  return String(v);
}

async function paintSessionReport(pdfPath) {
  const tb = $("results-table") && $("results-table").querySelector("tbody");
  if (!tb) return null;
  const doc = await rpc("get_session_report");
  tb.innerHTML = "";
  const steps = doc.steps || [];
  let n = 0;
  for (const s of steps) {
    const meas = Array.isArray(s.measurements) && s.measurements.length
      ? s.measurements
      : [{ id: "", result: s.success ? "pass" : "fail" }];
    for (const m of meas) {
      n += 1;
      const res = String((m && m.result) || (s.success ? "pass" : "fail"));
      tb.innerHTML += `<tr><td>${s.dut ?? ""}</td><td>${s.test_id || ""}</td><td>${(m && m.id) || ""}</td><td>${fmtSpec(m && m.min)}</td><td>${fmtSpec(m && m.max)}</td><td>${fmtSpec(m && m.typ)}</td><td>${fmtSpec(m && m.value)}</td><td>${res}</td><td>${s.summary || s.error || ""}</td></tr>`;
    }
  }
  if (!n) {
    tb.innerHTML = `<tr><td colspan="9">No session measurements yet -- START or DEMO</td></tr>`;
  }
  const hdr = doc.header || {};
  const fail = hdr.fail || 0;
  const status = hdr.status || "";
  if ($("results-sts-status")) {
    const bits = [
      status ? `Status ${status}` : "Run complete",
      `Total ${hdr.total || n}`,
      `Pass ${hdr.pass || 0}`,
      `Fail ${fail}`,
    ];
    if (pdfPath) bits.push(`PDF ${pdfPath}`);
    else if (doc.identity && doc.identity.lab_report) bits.push(`Lab ${(doc.identity && doc.identity.lab_report) || ""}`);
    $("results-sts-status").textContent = bits.join(" · ");
  }
  if ($("results-db-hint") && doc.identity) {
    $("results-db-hint").textContent =
      `Lab report: ${(doc.identity && doc.identity.lab_report) || ""} · pass ${(doc.header && doc.header.pass) || 0} / fail ${fail}` +
      (pdfPath ? ` · ${pdfPath}` : "");
  }
  return doc;
}

async function loadRunLedger(scope) {
  const tb = $("run-ledger") && $("run-ledger").querySelector("tbody");
  const hint = $("run-ledger-hint");
  if (!tb) return;
  if (scope) runLedgerScope = scope;
  try {
    const res = await rpc("list_runs", { scope: runLedgerScope, limit: 80 });
    tb.innerHTML = "";
    const runs = res.runs || [];
    if (hint) {
      hint.textContent =
        `${res.count || 0} run(s) · ${res.cloud_kind || "local"} · ${res.root || ""}` +
        (res.truncated ? " (truncated)" : "");
    }
    if (!runs.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 6;
      td.textContent = "No session JSON yet -- START or DEMO writes sessions/";
      tr.appendChild(td);
      tb.appendChild(tr);
      return;
    }
    for (const r of runs) {
      const tr = document.createElement("tr");
      for (const text of [
        runWhen(r.started),
        r.operator || "?",
        r.part || "",
        r.version || "",
        `${r.pass || 0}/${r.fail || 0}`,
      ]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.appendChild(td);
      }
      const td = document.createElement("td");
      const mk = (label, act) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "btn ghost";
        b.textContent = label;
        b.dataset.act = act;
        b.dataset.path = r.path || "";
        b.dataset.root = r.campaign_root || "";
        b.dataset.component = r.component || "";
        b.dataset.part = r.part || "";
        b.dataset.package = r.package || "";
        b.dataset.operator = r.operator || "";
        b.dataset.version = r.version || "";
        b.dataset.model = r.model || "";
        return b;
      };
      td.appendChild(mk("Open", "open"));
      td.appendChild(mk("Apply", "apply"));
      td.appendChild(mk("Delete", "delete"));
      tr.appendChild(td);
      tb.appendChild(tr);
    }
    if (!runLedgerBound && tb) {
      runLedgerBound = true;
      tb.addEventListener("click", onRunLedgerClick);
    }
  } catch (e) {
    if (hint) hint.textContent = `Runs: ${e.message}`;
  }
}

async function onRunLedgerClick(ev) {
  const b = ev.target && ev.target.closest && ev.target.closest("button[data-act]");
  if (!b) return;
  const act = b.dataset.act;
  try {
    if (act === "open") {
      await rpc("open_path", { path: b.dataset.path });
      return;
    }
    if (act === "apply") {
      paintCampaign({
        component: b.dataset.component,
        part: b.dataset.part,
        package: b.dataset.package,
        operator: b.dataset.operator,
        version: b.dataset.version,
        model: b.dataset.model || b.dataset.part,
        year: ($("db-year") && $("db-year").value) || "2026",
      });
      await applyDb();
      switchPage("setup");
      return;
    }
    if (act === "delete") {
      if (!confirm("Delete this session JSON? Campaign folders and the lab xlsx stay.")) return;
      await rpc("delete_run", { path: b.dataset.path });
      await loadRunLedger();
    }
  } catch (e) {
    alert(e.message);
  }
}

function escText(s) {
  return String(s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function seenAgo(ts) {
  if (!ts) return "";
  const t = Date.parse(ts);
  if (!Number.isFinite(t)) return String(ts).slice(0, 19);
  const min = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (min < 5) return "now";
  if (min < 120) return `${min}m`;
  const hr = Math.round(min / 60);
  if (hr < 48) return `${hr}h`;
  return `${Math.round(hr / 24)}d`;
}

async function loadProgressBoard() {
  const tb = $("progress-board") && $("progress-board").querySelector("tbody");
  const ownedTb = $("progress-owned") && $("progress-owned").querySelector("tbody");
  const freeTb = $("progress-unowned") && $("progress-unowned").querySelector("tbody");
  const hint = $("progress-board-hint");
  const list = $("board-items");
  if (!tb) return;
  try {
    const res = await rpc("progress_summary", { limit: 200 });
    tb.innerHTML = "";
    const presence = {};
    (res.presence || []).forEach((p) => {
      if (p && p.id) {
        presence[personFold(p.id)] = p;
        presence[personFold(displayPerson(p.id))] = p;
      }
      if (p && p.label) {
        presence[personFold(p.label)] = p;
        presence[personFold(displayPerson(p.label))] = p;
      }
    });
    const people = res.people || [];
    if (hint) {
      hint.textContent =
        `${res.run_count || 0} run(s) · ${(res.owned || []).length} owned · ${(res.unowned || []).length} no PIC · ${res.cloud_kind || "local"}`;
    }
    if ($("board-who") && !$("board-who").value.trim()) {
      try {
        $("board-who").value = requireWriteOperator();
      } catch (_) {
        $("board-who").value = boardAuthor() === "anon" ? "" : boardAuthor();
      }
    }
    if (!people.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 8;
      td.textContent = "No people yet -- Add person or START/DEMO writes sessions";
      tr.appendChild(td);
      tb.appendChild(tr);
    }
    for (const p of people) {
      const who = p.operator || "?";
      const hit = presence[personFold(who)] || {};
      const product = [p.part, p.package].filter(Boolean).join(" ");
      const idle = p.idle || "";
      const tr = document.createElement("tr");
      [
        who,
        product,
        hit.campaign || "",
        runWhen(p.last),
        String(p.runs || 0),
        `${p.pass || 0}/${p.fail || 0}`,
        idle,
        seenAgo(hit.ts),
      ].forEach((text, i) => {
        const td = document.createElement("td");
        td.textContent = text;
        if (i === 6 && (idle === "no runs" || String(idle).indexOf("idle") >= 0)) {
          td.className = "idle-quiet";
        }
        tr.appendChild(td);
      });
      tb.appendChild(tr);
    }
    paintOwnedSkus(ownedTb, res.owned || []);
    paintUnownedSkus(freeTb, res.unowned || []);
    const whoTb = $("progress-who-tests") && $("progress-who-tests").querySelector("tbody");
    if (whoTb) {
      whoTb.innerHTML = "";
      const rows = res.who_tests || [];
      if (!rows.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 5;
        td.textContent = "No assigned parts yet -- Add person + product codes";
        tr.appendChild(td);
        whoTb.appendChild(tr);
      } else {
        for (const r of rows.slice(0, 200)) {
          const tr = document.createElement("tr");
          [r.operator || "?", r.part || "", r.test_id || "", r.source || "--", r.kind || ""].forEach((text) => {
            const td = document.createElement("td");
            td.textContent = text;
            tr.appendChild(td);
          });
          whoTb.appendChild(tr);
        }
      }
    }
    if (list) {
      list.innerHTML = (res.board || []).slice().reverse().map((item) => {
        const k = item.kind === "question" ? "Q" : "C";
        return `<li><strong>${escText(k)} ${escText(item.author)}</strong> ${escText(runWhen(item.ts))}<br>${escText(item.text)}</li>`;
      }).join("") || "<li>No comments yet</li>";
    }
  } catch (e) {
    if (hint) hint.textContent = `Progress: ${e.message}`;
  }
}

function fillSkuTbody(tb, rows, cols, empty, emptyCols) {
  if (!tb) return;
  tb.innerHTML = "";
  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = emptyCols;
    td.textContent = empty;
    tr.appendChild(td);
    tb.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    cols(row).forEach((cell) => tr.appendChild(cell));
    tb.appendChild(tr);
  });
}

function paintOwnedSkus(tb, rows) {
  fillSkuTbody(tb, rows, (r) => {
    return [
      r.part || "",
      r.package || "",
      r.pic || "",
      (r.owners || []).join(", "),
      r.last_operator ? `${r.last_operator} ${runWhen(r.last)}` : runWhen(r.last),
    ].map((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      return td;
    });
  }, "No tracking PIC yet -- pick up below", 5);
}

function paintUnownedSkus(tb, rows) {
  fillSkuTbody(tb, rows, (r) => {
    const cells = [r.part || "", r.package || "", r.category || ""].map((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      return td;
    });
    const td = document.createElement("td");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn accent";
    b.textContent = "Pick up";
    b.dataset.claim = "1";
    b.dataset.part = r.part || "";
    b.dataset.package = r.package || "";
    b.dataset.category = r.category || "";
    b.dataset.model = r.model || "";
    td.appendChild(b);
    cells.push(td);
    return cells;
  }, "Every tracking SKU has a PIC (or PASS rows are hidden)", 4);
  if (tb && !tb.dataset.claimBound) {
    tb.dataset.claimBound = "1";
    tb.addEventListener("click", (ev) => {
      const b = ev.target && ev.target.closest && ev.target.closest("button[data-claim]");
      if (!b) return;
      claimBoardSku({
        part: b.dataset.part,
        package: b.dataset.package,
        category: b.dataset.category,
        model: b.dataset.model,
        create: false,
      }).catch((e) => alert(e.message));
    });
  }
}

function boardClaimLabel() {
  const typed = String(($("board-who") && $("board-who").value) || "").trim();
  if (typed) return typed;
  return requireWriteOperator();
}

async function claimBoardSku(opts) {
  const label = boardClaimLabel();
  const part = String((opts && opts.part) || "").trim();
  if (!part) throw new Error("Part is required");
  const res = await rpc("board_claim", {
    label,
    part,
    package: String((opts && opts.package) || "").trim(),
    category: String((opts && opts.category) || ""),
    model: String((opts && opts.model) || ""),
    create: Boolean(opts && opts.create),
  });
  const hint = $("progress-claim-hint");
  if (hint) {
    const pic = res.pic_claimed ? `PIC ${res.pic}` : `PIC stays ${res.pic || "empty"}`;
    hint.textContent = `${res.operator} · ${res.part} ${res.package} · ${pic} · ${res.root || ""}`;
  }
  await loadOwners();
  await loadInventory();
  try {
    ingestDbTree(await rpc("list_db_tree"));
  } catch (_) { /* tree optional */ }
  const who = String(res.operator || label || "");
  const row = ownerRowByName(who);
  if (row && !ownerIsObserver(row.id)) {
    if ($("owner-select")) $("owner-select").value = row.id;
    saveOwner(row.id);
    if ($("board-who")) $("board-who").value = displayPerson(row.label || who);
  }
  if (res.component && res.part && who && !ownerIsObserver(who)) {
    paintCampaign({
      component: res.component,
      part: res.part,
      package: res.package,
      operator: who,
      version: "Version_1",
      model: res.model || res.part,
      year: ($("db-year") && $("db-year").value) || "2026",
    });
    await applyDb();
  }
  await loadProgressBoard();
  return res;
}

async function registerFromBoard() {
  const part = String(($("board-part") && $("board-part").value) || "").trim();
  if (!part) throw new Error("Type a part we are testing");
  const pkg = String(($("board-package") && $("board-package").value) || "").trim();
  if (!pkg) throw new Error("Type a package (SC70-5, SOP8, ...)");
  await claimBoardSku({
    part,
    package: pkg,
    category: ($("board-class") && $("board-class").value) || "",
    create: true,
  });
}

function boardAuthor() {
  const id = ($("owner-select") && $("owner-select").value) || readSavedOwner();
  const row = ownersList.find((o) => o.id === id);
  return (row && row.label) || id || "anon";
}

async function postBoard(kind) {
  const el = $("board-text");
  const text = (el && el.value.trim()) || "";
  if (!text) throw new Error("Type a comment or question first");
  await rpc("board_add", { author: boardAuthor(), text, kind });
  if (el) el.value = "";
  await loadProgressBoard();
}

function firstRunOwnerKnown(label) {
  const raw = String(label || "").trim().replace(/\s*\(observe\)\s*$/i, "");
  if (!raw || raw === FIRST_RUN_ADD) return false;
  return Boolean(ownerRowByName(raw));
}

function paintFirstRunLists() {
  const names = ownersList.filter((o) => o && o.id !== "all" && !hiddenOwnerRow(o)).map((o) => {
    return displayPerson(o.label || o.id);
  }).filter(Boolean);
  fillCombo($("first-run-who"), names, String(($("first-run-who") && $("first-run-who").value) || ""));
  fillFirstRunFilters();
  const labels = trackingSkuRows().map((r) => [r.part, r.package, r.model].filter(Boolean).join(" · "));
  fillCombo($("first-run-product"), labels, String(($("first-run-product") && $("first-run-product").value) || ""));
  paintFirstRunProducts();
  syncFirstRunProductsVisibility();
}

function firstRunWhoIsObserver() {
  const who = $("first-run-who");
  const raw = String((who && who.value) || "").trim().replace(/\s*\(observe\)\s*$/i, "");
  if (who && who.dataset.addName === "1") return false;
  if (!raw) return false;
  return ownerIsObserver(raw);
}

function enterFirstRunAddName(keep) {
  const who = $("first-run-who");
  const wrap = $("first-run-who-wrap");
  if (!who) return;
  const fromArg = String(keep != null ? keep : "").trim();
  const fromBox = String(who.value || "").trim();
  const cand = (fromArg && fromArg !== FIRST_RUN_ADD) ? fromArg
    : (fromBox && fromBox !== FIRST_RUN_ADD) ? fromBox
    : "";
  const pick = (cand && !firstRunOwnerKnown(cand)) ? cand : "";
  who.dataset.addName = "1";
  who.readOnly = false;
  who.value = pick;
  who.placeholder = "Your name";
  if (wrap) wrap.classList.add("first-run-typing");
  syncComboChrome(who);
  who.focus();
  syncFirstRunProductsVisibility();
}

function exitFirstRunAddName() {
  const who = $("first-run-who");
  const wrap = $("first-run-who-wrap");
  if (!who) return;
  delete who.dataset.addName;
  who.readOnly = false;
  who.placeholder = "Pick or type your name";
  if (wrap) wrap.classList.remove("first-run-typing");
}

function syncFirstRunProductsVisibility() {
  const wrap = $("first-run-products-wrap");
  const hint = $("first-run-product-hint");
  const hide = firstRunWhoIsObserver();
  if (wrap) wrap.classList.toggle("hidden", hide);
  if (hint) {
    hint.textContent = hide
      ? "Observer -- no product folders."
      : "Type your name, Continue. Then Pick up one product on Results. Tick here only if you already know the SKU.";
  }
}

function selectedFirstRunSkus() {
  return trackingSkuRows().filter((r) => firstRunPicked.has(addSkuKey(r.part, r.package)));
}

function fillFirstRunFilters() {
  const klass = $("first-run-filter-class");
  const pkg = $("first-run-filter-pkg");
  const who = $("first-run-filter-who");
  const rows = trackingSkuRows();
  const keepK = klass ? klass.value : "";
  const keepP = pkg ? pkg.value : "";
  const keepW = who ? who.value : "";
  const classes = [];
  const pkgs = [];
  const seenC = new Set();
  const seenP = new Set();
  for (const r of rows) {
    const c = String(r.sheet_class || r.category || "").trim();
    const p = String(r.package || "").trim();
    if (c && !seenC.has(c)) { seenC.add(c); classes.push(c); }
    if (p && !seenP.has(p)) { seenP.add(p); pkgs.push(p); }
  }
  classes.sort();
  pkgs.sort();
  if (klass) {
    klass.innerHTML = `<option value="">All classes</option>` + classes.map((c) =>
      `<option value="${escText(c)}">${escText(c)}</option>`).join("");
    if (keepK && seenC.has(keepK)) klass.value = keepK;
  }
  if (pkg) {
    pkg.innerHTML = `<option value="">All packages</option>` + pkgs.map((p) =>
      `<option value="${escText(p)}">${escText(p)}</option>`).join("");
    if (keepP && seenP.has(keepP)) pkg.value = keepP;
  }
  if (who) {
    const people = [];
    const seenW = new Set();
    for (const o of ownersList || []) {
      if (!o || o.id === "all" || ownerIsObserver(o.id)) continue;
      const lab = String(o.label || o.id || "").trim();
      const k = lab.toLowerCase();
      if (!lab || seenW.has(k)) continue;
      seenW.add(k);
      people.push(lab);
    }
    who.innerHTML = `<option value="">All SKUs</option><option value="mine">Mine</option>` +
      people.map((p) => `<option value="${escText(p)}">${escText(p)}</option>`).join("");
    const ok = [...who.options].some((opt) => opt.value === keepW);
    who.value = ok ? keepW : "";
  }
}

function firstRunProductQuery() {
  return String(($("first-run-product") && $("first-run-product").value) || "").trim().toLowerCase();
}

function firstRunFilteredRows() {
  const klass = String(($("first-run-filter-class") && $("first-run-filter-class").value) || "").trim();
  const pkg = String(($("first-run-filter-pkg") && $("first-run-filter-pkg").value) || "").trim();
  const whoF = String(($("first-run-filter-who") && $("first-run-filter-who").value) || "");
  const q = firstRunProductQuery();
  let who = "";
  if (whoF === "mine") {
    who = String(($("first-run-who") && $("first-run-who").value) || "").trim();
  } else if (whoF) {
    who = whoF;
  }
  return trackingSkuRows().filter((r) => {
    if (klass && String(r.sheet_class || r.category || "") !== klass) return false;
    if (pkg && String(r.package || "") !== pkg) return false;
    if (who) {
      const known = firstRunOwnerKnown(who);
      const codes = minePartCodes(who);
      if (known || codes.length) {
        if (!skuHandledBy(r.part, who)) return false;
      }
    }
    if (!q) return true;
    const picLab = operatorFromPic(r.pic) || r.pic || "";
    const blob = [r.part, r.package, r.model, r.sheet_class, r.category, picLab].join(" ").toLowerCase();
    return blob.includes(q);
  });
}

function diskPackagesForPart(part) {
  const want = String(part || "").toUpperCase();
  const found = [];
  for (const node of Object.values(dbTree.components || {})) {
    const slot = ((node && node.parts) || {})[want];
    if (!slot) continue;
    for (const p of Object.keys(slot.packages || {})) {
      if (p && !found.includes(p)) found.push(p);
    }
  }
  return found;
}

function paintFirstRunDetect() {
  const el = $("first-run-detect");
  if (!el) return;
  const q = firstRunProductQuery().toUpperCase();
  const rows = trackingSkuRows();
  const shown = firstRunFilteredRows();
  const hit = q ? rows.find((r) => q.includes(r.part.toUpperCase())) : null;
  const partRows = hit ? rows.filter((r) => r.part === hit.part) : [];
  let msg = `Showing ${shown.length} / ${rows.length} tracking SKUs (inventory.yaml, no scrape).`;
  if (partRows.length) {
    const pkgs = [...new Set(partRows.map((r) => r.package).filter(Boolean))];
    const extra = diskPackagesForPart(partRows[0].part).filter((p) => !pkgs.includes(p));
    msg = `${partRows[0].part} tracking packages: ${pkgs.join(", ") || "(none)"}.`;
    if (extra.length) {
      msg += ` Disk also has (not offered here until an inventory.yaml row exists): ${extra.join(", ")}.`;
    }
    if (/MSOP/i.test(q) && !pkgs.some((p) => /MSOP/i.test(p))) {
      msg += " No MSOP row for this part on the tracking sheet (MSOP in tracking is RS2227).";
    }
  }
  el.textContent = msg;
}

function paintFirstRunProducts() {
  const box = $("first-run-products");
  if (!box) return;
  const checked = firstRunPicked;
  const rows = firstRunFilteredRows();
  const by = new Map();
  for (const r of rows) {
    const g = r.sheet_class || r.category || "other";
    if (!by.has(g)) by.set(g, []);
    by.get(g).push(r);
  }
  let html = "";
  for (const [g, listG] of by) {
    html += `<div class="sku-family">${escText(g)}</div>` + listG.map((r) => {
      const picLab = operatorFromPic(r.pic) || String(r.pic || "").trim();
      const bits = [r.part, r.package, r.model, picLab ? ("PIC " + picLab) : ""].filter(Boolean).join(" · ");
      const on = checked.has(addSkuKey(r.part, r.package));
      return `<label class="check"><input type="checkbox" class="first-run-sku-cb" data-part="${escText(r.part)}" data-package="${escText(r.package)}" data-category="${escText(r.category)}" data-model="${escText(r.model)}" ${on ? "checked" : ""} /> ${escText(bits)}</label>`;
    }).join("");
  }
  box.innerHTML = html || `<p class="hint">No SKUs match this filter. Switch Owner to All people, or clear class/package.</p>`;
  paintFirstRunProductChips();
  paintFirstRunDetect();
}

function paintFirstRunProductChips() {
  const el = $("first-run-product-chips");
  if (!el) return;
  const skus = selectedFirstRunSkus();
  el.innerHTML = "";
  if (!skus.length) {
    const empty = document.createElement("span");
    empty.className = "hint";
    empty.textContent = "none yet -- add or tick";
    el.appendChild(empty);
    return;
  }
  for (const r of skus) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = `${r.part} ${r.package}`.trim() + " x";
    chip.title = "Deselect";
    chip.onclick = () => {
      firstRunPicked.delete(addSkuKey(r.part, r.package));
      paintFirstRunProducts();
    };
    el.appendChild(chip);
  }
}

function addFirstRunProduct(raw) {
  const text = String(raw || "").trim();
  if (!text) return;
  const rows = trackingSkuRows();
  const exact = rows.filter((r) => {
    const bits = [r.part, r.package, r.model].filter(Boolean).join(" · ");
    return bits === text || bits.toLowerCase() === text.toLowerCase();
  });
  const hits = exact.length ? exact : rows.filter((r) =>
    r.part === text.toUpperCase() || r.part.toLowerCase() === text.toLowerCase()
  );
  if (!hits.length) {
    notice("Unknown product -- tracking sheet only");
    return;
  }
  for (const hit of hits) firstRunPicked.add(addSkuKey(hit.part, hit.package));
  paintFirstRunProducts();
}

function needsFirstRun() {
  const id = readSavedOwner();
  return !id || id === "all";
}

async function completeFirstRun() {
  const who = $("first-run-who");
  const typed = String((who && who.value) || "").trim();
  const typing = (who && who.dataset.addName === "1") || (typed && !firstRunOwnerKnown(typed));
  let id = "";
  let label = "";
  if (typing) {
    if (!typed || typed === FIRST_RUN_ADD) throw new Error("Type your name, or open the list to pick one");
    const res = await rpc("upsert_owner", { label: typed, update_defaults: false });
    id = (res.owner && res.owner.id) || "";
    label = (res.owner && res.owner.label) || typed;
    await loadOwners();
  } else {
    const raw = typed.replace(/\s*\(observe\)\s*$/i, "");
    const row = ownerRowByName(raw);
    id = (row && row.id) || "";
    label = (row && row.label) || raw;
  }
  if (!id) throw new Error("Pick a name, or + Add Your Name");
  const observer = ownerIsObserver(id);
  const skus = observer ? [] : selectedFirstRunSkus();
  saveOwner(id);
  if ($("owner-select")) $("owner-select").value = id;
  if ($("board-who")) $("board-who").value = displayPerson(label || typed);
  if (!observer && skus.length) {
    const nDut = Number(($("dut-count") && $("dut-count").value) || 4);
    await rpc("provision_operator", {
      label,
      sample_size: nDut,
      with_workbook: true,
      only_skus: skus,
    });
    await loadOwners();
    ingestDbTree(await rpc("list_db_tree"));
    mergeInventoryIntoTree();
    await applyOwner(id);
  }
  const modal = $("first-run-modal");
  if (modal) modal.classList.add("hidden");
  switchPage("results");
  await loadProgressBoard();
}

let heartTimer = 0;
function startHeartbeat() {
  if (heartTimer) return;
  const ping = () => {
    const id = ($("owner-select") && $("owner-select").value) || readSavedOwner();
    if (!id || ownerIsObserver(id)) return;
    const row = ownersList.find((o) => o.id === id);
    const sel = currentDbSelection();
    rpc("heartbeat", {
      id,
      label: (row && row.label) || id,
      campaign: [sel.component, sel.part, sel.package].filter(Boolean).join("/"),
    }).catch(() => {});
  };
  ping();
  heartTimer = setInterval(ping, 180000);
}

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
  if (!tests.length) {
    sel.innerHTML = '<option value="">-- no mapped tests --</option>';
    return;
  }
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
  if (lastActivity.phase === "delay" || pendingPrompt) paintRunStrip();
}

function pollLoop() {
  pollEvents().finally(() => {
    const ms = runPollActive || pendingPrompt ? 350 : 900;
    setTimeout(pollLoop, ms);
  });
}

(async function boot() {
  initCombos();
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
  if ($("channel-picks") && !document.querySelector(".ch-cb")) {
    applyProbeChannels(fallbackProbeChannels(), { force: true });
  }
  if ($("dut-count")) {
    $("dut-count").addEventListener("change", () => {
      renderDutPicks();
      renderRunPlans();
      persistRunPrefs().catch(() => {});
    });
  }
  if ($("walk-order")) {
    try {
      applyWalkOrder(localStorage.getItem("ate.walkOrder") || "channel");
    } catch (e) {
      applyWalkOrder("channel");
    }
    $("walk-order").addEventListener("change", () => {
      persistWalkOrder().catch(() => {});
    });
  }
  if ($("notice-banner-ok")) {
    $("notice-banner-ok").onclick = () => hideNotice();
  }
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
  const bindRuns = (id, scope) => {
    const el = $(id);
    if (!el) return;
    el.onclick = () => loadRunLedger(scope).catch((e) => alert(e.message));
  };
  bindRuns("btn-runs-campaign", "campaign");
  bindRuns("btn-runs-part", "part");
  bindRuns("btn-runs-all", "all");
  if ($("btn-runs-reload")) {
    $("btn-runs-reload").onclick = () => loadRunLedger().catch((e) => alert(e.message));
  }
  if ($("btn-board-comment")) {
    $("btn-board-comment").onclick = () => postBoard("comment").catch((e) => alert(e.message));
  }
  if ($("btn-board-question")) {
    $("btn-board-question").onclick = () => postBoard("question").catch((e) => alert(e.message));
  }
  if ($("btn-board-register")) {
    $("btn-board-register").onclick = () => registerFromBoard().catch((e) => alert(e.message));
  }
  if ($("btn-board-reload")) {
    $("btn-board-reload").onclick = () => loadProgressBoard().catch((e) => alert(e.message));
  }
  if ($("btn-board-issue")) {
    $("btn-board-issue").onclick = async () => {
      try {
        const res = await rpc("progress_summary", { limit: 20 });
        const q = (res.board || []).filter((x) => x.kind === "question").pop();
        if (!q) throw new Error("Post a question first");
        const title = String(q.text || "Lab question").slice(0, 80);
        const body = `${q.author || ""}: ${q.text || ""}\n\nSaved on the lab board (${res.root || ""}).`;
        const issued = await rpc("open_github_issue", { title, body });
        alert(issued.url || "Issue opened");
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("first-run-go")) {
    $("first-run-go").onclick = () => completeFirstRun().catch((e) => alert(e.message));
  }
  if ($("first-run-products")) {
    $("first-run-products").addEventListener("change", (ev) => {
      const cb = ev.target;
      if (!cb || !cb.classList || !cb.classList.contains("first-run-sku-cb")) return;
      const k = addSkuKey(cb.dataset.part, cb.dataset.package);
      if (cb.checked) firstRunPicked.add(k);
      else firstRunPicked.delete(k);
      paintFirstRunProductChips();
    });
  }
  const onFirstRunFilter = () => paintFirstRunProducts();
  if ($("first-run-filter-class")) $("first-run-filter-class").addEventListener("change", onFirstRunFilter);
  if ($("first-run-filter-pkg")) $("first-run-filter-pkg").addEventListener("change", onFirstRunFilter);
  if ($("first-run-filter-who")) $("first-run-filter-who").addEventListener("change", onFirstRunFilter);
  if ($("part-scope")) {
    $("part-scope").addEventListener("change", () => {
      try { localStorage.setItem(PART_SCOPE_KEY, $("part-scope").value || "mine"); } catch (_) { /* ignore */ }
      refreshDbCascades(currentDbSelection(), "db-part");
    });
  }
  const bindSearch = (id, fn) => {
    const el = $(id);
    if (!el) return;
    el.addEventListener("input", fn);
  };
  bindSearch("test-list-search", applyTestListSearch);
  bindSearch("campaign-test-search", applyCampaignTestSearch);
  bindSearch("detect-search", () => paintDetectedRows());
  if ($("detect-product")) {
    $("detect-product").addEventListener("change", () => paintDetectedRows());
  }
  if ($("btn-export-datalog")) {
    $("btn-export-datalog").onclick = async () => {
      try {
        const exp = await rpc("export_datalog", params());
        log(`STS datalog\n  ${exp.markdown || ""}\n  ${exp.html || ""}\n  ${exp.pdf || ""}\n`);
        await paintSessionReport(exp.pdf || "");
        if (exp.html) {
          try { await rpc("open_path", { path: exp.html }); } catch (_) { /* ignore */ }
        }
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("btn-fill-excel")) {
    $("btn-fill-excel").onclick = async () => {
      try {
        const res = await rpc("fill_workbook", params());
        log(`Excel fill: ${res.status || ""} filled=${res.filled || 0} narrative=${res.narrative || 0} notes=${res.annotated || 0} photos=${res.photos || 0} ${res.excel || ""}\n`);
        if ($("results-db-hint")) {
          $("results-db-hint").textContent = `Excel ${res.status}: ${res.excel || ""} (${res.filled || 0} cells, ${res.narrative || 0} intro, ${res.photos || 0} photos)`;
        }
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("btn-fetch-datasheet")) {
    $("btn-fetch-datasheet").onclick = async () => {
      try {
        const part = (($("db-part") && $("db-part").value) || "").trim();
        if (!part) throw new Error("Apply a campaign part first");
        const res = await rpc("fetch_datasheet", { part });
        const specs = (res.limits && res.limits.specs) || res.specs || [];
        const src = (res.limits && res.limits.source) || res.source || "";
        const yamlPath = (res.limits && res.limits.yaml) || res.yaml || "";
        log(`Limits ${res.part}: source=${src} engine=${(res.extract || {}).engine || ""} specs=${specs.length}\n${res.copilot || res.note || ""}\n`);
        if ($("results-db-hint")) {
          $("results-db-hint").textContent = `Fetched ${res.part} limits -> ${yamlPath} excel=${(res.fill || {}).excel || ""}`;
        }
        await loadTests();
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("layout-overlay")) {
    $("layout-overlay").addEventListener("change", () => {
      const pair = $("layout-compare-pair");
      if (pair) pair.classList.toggle("overlay", $("layout-overlay").checked);
    });
  }

  // ---- A14 Recipe canvas ----
  let recipeCanvasApi = null;
  let recipeGraphDraft = null;
  let recipeProductPick = "";
  let recipePersonPick = "";

  function ensureRecipeCanvas() {
    const root = $("recipe-root");
    const hint = $("recipe-canvas-hint");
    if (!root) return;
    if (recipeCanvasApi) return;
    if (!window.ATERecipeCanvas || typeof window.ATERecipeCanvas.mount !== "function") {
      if (hint) hint.textContent = "Canvas bundle missing (ate/ui/web/canvas/recipe-canvas.js).";
      return;
    }
    recipeCanvasApi = window.ATERecipeCanvas.mount(root, {
      graph: recipeGraphDraft || undefined,
      onChange: (g) => { recipeGraphDraft = g; },
    });
    if (hint) hint.textContent = "Canvas ready. Add blocks from the palette, then Save recipe.";
  }

  async function refreshRecipeList() {
    const box = $("recipe-list");
    if (!box) return;
    try {
      const fam = ($("recipe-family") && $("recipe-family").value) || "";
      const res = await rpc("list_recipes", { family: fam === "comparator" ? "" : fam });
      const rows = res.recipes || [];
      box.innerHTML = rows.length
        ? rows.map((r) => `<button type="button" class="recipe-hit" data-rid="${escText(r.id)}">${escText(r.id)} · ${escText(r.label || "")} · ${escText(r.family || "")}</button>`).join("")
        : "<span class='hint'>No recipes yet.</span>";
      box.querySelectorAll("[data-rid]").forEach((btn) => {
        btn.addEventListener("click", () => {
          if ($("recipe-id")) $("recipe-id").value = btn.getAttribute("data-rid") || "";
          loadRecipeIntoUi().catch((e) => alert(e.message));
        });
      });
    } catch (e) {
      box.textContent = e.message || String(e);
    }
  }

  async function loadRecipeIntoUi() {
    const rid = (($("recipe-id") && $("recipe-id").value) || "").trim();
    if (!rid) throw new Error("Set recipe id first");
    const res = await rpc("load_recipe", { recipe_id: rid });
    const r = res.recipe || {};
    if ($("recipe-label")) $("recipe-label").value = r.label || "";
    if ($("recipe-short")) $("recipe-short").value = r.shortform || "";
    if ($("recipe-details")) $("recipe-details").value = r.details || "";
    if ($("recipe-family") && r.family) $("recipe-family").value = r.family;
    if ($("recipe-products")) $("recipe-products").value = (r.products || []).join(", ");
    if ($("recipe-n") && r.logic_inputs != null) $("recipe-n").value = r.logic_inputs;
    if ($("recipe-levels") && Array.isArray(r.levels)) $("recipe-levels").value = r.levels.join(", ");
    recipeGraphDraft = { nodes: r.nodes || [], edges: r.edges || [] };
    ensureRecipeCanvas();
    if (recipeCanvasApi && recipeCanvasApi.setGraph) {
      recipeCanvasApi.setGraph(recipeGraphDraft);
    }
    if ($("recipe-rel-hint")) $("recipe-rel-hint").textContent = `Loaded ${rid} from ${r.id || rid}`;
  }

  async function saveRecipeFromUi() {
    const rid = (($("recipe-id") && $("recipe-id").value) || "").trim();
    if (!rid) throw new Error("Recipe id required");
    ensureRecipeCanvas();
    const graph = (recipeCanvasApi && recipeCanvasApi.getGraph && recipeCanvasApi.getGraph()) || recipeGraphDraft || { nodes: [], edges: [] };
    const levels = String(($("recipe-levels") && $("recipe-levels").value) || "")
      .split(/[,;]+/)
      .map((s) => Number(s.trim()))
      .filter((n) => Number.isFinite(n));
    const products = String(($("recipe-products") && $("recipe-products").value) || "")
      .split(/[,;]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    const n = Number(($("recipe-n") && $("recipe-n").value) || 2);
    const payload = {
      ...currentDbSelection(),
      recipe_id: rid,
      label: ($("recipe-label") && $("recipe-label").value) || rid,
      shortform: ($("recipe-short") && $("recipe-short").value) || "",
      details: ($("recipe-details") && $("recipe-details").value) || "",
      family: ($("recipe-family") && $("recipe-family").value) || "logic",
      products,
      graph: {
        ...graph,
        logic_inputs: n,
        levels,
      },
    };
    const res = await rpc("save_recipe", payload);
    if ($("recipe-rel-hint")) {
      $("recipe-rel-hint").textContent = `Saved ${res.id} -> ${res.path || ""}`;
    }
    await refreshRecipeList();
    return res;
  }

  async function previewRecipeCorners() {
    const n = Number(($("recipe-n") && $("recipe-n").value) || 2);
    const levels = String(($("recipe-levels") && $("recipe-levels").value) || "0, 5.5")
      .split(/[,;]+/)
      .map((s) => Number(s.trim()))
      .filter((x) => Number.isFinite(x));
    const res = await rpc("preview_corners", { logic_inputs: n, levels });
    const hint = $("recipe-corners-hint");
    if (hint) {
      const sample = (res.corners || []).slice(0, 8).map((c) => c.join("/")).join(" · ");
      hint.textContent = `Corners: ${res.count || 0} (n=${res.logic_inputs}) e.g. ${sample}`;
    }
  }

  async function paintProductHits() {
    const q = (($("recipe-product-q") && $("recipe-product-q").value) || "").trim();
    const box = $("recipe-product-hits");
    if (!box) return;
    if (!q) { box.innerHTML = ""; return; }
    const res = await rpc("grep_products", { q });
    const hits = res.hits || [];
    box.innerHTML = hits.map((h) =>
      `<button type="button" class="recipe-hit" data-pk="${escText(h.part_key)}">${escText(h.part)} · ${escText(h.package || h.source || "")}</button>`
    ).join("") || "<span class='hint'>No hit. Tracking sheet only.</span>";
    box.querySelectorAll("[data-pk]").forEach((btn) => {
      btn.addEventListener("click", () => {
        recipeProductPick = btn.getAttribute("data-pk") || "";
        const cur = ($("recipe-products") && $("recipe-products").value) || "";
        const parts = cur.split(/[,;]+/).map((s) => s.trim()).filter(Boolean);
        if (recipeProductPick && !parts.includes(recipeProductPick)) parts.push(recipeProductPick);
        if ($("recipe-products")) $("recipe-products").value = parts.join(", ");
      });
    });
  }

  async function paintPersonHits() {
    const q = (($("recipe-person-q") && $("recipe-person-q").value) || "").trim();
    const box = $("recipe-person-hits");
    if (!box) return;
    if (!q) { box.innerHTML = ""; return; }
    const res = await rpc("grep_people", { q });
    const hits = res.hits || [];
    box.innerHTML = hits.map((h) =>
      `<button type="button" class="recipe-hit" data-lab="${escText(h.label)}">${escText(h.label)} · ${(h.parts || []).slice(0, 4).join(", ")}</button>`
    ).join("") || "<span class='hint'>No person yet -- Add will create owners.yaml row.</span>";
    box.querySelectorAll("[data-lab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        recipePersonPick = btn.getAttribute("data-lab") || "";
        if ($("recipe-person-q")) $("recipe-person-q").value = recipePersonPick;
      });
    });
  }

  if ($("btn-recipe-preview")) $("btn-recipe-preview").onclick = () => previewRecipeCorners().catch((e) => alert(e.message));
  if ($("btn-recipe-load")) $("btn-recipe-load").onclick = () => loadRecipeIntoUi().catch((e) => alert(e.message));
  if ($("btn-recipe-save")) $("btn-recipe-save").onclick = () => saveRecipeFromUi().catch((e) => alert(e.message));
  if ($("btn-recipe-refresh-list")) $("btn-recipe-refresh-list").onclick = () => refreshRecipeList().catch(() => {});
  if ($("recipe-product-q")) {
    let t;
    $("recipe-product-q").addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => paintProductHits().catch(() => {}), 200);
    });
  }
  if ($("recipe-person-q")) {
    let t2;
    $("recipe-person-q").addEventListener("input", () => {
      clearTimeout(t2);
      t2 = setTimeout(() => paintPersonHits().catch(() => {}), 200);
    });
  }
  if ($("btn-recipe-attach-product")) {
    $("btn-recipe-attach-product").onclick = async () => {
      try {
        const code = recipeProductPick || (($("recipe-product-q") && $("recipe-product-q").value) || "").trim();
        const lab = (($("db-operator") && $("db-operator").value) || ($("owner-select") && $("owner-select").value) || "").trim();
        if (!lab || lab.toLowerCase() === "all") throw new Error("Pick a real operator first (not All)");
        if (!code) throw new Error("Type / pick a product first");
        const res = await rpc("attach_product", { label: lab, part: code });
        if ($("recipe-rel-hint")) $("recipe-rel-hint").textContent = `Attached ${code} to ${lab}: matched=${(res.matched || []).length} unmatched=${(res.unmatched || []).length}`;
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("btn-recipe-attach-person")) {
    $("btn-recipe-attach-person").onclick = async () => {
      try {
        const lab = recipePersonPick || (($("recipe-person-q") && $("recipe-person-q").value) || "").trim();
        if (!lab) throw new Error("Type a person name");
        const part = recipeProductPick || (($("recipe-products") && $("recipe-products").value) || "").split(/[,;]/)[0].trim();
        const res = await rpc("attach_person", { label: lab, part });
        if ($("recipe-rel-hint")) $("recipe-rel-hint").textContent = `Person ${lab} upserted${part ? ` + ${part}` : ""}`;
        await loadOwners();
      } catch (e) {
        alert(e.message);
      }
    };
  }
  if ($("recipe-id") && !$("recipe-id").value) $("recipe-id").value = "demo_corners";

  let pingOk = false;
  for (let i = 0; i < 20; i++) {
    try {
      setBootSplash("Connecting...");
      if (!pingOk) {
        await rpc("ping");
        pingOk = true;
      }
      setBootSplash("Checking for today's update...");
      try {
        const syn = await rpc("sync_repo");
        setBootSplash(syn.message || "Ready");
      } catch (_) {
        setBootSplash("Starting without a git update...");
      }
      setBootSplash("Loading...");
      $("session-hint").textContent = "Worker online — Discover → Open Session";
      await loadOwners();
      await loadCategories();
      await loadInventory();
      await loadDb();
      await refreshCloudDbHint();
      mergeInventoryIntoTree();
      refreshDbCascades(currentDbSelection());
      if (!needsFirstRun()) {
        syncOwnerSelectFromFolder(($("db-operator") && $("db-operator").value) || "");
      }
      await syncFamilyFromWorker();
      await loadFixtureCatalog();
      await loadParamDefaults();
      await syncPendingGate({ autoOpen: false });
      paintFirstRunLists();
      if (needsFirstRun() && $("first-run-modal")) {
        $("first-run-modal").classList.remove("hidden");
      }
      startHeartbeat();
      const st = await syncRunState();
      if (st && st.busy) {
        runPollActive = true;
        switchPage("run");
        waitForRunComplete((st.run_epoch || 1) - 1)
          .then(() => paintSessionReport())
          .then(() => { runPollActive = false; })
          .catch(() => { runPollActive = false; });
      } else {
        await paintSessionReport();
      }
      await loadTests();
      await refreshSession();
      hideBootSplash();
      return;
    } catch (e) {
      if (i === 0) {
        setBootSplash("Starting services...");
        $("session-hint").textContent =
          "Waiting for worker on :8766 — double-click restart_ate_worker.bat";
      }
      if (i === 19) {
        log(`Boot failed: ${e.message}\n`);
        setBootSplash(
          pingOk
            ? `Worker up, load failed: ${e.message}`
            : "Could not start. Close and double-click START.bat again."
        );
        $("session-hint").textContent = pingOk
          ? "Worker online — campaign load failed. Ctrl+F5"
          : "Worker offline — run restart_ate_worker.bat then Ctrl+F5";
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
  }
})();
