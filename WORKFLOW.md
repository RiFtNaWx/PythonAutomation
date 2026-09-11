---

# PythonAutomation — Team Workflow

## What this is
A shared Python codebase for lab hardware test automation.
Each engineer owns their own module file.
All changes go through a Pull Request reviewed by Eugene (RiFtNaWx).

**Also read:**
- [AGENTS.md](AGENTS.md) -- operator console: add user / version / test without breaking the tree
- [README.md](README.md) -- console quick start (not `main.py` first)
- [TEST_DESIGN.md](TEST_DESIGN.md) -- legacy `main.py` test anatomy (wrap into `ate/tests/` for the UI)
- [PYVISA_OPA_DEEP_DIVE.md](PYVISA_OPA_DEEP_DIVE.md) -- precise PyVISA layer + OPA deep dive (architecture, SCPI APIs, pitfalls)

---

## First time setup — do this once on a new machine

**Step 1 — Install Python 3.11**
Download from https://www.python.org/downloads/
On Windows: tick **Add Python to PATH** during install.

**Step 2 — Install Git**
Download from https://git-scm.com/downloads
During install choose: *Git from the command line and also from 3rd-party software*

Set your identity — open any terminal and run:
```
git config --global user.name "Your Full Name"
git config --global user.email "your@email.com"
```

**Step 3 — Clone the repo (console branch)**
```
git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git
cd PythonAutomation
```

Default `main` on this GitHub is the older lab tree. Day-to-day console work is `eugene-console`. Opening the folder in Cursor/VS Code (or `run_ate_app.bat`) runs `python -m ate.core.sync_repo`: fetch + fast-forward only, skipped if you have uncommitted files. It will not `reset --hard` your edits.

**Step 4 — Run the installer**
```
python install.py
```
This creates the virtual environment, installs all packages,
registers the push command, and launches the push button.
Run this only once per machine.

**Step 5 — Get env.local from team lead**
Ask Eugene for the env.local file.
Place it inside the Github_Auto/ folder.
Never share this file or commit it to GitHub.

**Step 6 — Reopen your terminal**
Close the current terminal and open a new one.
This activates the PATH change so the push command works.

Setup is complete. Never repeat these steps on the same machine.

---

## Daily workflow — pushing your changes

When you finish editing and want to share your work, use any one method:

**Method 1 — Terminal command**
```
push
```
Type this from anywhere inside the repo folder.

**Method 2 — Floating button**
Click the green circle button on your screen.
If it is not visible, type:
```
.\push_button
```

**Method 3 — VS Code**
Terminal menu → Run Task → Push to GitHub

---

## What happens when you push

1. Script checks what you changed vs the main branch
2. SEA-LION AI generates a short title and description (about 20 seconds)
3. A popup shows the AI suggestion — read it, edit if needed
4. Click **Push now**
5. A Pull Request is created on GitHub automatically
6. Eugene reviews and merges

If nothing changed since your last push, the script says
*"Everything is already up to date"* and closes. Nothing is sent.

If AI is unavailable, the popup opens with a blank description.
Type what you changed, click Push now. Works the same.

---

## Before you close for the day

When you click × on the green push button, if you have
unpushed changes it will ask:
*"You have unpushed changes. Push before you go?"*

Click **Push now** to send your work, or **Skip** to close without pushing.

---

## Module ownership

| File | Owner |
|------|-------|
| opa_tests.py | OPA engineer |
| level_shifter_tests.py | Level shifter engineer |
| ldo_tests.py | LDO engineer |
| logic_tests.py | Logic engineer |
| configurations.py, limits.py | Eugene (team lead) |
| main.py | Eugene (team lead) |
| Github_Auto/ | Do not edit unless adding features |

Instrument helpers (`instruments.py`, `*_setup.py`, `datalog.py`, `utils.py`) are shared — coordinate before large refactors.

---

## Where to change code (short map)

Operator console (people, versions, families, START): **[AGENTS.md](AGENTS.md)**. Do not add a user or a product by editing `main.py`.

| Need | File | Notes |
|------|------|--------|
| New person / version / campaign | `ate/config/owners.yaml` + Setup | See AGENTS.md |
| New console test | `ate/tests/<family>/` `register(TestSpec)` | Restart worker |
| Legacy one-shot / golden body | Your root `*_tests.py` | Wrap into ate/ for the UI |
| Enable a test in legacy `main.py` | `main.py` | Ask Eugene; does not feed the console |
| Change VCC corners / current limit (legacy) | `configurations.py` | Ask Eugene |
| Add pass/fail limits for a new param (legacy) | `limits.py` | Required before `logger.log_test` |
| New SCPI helper | matching `*_setup.py` | Prefer reuse first |

Full legacy tutorials (including **Voffset** and **DC sweep**): [TEST_DESIGN.md](TEST_DESIGN.md).

---

## Rules

- Do not edit main.py or configurations.py without checking with Eugene
- Do not share or commit env.local
- Always use the push tool — do not run raw git commands to push
- If push fails, screenshot the terminal and send to Eugene

---

## Run a lab test (after setup)

1. Connect MSO / DP832 / DG8xx (and DMM if your test needs it)
2. From the repo folder:

```
.\venv\Scripts\python.exe main.py
```

3. Check the Excel datalog written at the end of the run
4. For OPA SCPI debug: `$env:OPA_DEBUG="1"` then re-run

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| push not recognised | Run `.\Github_Auto\setup_push_command.bat`, close terminal, open new one, then `push` |
| venv not found | Run `python install.py` again |
| Nothing to push message | You are already synced — no action needed |
| AI timeout | Popup opens anyway — type your description manually |
| Push button disappeared | Type `.\push_button` in terminal |
| PR not on GitHub | Check terminal for red error text, send to Eugene |
| Instrument not found | See [README.md](README.md) troubleshooting; confirm `*IDN?` prints your gear |
| `TEST_SPECS` ValueError | Add the parameter in `limits.py` before logging |

---

## Repo structure

```
PythonAutomation/
├── Github_Auto/            automation tools
│   ├── git_helper.py       push script (do not edit)
│   ├── push_button.pyw     floating button
│   └── env.local           your keys — never commit this
├── venv/                   Python environment (auto-created)
├── main.py                 run this for lab tests
├── opa_tests.py            OPA module
├── logic_tests.py          Logic module
├── configurations.py       VCC_LIST, current_limit, capture helpers
├── limits.py               datasheet pass/fail specs
├── instruments.py          PyVISA discovery + sessions
├── *_setup.py              PSU / AWG / scope / DMM SCPI wrappers
├── datalog.py              Excel results
├── install.py              run once per machine
├── push.bat                terminal push command
├── push_button.bat         relaunch floating button
├── README.md               project overview
├── TEST_DESIGN.md          how to design / add tests
├── PYVISA_OPA_DEEP_DIVE.md PyVISA + OPA architecture deep dive
└── WORKFLOW.md             this file
```

---

*Questions? Message Eugene on the team chat.*
