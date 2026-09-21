"""Fail-closed UI contract for ate/ui/web (A17-T02).

Run: python -m ate.core.check_ui_contract
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "ui" / "web"
INDEX = WEB / "index.html"


def main() -> int:
    errors: list[str] = []
    if not INDEX.is_file():
        print("FAIL check_ui_contract: index.html missing")
        return 1
    html = INDEX.read_text(encoding="utf-8")

    tabs = re.findall(r'data-page="([a-z0-9\-]+)"', html)
    if not tabs:
        errors.append("no data-page tabs found")
    for name in tabs:
        if f'id="page-{name}"' not in html:
            errors.append(f"tab data-page={name!r} missing section#page-{name}")

    nav_count = len(re.findall(r'<nav\s+class="[^"]*\btabs\b', html))
    if nav_count != 1:
        errors.append(f"expected exactly 1 nav.tabs, found {nav_count}")

    # Google Fonts families: count family= tokens only
    families: list[str] = []
    for m in re.finditer(r"family=([A-Za-z0-9+]+)", html):
        fam = m.group(1).replace("+", " ")
        if fam and fam not in families:
            families.append(fam)
    if len(families) > 3:
        errors.append(f"too many webfont families ({len(families)}): {families}")

    if "UI_CONTRACT.md" not in (WEB / "UI_CONTRACT.md").name or not (WEB / "UI_CONTRACT.md").is_file():
        errors.append("ate/ui/web/UI_CONTRACT.md missing")
    agents = Path(__file__).resolve().parents[2] / "AGENTS.md"
    if not agents.is_file():
        errors.append("repo AGENTS.md missing")
    claude = Path(__file__).resolve().parents[2] / "CLAUDE.md"
    ai_md = Path(__file__).resolve().parents[2] / "AI.md"
    if not claude.is_file() or not ai_md.is_file():
        errors.append("CLAUDE.md and AI.md must exist (always-on system prompt)")

    if "tags" in tabs:
        errors.append("Tags must live in Setup More, not a Tags tab")
    if 'id="tag-board-select"' in html or 'id="btn-tag-add-board"' in html:
        errors.append("Legacy dual board combo (tag-board-select) must stay removed")
    if 'id="campaign-board"' not in html:
        errors.append("Setup must have one #campaign-board (single fixture PCB)")
    if 'id="label-kind-hint"' not in html:
        errors.append("Setup tags hint missing")
    if 'id="board-pick-hint"' not in html:
        errors.append("Board pick hint missing")
    if "detect" not in tabs:
        errors.append("Tests/Detect tab (data-page=detect) missing")
    setup_html = html.split('id="page-setup"', 1)[-1].split('id="page-detect"', 1)[0] if 'id="page-detect"' in html else html
    if 'id="detected-tests"' in setup_html or 'id="campaign-tests"' in setup_html:
        errors.append("Detected / customize tests must not live on Setup")
    if 'id="detected-tests"' not in html or 'id="page-detect"' not in html:
        errors.append("Detected tests panel missing from Tests page")
    if 'id="btn-edit-tests"' not in html or 'id="tests-menu-modal"' not in html:
        errors.append("Setup Add/edit tests button + popup missing")
    if 'id="campaign-tests"' not in html or 'id="version-gaps"' not in html:
        errors.append("Tests page customize / version-gaps panels missing")
    if "this Version" not in html or ("pointer" not in html.lower() and "snippet" not in html.lower()):
        errors.append("Tests page must say Path A is this Version and scan uses snippet pointer")
    if 'id="btn-copy-tests"' in html or 'id="detect-copy-from"' in html:
        errors.append("Copy tests between parts must stay parked")
    if 'id="btn-start"' not in html or 'id="btn-demo"' not in html:
        errors.append("START / DEMO controls missing")
    if 'id="run-dock"' not in html or 'id="run-dock-go"' not in html:
        errors.append("sticky right START/Continue #run-dock missing")
    if 'id="run-need-hint"' not in html:
        errors.append("Setup must say START uses ticked TestSpec ids (not all tiles)")
    if "logic-dc-fold" not in html:
        errors.append("#panel-logic-dc must collapse product_model JSON behind details")
    start_at = setup_html.find('id="btn-start"')
    plans_at = setup_html.find('id="test-plans"')
    if start_at < 0 or plans_at < 0 or start_at > plans_at:
        errors.append("START must sit above the test accordion")
    if 'data-family="power"' not in html:
        errors.append("Power family rail button missing")
    if 'id="campaign-board"' not in html or 'id="db-tag-chips"' not in html:
        errors.append("Setup board pick + tag chips missing")
    if 'id="btn-setup-add-label"' in html or 'id="setup-label-kind"' in html:
        errors.append("Kind+Value board pile removed; use #campaign-board + free tags")
    if 'id="btn-add-version"' in html:
        errors.append("+ Version extra button must not exist; Version box is editable")
    if 'id="setup-label-new"' in html:
        errors.append("Or type extra field must not exist; label value is editable")
    if 'class="combo"' not in html or "combo-caret" not in html:
        errors.append("Setup combo dropdown (caret + open list) missing")
    if 'id="db-tag-input"' not in html:
        errors.append("Setup tag type field missing")
    if 'id="setup-label-chips"' not in html:
        errors.append("setup-label-chips slot missing (may stay hidden)")
    if 'id="db-version-list"' in html or 'id="setup-label-value-list"' in html:
        errors.append("datalist leftover; Setup uses .combo menu not datalist")
    if 'id="run-ledger"' not in html or 'id="btn-open-central"' not in html:
        errors.append("Run ledger / Open central DB missing")
    if 'id="btn-pick-cloud-db"' not in html:
        errors.append("Setup Choose folder (#btn-pick-cloud-db) missing")
    if 'id="panel-progress-board"' not in html or 'id="first-run-modal"' not in html:
        errors.append("Lab progress board / first-run name picker missing")
    if html.find('id="results-table"') > html.find('id="panel-progress-board"'):
        errors.append("Results Last results table must come before Lab progress")
    if 'id="progress-owned"' not in html or 'id="progress-unowned"' not in html:
        errors.append("Progress board must list owned SKUs and no-PIC pickup")
    if 'id="btn-board-register"' not in html or 'id="board-who"' not in html:
        errors.append("Progress board must register person/product/package")
    if "Who's working" not in html and "Who\u2019s working" not in html:
        errors.append("Progress board must be the shared who's-working panel")
    if 'class="setup-more"' not in html:
        errors.append("Setup import/new-product must stay collapsed behind setup-more")
    setup_daily = setup_html.split('class="setup-more"', 1)[0]
    setup_more = setup_html.split('class="setup-more"', 1)[-1] if 'class="setup-more"' in setup_html else ""
    for banned, msg in (
        ('id="db-tag-input"', "Setup tags must live inside setup-more"),
        ('id="btn-import-xlsx"', "Import xlsx must live inside setup-more"),
        ('id="btn-new-product"', "Create folders must live inside setup-more"),
    ):
        if banned in setup_daily:
            errors.append(msg)
        if banned not in setup_more:
            errors.append(msg.replace("must live inside setup-more", "missing from setup-more"))
    if 'id="boot-splash"' not in html or 'id="boot-splash-msg"' not in html:
        errors.append("boot splash overlay missing")
    if "sharepoint" not in html.lower():
        errors.append("Setup central-db hint must mention SharePoint")
    if 'id="pin1-hint"' not in html:
        errors.append("pin-1 orientation hint missing")
    if 'id="psu-wiring-hint"' not in html:
        errors.append("Setup PSU wiring hint missing")
    if 'id="btn-tags-clear"' not in html:
        errors.append("Clear all tags control missing")
    if 'id="label-scope"' not in html:
        errors.append("Label scope (campaign / class / all) missing")
    if 'id="btn-save-person"' not in html or 'id="btn-forget-person"' not in html:
        errors.append("Save / Forget person controls missing")
    if 'id="person-sku-chips"' not in html or 'data-contract="person-skus"' not in html:
        errors.append("Setup product-code chips (person-skus) missing")
    if 'data-page="settings"' not in html or 'id="page-settings"' not in html:
        errors.append("Settings tab / page missing")
    if 'id="forget-phrase"' not in html or 'id="forget-wipe-folders"' not in html:
        errors.append("Settings Remove person must type FORGET {label} and optional wipe")
    if 'id="btn-save-person"' in setup_html:
        errors.append("Save person belongs on Settings, not Setup daily")
    if 'id="btn-import-family"' in setup_html:
        errors.append("Import family belongs on Settings")
    if 'id="page-users"' in html:
        errors.append("Users page chrome must stay parked")
    if 'id="btn-export-datalog"' not in html or 'id="btn-fetch-datasheet"' not in html:
        errors.append("STS datalog export / datasheet fetch controls missing")
    if 'id="btn-new-session"' in html:
        errors.append("+ Session must not exist; START stamps campaign tags")
    if 'id="walk-order"' not in html:
        errors.append("Walk order (channel vs DUT first) missing")

    js_path = WEB / "app.js"
    if not js_path.is_file():
        errors.append("app.js missing")
    else:
        js = js_path.read_text(encoding="utf-8")
        node = shutil.which("node")
        if node:
            parsed = subprocess.run(
                [node, "--check", str(js_path)],
                capture_output=True,
                text=True,
            )
            if parsed.returncode:
                errors.append(f"app.js syntax: {(parsed.stderr or parsed.stdout).strip()}")
        if re.search(r"\bif\s+![A-Za-z_]", js):
            errors.append("app.js has invalid if ! without parentheses")
        if "requireWriteOperator" not in js or "not All" not in js:
            errors.append("Create folders / DEMO / START must refuse All")
        if 'rpc("open_session", { sim: true })' not in js and 'rpc("open_session",{ sim: true })' not in js:
            if "sim: true" not in js:
                errors.append("DEMO / Open SIM must call open_session with sim: true")
        if 'rpc("ensure_version"' not in js:
            errors.append("Apply must call ensure_version for a typed Version_N")
        if "sel.operator || requireWriteOperator" in js:
            errors.append("Apply must not skip All-gate when db-operator is filled")
        apply = re.search(r"async function applyDb\(\)\s*\{[\s\S]{0,900}", js)
        if not apply or "requireWriteOperator()" not in apply.group(0):
            errors.append("applyDb must call requireWriteOperator before writes")
        if "inventoryRows" not in js or "loadInventory" not in js:
            errors.append("Setup tracking sheet must load inventory")
        if "!(inventoryRows || []).length" not in js:
            errors.append("family rail click must retry loadInventory when tracking rows are empty")
        if "hiddenOwnerRow" not in js or "alias_of" not in js:
            errors.append("Lim/SeeLim alias_of must hide the duplicate picker row")
        if re.search(r"(?m)^def ", js):
            errors.append("app.js leaked Python def")
        if "function displayPerson" not in js or "function ownerRowByName" not in js:
            errors.append("person names must fold Lim/SeeLim and ChangTong")
        if 'rpc("progress_summary"' not in js:
            errors.append("Results board must call progress_summary")
        if 'rpc("board_claim"' not in js or "claimBoardSku" not in js:
            errors.append("Progress pickup / register must call board_claim")
        if "paintUnownedSkus" not in js or "Pick up" not in html:
            errors.append("No-PIC list must have Pick up")
        if 'id="first-run-who-wrap"' not in html or 'id="first-run-products"' not in html:
            errors.append("first-run Name combo + product ticks missing")
        if 'id="first-run-new"' in html or "<select id=\"first-run-who\"" in html:
            errors.append("first-run must not use a second name field or <select> Name")
        if 'id="first-run-product-chips"' not in html:
            errors.append("first-run product chips (deselect) missing")
        if "enterFirstRunAddName" not in js or "FIRST_RUN_ADD" not in js:
            errors.append("first-run + Add Your Name lane missing")
        if "selectedFirstRunSkus" not in js or "paintFirstRunProductChips" not in js:
            errors.append("first-run must add and deselect products")
        if 'id="first-run-filter-class"' not in html or 'id="first-run-filter-pkg"' not in html:
            errors.append("first-run class/package filters missing")
        if 'id="first-run-filter-who"' not in html:
            errors.append("first-run owner/mine filter missing")
        if 'id="part-scope"' not in html or 'id="part-scope-hint"' not in html:
            errors.append("Setup Part Mine/All scope missing")
        if 'id="test-list-search"' not in html or 'id="campaign-test-search"' not in html:
            errors.append("test search boxes missing")
        if 'id="detect-search"' not in html or 'id="detect-product"' not in html:
            errors.append("wrap search / product filter missing")
        if 'id="detect-author"' not in html or 'id="snippet-edit"' not in html:
            errors.append("Tests page must filter own-code author and edit original snippet")
        if 'id="panel-ate-prompt"' not in html or 'id="btn-copy-prompt"' not in html:
            errors.append("Tests page must have Cursor prompt fill/copy")
        if 'id="panel-write-test"' not in html or 'id="btn-save-path-b"' not in html:
            errors.append("Tests page must have Path B Write test panel")
        if 'id="tests-menu-write"' not in html or 'id="tests-menu-prompt"' not in html:
            errors.append("Add/edit tests menu must jump to Write test and Cursor prompt")
        if "fillAtePrompt" not in js or "savePathBFile" not in js or "openPathBEditor" not in js:
            errors.append("Tests page must fill prompt, save Path B, and Edit source")
        if 'rpc("cursor_prompt"' not in js or 'rpc("save_path_b_test"' not in js:
            errors.append("prompt/write must rpc cursor_prompt and save_path_b_test")
        if "test-edit-source" not in js:
            errors.append("Test program row must have Edit source")
        if 'id="detect-allow-others"' not in html or 'id="btn-open-golden-bank"' not in html:
            errors.append("Tests page must gate other-people goldens and open goldens/ bank")
        if "own code" not in html.lower():
            errors.append("Tests page must say each person sees their own code")
        if "goldens/TUTORIAL.md" not in html and "TUTORIAL.md" not in html:
            errors.append("Tests page must link the golden bank tutorial")
        if "othersGoldensAllowed" not in js or "open_golden_bank" not in js:
            errors.append("Detect must send allow_others and open_golden_bank")
        if 'id="detect-family" disabled' not in html and 'id="detect-family" disabled>' not in html:
            if 'id="detect-family"' not in html or "disabled" not in html.split('id="detect-family"', 1)[-1][:80]:
                errors.append("wrap family must stay locked to this category")
        if "minePartCodes" not in js or "ingestDbTree" not in js:
            errors.append("Mine filter must use owners.yaml + PIC")
        mine_fn = js[js.find("function minePartCodes") : js.find("function skuHandledBy")]
        if "diskPartsByOperator" in mine_fn:
            errors.append("Mine must not treat empty provision folders as assigned SKUs")
        if "skuHandledBy" not in js or "partScopeIsMine" not in js:
            errors.append("Mine must expose skuHandledBy / partScopeIsMine")
        if "fillDetectProductSelect" not in js or "sameDetectFamily" not in js:
            errors.append("wrap product filter must stay in this category")
        if "applyTestListSearch" not in js or "applyCampaignTestSearch" not in js or "paintDetectedRows" not in js:
            errors.append("test / wrap search handlers missing")
        ingest_fn = js[js.find("function ingestDbTree") : js.find("function findOwnerRow")]
        if "diskPartsByOperator = byOp" not in ingest_fn:
            errors.append("ingestDbTree must snapshot disk operators before inventory merge")
        for m in re.finditer(r'rpc\("list_db_tree"\)', js):
            ctx = js[max(0, m.start() - 24) : m.end()]
            if "ingestDbTree" not in ctx:
                errors.append("list_db_tree must go through ingestDbTree so Mine is not the merged inventory")
                break
        board = re.search(r'<table id="progress-board">.*?</table>', html, re.S)
        board_html = board.group(0) if board else ""
        for col in ("Who", "Part", "Opened", "Last run", "Runs", "P/F", "Idle", "Seen"):
            if f"<th>{col}</th>" not in board_html:
                errors.append(f"progress-board must have {col} column (not owned-table Part)")
                break
        paint_board = js[js.find("async function loadProgressBoard") : js.find("function paintOwnedSkus")]
        if "hit.campaign" not in paint_board or "p.part" not in paint_board:
            errors.append("progress-board rows must paint last-run Part and heartbeat Opened")
        if "p.idle" not in paint_board:
            errors.append("progress-board rows must still paint Idle")
        casc = js[js.find("function refreshDbCascades") : js.find("function refreshDbCascades") + 1400]
        if "partScopeIsMine" not in casc or "mine.has" not in casc:
            errors.append("Part combo Mine must filter by minePartCodes")
        css_v = re.search(r"styles\.css\?v=([^\"\s]+)", html)
        js_v = re.search(r"app\.js\?v=([^\"\s]+)", html)
        if not css_v or not js_v or css_v.group(1) != js_v.group(1):
            errors.append("index.html styles.css and app.js cache bust must match")
        fill_fam = js[js.find("function fillDetectFamilySelect") : js.find("function closeTestsMenu")]
        if "el.disabled = true" not in fill_fam:
            errors.append("wrap family select must stay disabled in JS")
        fr_prod = js[js.find("function paintFirstRunProducts") : js.find("function paintFirstRunProductChips")]
        if '"PIC "' not in fr_prod and "'PIC '" not in fr_prod:
            errors.append("first-run ticks must show PIC label")
        if 'id="first-run-detect"' not in html or "paintFirstRunDetect" not in js:
            errors.append("first-run detect (tracking vs disk) missing")
        if "firstRunOwnerKnown" not in js or "firstRunPicked" not in js:
            errors.append("first-run must absorb typed name and keep SKU ticks across filters")
        enter_add = js[js.find("function enterFirstRunAddName") : js.find("function exitFirstRunAddName")]
        if "who.value = absorb" in enter_add or 'who.value = ""' in enter_add:
            errors.append("enterFirstRunAddName must not wipe a typed name")
        add_first = js[js.find("async function completeFirstRun") : js.find("let heartTimer")]
        if 'rpc("provision_operator"' not in add_first:
            errors.append("first-run Continue must provision ticked SKUs")
        if "tick at least one product" in add_first:
            errors.append("first-run name-only must be allowed (Pick up on Results)")
        if "firstRunOwnerKnown(typed)" not in add_first:
            errors.append("first-run Continue must upsert an unknown typed name")
        if 'rpc("list_campaign_tests"' not in js or 'rpc("set_campaign_enabled_tests"' not in js:
            errors.append("Tests page must call list_campaign_tests / set_campaign_enabled_tests")
        if "btn-copy-tests" in js or "detect-copy-from" in js:
            errors.append("Copy tests between parts UI must stay parked")
        if 'rpc("assign_owner_products"' not in js:
            errors.append("Save person must call assign_owner_products")
        if 'rpc("provision_operator"' not in js:
            errors.append("Add person / All SKUs + golden must call provision_operator")
        if "unassignPersonSku" not in js or "paintPersonSkuChips" not in js:
            errors.append("Setup person-sku unassign / chips handlers missing")
        if 'id="results-sts-status"' not in html:
            errors.append("Results must show STS status Total/Pass/Fail")
        if "results-sts-status" not in js or "Complete:" not in js:
            errors.append("DEMO/START must paint complete Total/Pass/Fail after the run")
        if "hideBootSplash" not in js or 'rpc("sync_repo")' not in js:
            errors.append("boot splash must sync_repo then hide")
        if "paintPsuWiring" not in js or "2.5 V" not in js:
            errors.append("paintPsuWiring must say OpAmp 2.5 V not 5 V on CH1")
        if "pingOk" not in js or "Worker up, load failed" not in js:
            errors.append("boot must separate ping-fail from campaign-load fail")
        if "visa_backend" not in js:
            errors.append("session hint must show visa_backend")
        if "not on bus" not in js or "USBTMC Unknown" not in js:
            errors.append("session hint must name missing AWG (PnP Unknown / not on bus)")
        if "No USB instruments" not in js:
            errors.append("Discover empty must notice so USB recording is not a silent {}")
        if "function notice(" not in js:
            errors.append("operator notices must use in-app #notice-banner")
        if "applyProbeChannels" not in js or "probe_channels" not in js:
            errors.append("Setup must apply probe_channels then let operator add/tick channels")
        if "btn-add-channel" not in js or "paintWalkOrderLabels" not in js:
            errors.append("Probe channels must scale with + / x and walk-order labels")
        if 'id="btn-add-operator"' not in html or 'id="add-operator-modal"' not in html:
            errors.append("Add person confirm popup missing")
        if "openAddOperatorModal" not in js or "confirmAddOperator" not in js:
            errors.append("Add person must confirm then upsert_owner")
        if "applyComboPick" in js and 'input.id === "db-operator"' not in js[js.find("function applyComboPick"):js.find("function removeComboOption")]:
            errors.append("Operator combo Add <name> must open add-person modal")
        if "operators.includes(sel.operator)" not in js:
            errors.append("Typed new Operator folder must not snap back to Ariff/disk")
        if 'id="add-operator-products"' not in html:
            errors.append("Add person popup must tick tracking-sheet products")
        if 'id="add-operator-all-skus"' not in html:
            errors.append("Add person must offer all tracking SKUs + golden checkbox")
        if 'id="add-operator-all-skus" checked' in html:
            errors.append("Add person must not default All SKUs (dump)")
        if 'add-operator-all-skus")).checked = true' in js:
            errors.append("Add person JS must not re-check All SKUs")
        if "provisionPersonFromSetup" not in js or 'id="btn-provision-person"' not in html:
            errors.append("More must have All SKUs + golden for the current person")
        add_fn = js[js.find("async function confirmAddOperator") : js.find("async function applyDb")]
        if "personSkuCodes" in add_fn:
            errors.append("Add person Create folders must use popup ticks, not More-panel SKU chips")
        if 'rpc("provision_operator"' not in add_fn:
            errors.append("Add person Create folders must call provision_operator")
        if "selectedAddOperatorSkus" not in js or "paintAddOperatorProducts" not in js:
            errors.append("Add person must paint tracking SKUs and read ticks")
        if 'id="notice-banner"' not in html or 'id="channel-hint"' not in html:
            errors.append("notice banner / channel hint missing")
        disc = js[js.find("$(\"btn-discover\")") : js.find("$(\"btn-open\")")]
        if disc and "notice(" not in disc:
            errors.append("Discover empty must call notice, not window.alert")
        if disc and "setTiles(st.mapping" in disc:
            errors.append("empty Discover must not restore SIM tiles as USB-detected")
        if "tileMapFromStatus" not in js or "st.pnp" not in js:
            errors.append("header tiles must light PnP-OK USB (connected AWG)")
        if 'source.kind === "wrap"' not in js:
            errors.append("Test program must hide leftover wrap src on ate/tests bodies")
        if "stimPrefix" not in js or "testNeedsAwg" not in js:
            errors.append("IOZ must not badge AWG DC when required_instruments has no AWG")
        refresh = js[js.find("async function refreshSession") : js.find("const familyRail")]
        if "tileMapFromStatus" not in refresh:
            errors.append("refreshSession must not wipe Discover/PnP tiles with empty mapping")
        if 'const need = ["MSO", "PSU", "AWG"]' in js:
            errors.append("Open Session must not require all of MSO+PSU+AWG")
        if 'rpc("bench_preflight"' not in js:
            errors.append("DEMO must call bench_preflight before SIM (USB vs fake SCPI)")
        if "waitForRunComplete(epoch0)" not in js and "run_epoch" not in js:
            errors.append("DEMO/START must wait for run_epoch so Building plan cannot miss the run")
        if "Worker restarted during run" not in js:
            errors.append("waitForRunComplete must drop stale poll after worker restart")
        if "MSO stays 2 probes" not in js:
            errors.append("Parameters must say 2^n is AWG corners, MSO stays 2 probes")
        if "let ids = selectedTests();" not in js:
            errors.append("DEMO must auto-select campaign tests when none are checked")
        if 'querySelectorAll(".test-item input:checked")' in js:
            errors.append("selectedTests must read #test-list only (Tests page duplicates START)")
        if 'part: (dbContext && dbContext.part_key) || "rs622"' in js:
            errors.append("DEMO/START must not default part to rs622")
        if 'rpc("fill_workbook"' not in js:
            errors.append("run complete must auto-fill Excel numbers")
        if "res.copilot" not in js:
            errors.append("Fetch datasheet must log ingest status")
        if "stimulus" not in js or "AWG " not in js:
            errors.append("Test list must show AWG stimulus shape")
        if "sim_bus" not in js:
            errors.append("SIM session hint must show last AWG/PSU sim_bus")
        if "autoContinue: true" not in js and "auto_continue: true" not in js:
            errors.append("DEMO must pass auto_continue so START does not inherit SIM skip")
        if "SIM session is still open" not in js:
            errors.append("START must refuse leftover SIM when USB is live")
        if 'classList.toggle("sim"' not in js:
            errors.append("SIM tiles must use .tile.sim so they do not look like USB")
        if "btn-new-session" in js:
            errors.append("+ Session handler must not exist")
        if "walk_order" not in js or 'rpc("set_run_prefs"' not in js:
            errors.append("Walk order must send walk_order and set_run_prefs")
        if 'id="modal-later"' not in html or 'id="run-strip"' not in html:
            errors.append("Continue popup Later / live run-strip missing")
        if 'id="run-continue"' not in html or 'id="run-strip-continue"' not in html:
            errors.append("Run page / strip Continue missing")
        if "dismissOperatorModal" not in js or "gateHeld" not in js:
            errors.append("Later must hide Continue without aborting")
        if "autoOpen: !gateHeld" not in js:
            errors.append("poll must not auto-reopen a held Continue popup")
        sync_fn = js[js.find("async function syncRunState") : js.find("async function syncRunState") + 700]
        if "if (pendingPrompt)" not in sync_fn or 'setRunPill("wait")' not in sync_fn:
            errors.append("WAIT pill must win over busy RUNNING (no shake on Continue)")
        if 'kind !== "dut_change"' not in js:
            errors.append("step bar must hide dut_change (duplicate CHA wording)")
        if 'el.type === "checkbox"' not in js:
            errors.append("collectOneTestParams must read checkbox (voh_100ua select/deselect)")
        if "voh_100ua" not in js or "Include 100 uA" not in js:
            errors.append("VOH/VOL Parameters must expose Include 100 uA checkbox")
        if 'id="dut-count"' not in html:
            errors.append("Setup DUT count input missing")
        if "Select tests — standard defaults apply." not in html:
            errors.append("empty test ticks must say standard defaults apply")
        if 'id="panel-run-conditions"' in html or 'id="run-conditions"' in html:
            errors.append("shared Run conditions VCC bar must stay removed")
        if 'id="sweep-panel"' in html or 'id="vcc-start"' in html:
            errors.append("global sweep panel must stay removed; params live on each Test program row")
        if "test-spec-edit" not in js or "test-param-write" not in js:
            errors.append("each Test program row must have Parameters editor + Write")
        load_tests = js[js.find("async function loadTests") : js.find("async function refreshSession")]
        if "wrap.open = true" not in load_tests:
            errors.append("Test program fixture groups must open so per-test Parameters are visible")
        if "<details class=\"test-spec-edit\">" not in js and "<details class='test-spec-edit'>" not in js:
            errors.append("per-test Parameters must be collapsed details (click to expand)")
        if "<details class=\"test-spec-edit\" open" in js or "<details class='test-spec-edit' open" in js:
            errors.append("per-test Parameters must default closed")
        if "clickStartOrContinue" not in js or "campaignAlreadyApplied" not in js:
            errors.append("START must Continue when WAIT and skip applyDb when campaign already applied")
        if "no Apply reload" not in js:
            errors.append("START must pin campaign without applyDb reload (Failed to fetch)")
        if "/fetch|network|Failed/" not in js:
            errors.append("rpc must retry once on Failed to fetch")
        params_fn = js[js.find("function params()") : js.find("function currentPartKey")]
        if "operator: sel.operator" not in params_fn or "component: sel.component" not in params_fn:
            errors.append("START params must pin Setup component/operator folder")
        if "Stimulus AWG" not in load_tests and "Stimulus AWG" not in js:
            errors.append("each test editor must show stimulus AWG shape")
        if "Limits / specifications" not in js:
            errors.append("each test editor must show limits min/max for this Version")
        if 'paramNumInput("vin_step"' not in js:
            errors.append("Parameters must expose VIN trip step (0.01 / 0.001)")
        if 'paramNumInput("vcc_step", "VCC step (V)"' not in js or "0.01" not in js[js.find('paramNumInput("vcc_step"') : js.find('paramNumInput("vcc_step"') + 120]:
            errors.append("VCC step input must allow 0.01")
        if 'paramNumInput("ioz_vout_step"' not in js:
            errors.append("IOZ Parameters must expose Vout step 0.1 (See Lin 0..5.5)")
        paint_c = js[js.find("function paintCampaign") : js.find("function currentDbSelection")]
        if "syncOwnerSelectFromFolder(sel.operator)" not in paint_c:
            errors.append("changing Operator folder must sync the header person")
        apply_db = js[js.find("async function applyDb") : js.find("function fillDetectFamilySelect")]
        if "st.busy" not in apply_db and "runPollActive" not in apply_db:
            errors.append("Apply campaign must skip set_db_context while a run is busy")
        if 'rpc("set_test_params"' not in js:
            errors.append("Write must rpc set_test_params")
        write_fn = js[js.find("async function writeTestParams") : js.find("function sweepValues")]
        if "currentDbSelection" not in write_fn or "component:" not in write_fn:
            errors.append("Write must pin Setup campaign so leftover worker context cannot steal the yaml")
        srv = (WEB.parents[1] / "worker" / "server.py").read_text(encoding="utf-8")
        if "busy_locked" not in srv:
            errors.append("set_db_context must busy_locked so AnalogSwitch cannot steal a Logic run")
        if "_pin_run_campaign" not in srv:
            errors.append("run_sequence_async must pin START campaign after claim")
        if "_session_bound_ctx" not in srv:
            errors.append("Excel/STS export must bind the START campaign folder")
        if 'method == "cursor_prompt"' not in srv or 'method == "save_path_b_test"' not in srv:
            errors.append("worker must expose cursor_prompt and save_path_b_test")
        if "coerce_screenshot_from" not in srv:
            errors.append("list_tests must coerce screenshot_from from TestSpec instruments")
        set_tp = srv[srv.find('if method == "set_test_params"') : srv.find('if method == "import_tags"')]
        if "set_context" not in set_tp:
            errors.append("set_test_params must pin campaign from payload before save")
        if "overlay_for" not in (WEB.parents[1] / "core" / "runner.py").read_text(encoding="utf-8"):
            errors.append("runner RunParams.overlay_for must apply per-test params")
        if "vcc_start" not in js or "sweepValues" not in js:
            errors.append("START params must still send vcc_start/stop/step fallback")
        if 'data-param="vcc_list"' not in js or 'data-param="logic_inputs"' not in js:
            errors.append("Parameters must expose vcc_list and logic_inputs (PRD-004 recipe)")
        if 'data-param="rails_mode"' not in js or 'data-param="rails_psu"' not in js:
            errors.append("Parameters must expose rails single/dual + PSU CH volts")
        for timing_key in ("settle_s", "timeout_s", "dwell_s"):
            if f'paramNumInput("{timing_key}"' not in js:
                errors.append(f"Parameters must expose recipe timing {timing_key}")
        if 'data-param="screenshot_from"' not in js:
            errors.append("Parameters must expose screenshot_from (none | MSO | DMM)")
        if 'option value="dmm"' not in js:
            errors.append("screenshot_from must include DMM when the TestSpec needs DMM")
        if 'option value="none"' not in js:
            errors.append("screenshot_from must include none so DMM shot can be disabled")
        if 'needsDmm && !needsMso ? "dmm"' not in js:
            errors.append("DMM-only tests must default screenshot_from=dmm, never MSO")
        if "!needsMso && needsDmm" not in js:
            errors.append("stale screenshot_from=mso on DMM-only tests must coerce to dmm")
        if 'paramNumInput("dmm_avg_n"' not in js or 'paramNumInput("dmm_nplc"' not in js:
            errors.append("Parameters must expose DMM avg N + NPLC host wait (no SCPI NPLC)")
        if "campaignTestOrderIds" not in js or "initCampaignTestReorder" not in js:
            errors.append("Path A customize must HTML5-reorder enabled_tests (not A14 xyflow)")
        if "campaign-drag-handle" not in js:
            errors.append("campaign-tests drag handle missing")
        if 'id="page-recipe"' not in html or 'data-page="recipe"' not in html:
            errors.append("Recipe tab #page-recipe missing (A14)")
        if 'id="recipe-root"' not in html:
            errors.append("#recipe-root canvas mount missing (A14)")
        if "canvas/recipe-canvas.js" not in html:
            errors.append("index.html must load canvas/recipe-canvas.js")
        if not (WEB / "canvas" / "recipe-canvas.js").is_file():
            errors.append("committed canvas dist recipe-canvas.js missing")
        if 'id="progress-who-tests"' not in html:
            errors.append("Results who-has-what table #progress-who-tests missing")
        if "who_tests" not in js:
            errors.append("loadProgressBoard must paint who_tests rows")
        runner = (WEB.parents[1] / "core" / "runner.py").read_text(encoding="utf-8")
        if "vcc_list" not in runner or "if self.vcc_list" not in runner:
            errors.append("RunParams.resolved_vcc_sweep must honor vcc_list")
        if "freq_start" not in js:
            errors.append("START params must send freq_start/stop/step from the test row")
        if "diskOps.concat(yamlOps)" in js or "yamlOps" in js:
            errors.append("Operator folder list must not dump owners.yaml (Kevin/ATE)")
        if "hiddenOperatorName" not in js:
            errors.append("Kevin / ATE must be hidden from campaign operator lists")
        if 'id="btn-plus-operator"' not in html or 'id="btn-plus-package"' not in html:
            errors.append("Package / Operator combos need + plus buttons")
        if 'id="campaign-plus-modal"' not in html or "openCampaignPlus" not in js:
            errors.append("plus must open pick-existing or add-new panel")
        if 'rpc("ensure_product"' not in js[js.find("async function confirmCampaignPlus") : js.find("function addSkuKey")]:
            errors.append("plus existing operator/package must ensure_product this SKU")
        if "persistRunPrefs" not in js or "sample_size" not in js:
            errors.append("DUT count / channels must save via persistRunPrefs sample_size")
        if "cb.disabled = !ok" in js:
            errors.append("Channel B must stay tickable, not yaml-locked")
        if "from a senior" not in html:
            errors.append("Setup import must note lab report from a senior")
        if "AI agent" not in html:
            errors.append("Setup import must note AI agent can annotate paste cells")
        if "narrative=" not in js:
            errors.append("Fill Excel must log narrative counts")
        combo = re.search(
            r'\["db-component", "db-part", "db-package", "db-operator", "db-version"\]\.forEach[\s\S]*?\$\("btn-apply-db"\)',
            js,
        )
        if not combo:
            errors.append("Setup campaign combo change listener missing")
        elif "applyDb(" in combo.group(0):
            errors.append("Setup combo change must not auto applyDb")
        apply_owner = js[js.find("async function applyOwner") : js.find("function writeOperatorLabel")]
        if "operatorFromPic" in apply_owner or "picFolder" in apply_owner:
            errors.append("applyOwner must use this person folder, not inventory pic")
        load_db = js[js.find("async function loadDb") : js.find("let campaignTags")]
        if "campaignForThisPc(saved, ctx)" not in load_db:
            errors.append("loadDb must restore this PC ate_operator, not worker last-apply")
        if "ate_last_campaign_by_owner" not in js:
            errors.append("last campaign must be per-person on this PC")
        if 'rpc("pick_cloud_db"' not in js or "refreshCloudDbHint" not in js:
            errors.append("Setup must pick #Test_Database folder and refresh the central-db hint")
        if 'rpc("cloud_db_status"' not in js:
            errors.append("boot must call cloud_db_status when the folder is missing")
        boot = js[js.find("(async function boot()") :]
        own_i = boot.find("await loadOwners()")
        db_i = boot.find("await loadDb()")
        if own_i < 0 or db_i < 0 or own_i > db_i:
            errors.append("boot must loadOwners before loadDb so this PC person wins")
        from_inv = js[js.find("function campaignFromInventory") : js.find("function versionsForSel")]
        if "writeOperatorLabel()" not in from_inv or from_inv.find("writeOperatorLabel()") > from_inv.find(
            "operatorFromPic"
        ):
            errors.append("family rail campaign must prefer this PC person over inventory pic")
        forget_fn = js[js.find("$(\"btn-forget-person\")") : js.find("function paintSettingsPcHint")]
        if "confirm_text" not in forget_fn or "delete_folders" not in forget_fn:
            errors.append("Forget click must send confirm_text and delete_folders")

    if errors:
        print("FAIL check_ui_contract:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK check_ui_contract tabs={tabs} fonts={families}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
