# Test design guide -- wrap goldens into the console

**Live console is not this file.** New tests, people, and campaigns go through `ate/tests/<family>/` using the three paths in [docs/VIBE_CODE.md](docs/VIBE_CODE.md) (A customize this Version, B realize TestSpec, C wrap then fill). Map: [AGENTS.md](AGENTS.md).

What follows is the **legacy** `main.py` dual-stack. Treat `opa_tests.py` / `logic_tests.py` as **golden source** you may wrap (Path C). Editing `main.py` to add a test will not show up on UI **5174**.

**Wrap this golden into the console**

1. Confirm the `def test_*` body does not call `input()` (rewrite to `params.pause_hook` first).
2. Tests page **Wrap + enable on this Version** -> `ate/tests/<family>/imported_<id>.py` scaffold.
3. Fill `run()` + `measurements` (Path B). Idle-restart worker.
4. Add limits + optional `sheet_map`. DEMO that id.

Do not grow `TEST_SPECS` in root `limits.py` for the console. Console limits are `ate/config/limits/<key>.yaml`.


---

## 1. Mental model

| Layer | Files | You do |
|-------|-------|--------|
| Entry & sequence | `main.py` | Call your `test_*` inside the `VCC_LIST` loop (ask Eugene) |
| Global knobs | `configurations.py` | `VCC_LIST`, `current_limit`, `EXCEL_FILE` (ask Eugene) |
| Pass/fail specs | `limits.py` | Add parameter to `TEST_SPECS` / `TEST_CATEGORIES` (ask Eugene) |
| Your procedure | `opa_tests.py` / `logic_tests.py` / … | **Write the test here** |
| SCPI helpers | `*_setup.py` | Reuse; add a small helper only if missing |
| Sessions | `instruments.py` | Open/discover; enable DMM only when needed |
| Logging | `datalog.py` | Call `logger.log_test(name, value, duration_ms=…)` |

**Contract for every test function:**

```text
def test_something(instr, vcc, logger=None) -> dict | None:
    # 1) power / stimulus / measure / log
    # 2) clean local outputs if needed
    # 3) return a small results dict (optional but useful)
```

`instr` always exposes at least: `.scope`, `.psu`, `.gen` (and `.dmm` only if enabled).

---

## 2. Where to change what (cheat sheet)

| Goal | Edit |
|------|------|
| Run a different OPA/logic test | `main.py` — uncomment/append `results.append(test_…(instr, vcc, logger))` |
| Sweep supply corners | `configurations.py` → `VCC_LIST = [3.3, 5]` |
| Change current limit / OVP default usage | `configurations.py` → `current_limit`; call site uses `power_on_protected(...)` |
| Log a new parameter name | `limits.py` → `TEST_SPECS` **and** usually `TEST_CATEGORIES` |
| Implement measure / SCPI sequence | Your `*_tests.py` |
| New waveform helper | `generator_setup.py` |
| New PSU helper | `psu_setup.py` |
| New scope measure wrapper | `scope_setup.py` |
| New DMM mode | `dmm_setup.py` |
| Enable Keithley DMM session | `instruments.py` (uncomment IDN + `self.dmm = self._open("DMM")` + include in reset/close) |
| Datalog Excel name / user tag | `DataLogger(..., test_name=..., user_id=...)` in `main.py` |
| Docs-only list of planned params | `test_parameter()` at top of your `*_tests.py` (metadata; does **not** run tests) |

---

## 3. Canonical test anatomy (copy this pattern)

Good reference implementations:

- **OPA AC / dual-rail:** `test_opa_gbw` / `measure_gbw` in `opa_tests.py`
- **Logic timing:** `test_tp` in `logic_tests.py`
- **Logic DC voltage:** `test_output_voltage` in `logic_tests.py` (DMM pattern)

### Template

```python
def test_my_param(instr, vcc, logger=None):
    """One-line purpose. Units for logged values called out here."""
    psu = instr.psu
    gen = instr.gen
    scope = instr.scope
    # dmm = instr.dmm   # only if DMM enabled

    initial_time()

    # --- SETUP ---
    # OPA dual-rail style:
    power_on_protected(psu, 1, vcc / 2, current_limit)
    power_on_protected(psu, 2, vcc / 2, current_limit)
    # Logic single-rail style:
    # power_on_protected(psu, 1, vcc, current_limit)

    setup_sine(gen, 1, 1000, 0.05, 0)   # or setup_square / set_offset / ...
    enable_output(gen, 1)
    scope_setup(scope, 1e-3, 0.0)       # skip AUToscale-heavy paths for pure DC

    # --- MEASURE ---
    time.sleep(0.5)                     # settle
    value = ...                         # scope query or dmm_read_avg

    duration = final_time()

    # --- LOG (name MUST exist in limits.TEST_SPECS) ---
    if logger:
        logger.log_test("IN+", vcc, duration_ms=duration)
        logger.log_test("MyParam", value, duration_ms=duration)

    # --- LOCAL CLEANUP (global cleanup still runs in main.finally) ---
    stop_output(gen)
    power_off(psu)

    return {"IN+": vcc, "MyParam": value}
```

### Wire it in `main.py`

```python
for vcc in VCC_LIST:
    results.append(test_my_param(instr, vcc, logger))
```

---

## 4. Instrument API quick reference

### PSU — `psu_setup.py` (DP832)

| Call | Meaning |
|------|---------|
| `power_on_protected(psu, ch, voltage, current_limit, ovp=None, ocp=None)` | Set V/I, enable OVP/OCP, then ON |
| `power_on(psu, ch, voltage)` | Simple V then ON |
| `power_off(psu)` | CH1–CH3 OFF |

OPA tests typically use **CH1 + CH2 at `vcc/2`**. Logic often uses **CH1 at `vcc`**.

### AWG — `generator_setup.py` (DG8xx)

| Call | Meaning |
|------|---------|
| `setup_sine(gen, ch, freq, vpp, offset, phase=0)` | Sine + output ON |
| `setup_square(gen, ch, freq, vpp, offset, duty=50)` | Square + duty |
| `setup_pulse` / `setup_ramp` / `setup_noise` / `apply_waveform` | Other shapes |
| `set_frequency` / `set_amplitude` / `set_offset` | Change live params |
| `enable_output` / `disable_output` / `stop_output` | Output control |

**Important:** AWG `offset` is **waveform DC offset**, not opamp \(V_{OS}\).

### Scope — `scope_setup.py` (MSO5)

| Call | Meaning |
|------|---------|
| `scope_setup(scope, time_scale, trig_level)` | Often includes `:AUToscale` — bad for absolute DC |
| `set_threshold(scope, ch)` | Measure thresholds 80/20/50 |
| `measure_single(scope, item, ch)` | Statistic average of an item |
| `measure_delay(scope, item, ch1, ch2)` | Two-channel delay |
| Direct `scope.query(":MEAS:ITEM? VAMP,CHAN2")` | Also used in OPA code |

### DMM — `dmm_setup.py` (when session exists)

| Call | Meaning |
|------|---------|
| `dmm_setup_voltage(dmm)` | DC volts + autorange |
| `dmm_read(dmm)` / `dmm_read_avg(dmm, n=5)` | Single / averaged `:READ?` |
| `dmm_setup_current` / `dmm_setup_cap` | Other modes |

### Sessions — `instruments.py`

| Call | Meaning |
|------|---------|
| `Instruments()` | Discover + open |
| `instr.reset_all()` | `*RST` |
| `instr.close_all()` | Close VISA |

Default open timeout: **3000 ms**.

---

## 5. Tutorial A — Add a functional AC-style OPA test (existing pattern)

Example goal: run settling time (already in repo).

1. Implement `test_settlingTime(instr, vcc, logger=None)` in `opa_tests.py`.
2. Ask Eugene to enable in `main.py`:

   ```python
   results.append(test_settlingTime(instr, vcc, logger))
   ```

3. If you `log_test("Settling_us", value)`, add to `limits.py` first:

   ```python
   TEST_SPECS = {
       'IN+': (2, 5.0),
       'Settling_us': (100.0, 20.0),  # nominal, ±%
   }
   TEST_CATEGORIES = {
       ...
       'Settling_us': 'ac',
   }
   ```

4. Run: `.\venv\Scripts\python.exe main.py`
5. Confirm Excel datalog and PASS/FAIL windows.

Debug SCPI noise in OPA module:

```powershell
$env:OPA_DEBUG="1"
.\venv\Scripts\python.exe main.py
```

---

## 6. Tutorial B — Design a **Voffset** (\(V_{OS}\)) test (not in repo yet)

### Physics (pick one method)

| Method | Idea | Fit for this bench |
|--------|------|--------------------|
| Closed-loop | Ground/short inputs, \(V_{OS} = V_{OUT}/A_{CL}\) | Best start — DMM + known gain |
| Null / binary search | Step Vin until Vout ≈ 0 | Reuse GBW binary-search style |
| Full DC sweep | Step Vin, record Vout, fit intercept | Characterization tables |

### Checklist

1. **Hardware:** known closed-loop gain \(G\) (GBW code often assumes ~11), sense node for DMM, rails as in other OPA tests.
2. **Enable DMM** in `instruments.py` (uncomment detection + `self.dmm`; add to `reset_all` / `close_all`).
3. **Specs** in `limits.py`, e.g. `'Voffset_mV': (1.0, 500.0)` (percent-of-nominal model — pick a non-zero nominal; discuss with Eugene if you need absolute limits).
4. **Function** in `opa_tests.py`:

```python
def test_opa_voffset(instr, vcc, logger=None, gain=11.0):
    psu, dmm, gen = instr.psu, instr.dmm, instr.gen
    initial_time()

    power_on_protected(psu, 1, vcc / 2, current_limit)
    power_on_protected(psu, 2, vcc / 2, current_limit)
    time.sleep(1)

    stop_output(gen)   # or apply known DC 0 if the fixture needs the AWG tied in

    dmm_setup_voltage(dmm)
    time.sleep(0.5)
    vout = dmm_read_avg(dmm, n=5)
    vos_mV = (vout / gain) * 1e3

    duration = final_time()
    if logger:
        logger.log_test("IN+", vcc, duration_ms=duration)
        logger.log_test("Voffset_mV", vos_mV, duration_ms=duration)

    power_off(psu)
    return {"IN+": vcc, "Voffset_mV": vos_mV}
```

5. Register call in `main.py` (with Eugene).
6. Do **not** use `scope_setup`’s autoscale path for this measurement.

---

## 7. Tutorial C — Design a **DC sweep**

There is **no** built-in sweep helper. Use a Python loop:

```python
def dc_sweep_vin(instr, vcc, vin_list, settle_s=0.3, gain=11.0):
    psu, gen, dmm = instr.psu, instr.gen, instr.dmm

    power_on_protected(psu, 1, vcc / 2, current_limit)
    power_on_protected(psu, 2, vcc / 2, current_limit)
    dmm_setup_voltage(dmm)

    rows = []
    for vin in vin_list:
        set_offset(gen, 1, vin)
        enable_output(gen, 1)
        time.sleep(settle_s)
        vout = dmm_read_avg(dmm, n=5)
        rows.append({"vin": vin, "vout": vout, "vos_est": vout / gain})

    stop_output(gen)
    power_off(psu)
    return rows
```

Optional improvements matching this codebase:

- Add `setup_dc(gen, ch, volts)` in `generator_setup.py` if you prefer `:APPL:DC` over sine+offset.
- Save sweep rows to a separate CSV with pandas (do not force every point through `TEST_SPECS` unless you want one log line per step).
- Reuse the **binary search** pattern from `measure_gbw` if you only need the Vin null, not a full table.

Suggested settle times: **0.2–1.0 s** depending on filtering/thermal. Prefer `dmm_read_avg` over single reads.

---

## 8. Logging rules (read before first `log_test`)

```python
logger.log_test(parameter, result, duration_ms=duration)
```

- `parameter` **must** be a key in `limits.TEST_SPECS` or you get `ValueError`.
- Pass window = `nominal ± (nominal * tolerance_percent / 100)`.
- Soft bin: `1` PASS, `2` functional fail, `3` AC fail (`TEST_CATEGORIES`).
- `test_parameter()` arrays in `*_tests.py` are **documentation for planned columns**; they do not schedule runs or auto-log.

---

## 9. Design checklist (print before PR)

- [ ] Test lives in the correct owned `*_tests.py`
- [ ] Signature is `(instr, vcc, logger=None)`
- [ ] Uses `power_on_protected` with `current_limit` from `configurations`
- [ ] Settling `time.sleep` after power / stimulus change
- [ ] Every logged name exists in `limits.TEST_SPECS`
- [ ] Local `stop_output` / `power_off` when leaving rails noisy
- [ ] `main.py` call approved if you do not own that file
- [ ] No hardcoded VISA resource strings (use `instr.*`)
- [ ] Avoid `:AUToscale` for absolute DC / Vos
- [ ] Verified one live run and inspected Excel datalog

---

## 10. References

### In-repo examples

| Pattern | File / symbol |
|---------|----------------|
| Dual-rail + sine + scope search | `opa_tests.measure_gbw` |
| Dual-rail + square + slew | `opa_tests.measure_sr` |
| Single-rail + delay measure | `logic_tests.test_tp` |
| DMM DC read pattern | `logic_tests.test_output_voltage` |
| Session lifecycle | `main.main` + `instruments.Instruments` |

### External

- [PyVISA](https://pyvisa.readthedocs.io/) — `ResourceManager`, `open_resource`, timeouts  
- Rigol programming manuals for **DP832**, **DG800**, **MSO5000** (SCPI command reference)  
- Vendor app notes: *op-amp input offset voltage measurement* / *nulling amplifier* (TI, ADI, Renesas)  

---

*When in doubt: keep SCPI in `*_setup.py`, keep product logic in your `*_tests.py`, ask Eugene for `main` / `limits` / `configurations`.*
