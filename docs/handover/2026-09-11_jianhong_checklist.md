# Jian Hong handover -- 2026-09-11

Print this first. Detail lives in the four sibling files in this folder.

**Repo (code):** `eugene-console` branch. Checklist link `jian-hong/Python_Automation_JH`. Daily clone used in lab docs: `git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git`. Same product. Confirm with Eugene which remote AE clones.

**Live product:** operator console (`ate/` + worker port **8766** + UI port **5174**). Not root `main.py`.

---

## Checklist map (what you say, who owns next)

| # | Sheet row | What it actually is | POC next | Say this in 20 seconds | Full doc |
|---|-----------|---------------------|----------|------------------------|----------|
| 1 | Software / last-shot improvement | One program on the laptop. It can fill the lab Excel. | Eugene | Program on the laptop. Results go into the shared folder. Excel fills itself. You don't type the numbers. | [SOFTWARE_CONSOLE.md](SOFTWARE_CONSOLE.md) |
| 2 | RS622 new board | New PCB. Software already has an RS622 folder. | Ariff then Eugene | Hardware. Not this software pack. Folders for RS622 already exist. | STATUS.md + PCBToPrint |
| 3 | Cloud Database for Test | Shared OneDrive folder `#Test_Database`. | Kevin | Shared folder. Program on the laptop. START writes in. OneDrive uploads. | [CLOUD_TEST_DATABASE.md](CLOUD_TEST_DATABASE.md) |
| 4 | Work report | Daily work Excel. Not the lab folder. | Kevin | Different file. Don't put it in `#Test_Database`. | WorkReport xlsx |
| 5 | Lead holder | Plastic/metal print. Not software. | Eugene | Hardware. Not this pack. | -- |
| 6 | VoS research | Offset test already in the program. Next: put it on the new board. | Ariff / Eugene / William | Sweep already works. The Downloads Excel is the long table. Next: stop flying wires. | [VOS_RESEARCH.md](VOS_RESEARCH.md) |

Agents / vibe-coders after you leave: [AGENT_PROMPTS.md](AGENT_PROMPTS.md) + repo-root [AGENTS.md](../../AGENTS.md).

---

## Meeting talk order (about 12 minutes)

1. **Kevin (2 min).** Open the `#Test_Database` folder. Say the section 8 lines. Show: two people = two name folders.
2. **Eugene (5 min).** Show four tabs. Apply, then Fill Excel numbers. Say what is still open (Logic 4.5 V only, RS2323 rON still a picture).
3. **Ariff (3 min).** VOS already runs. Next is the module on the new board, not a second program.

Do not promise: Comparator suite, nV/rtHz noise, A13 OneDrive Excel MCP, scraping en.run-ic.com into the database.

---

## Links (access)

| What | Where |
|------|--------|
| SharePoint `#Test_Database` | https://jumptechwin.sharepoint.com/:f:/s/RD/IgC_gG1VFnI3RbuN7gqBaNAxAU6m3sLDVuj4EIdauFRGG4E?e=te8KJN (also `ate/config/sharepoint.url`) |
| Code branch | `eugene-console` |
| Operator zip | `pack_ate_console.py` -> Desktop + `dist/ATE_Console_Try_*.zip` |
| Stakeholder status | [STATUS.md](../../STATUS.md) |
| Next waves | [docs/SHIP_NEXT.md](../SHIP_NEXT.md) |
| Copy-paste prompts | [docs/PROMPT_GUIDE.md](../PROMPT_GUIDE.md) |

---

## Not finished (say this out loud)

Must leftovers: Logic Excel fill is VOX sheet Vccs (1.65/2.3/3.0/4.5) + ICC D10; yaml 2.0/3.3/5.0/5.5 have no VOX row; RS0204 Icc/VOH grids unmapped; ORT photos-only; RS2323 rON table still a PDF image; stub families (Comparator, Interface, ...) parked.

Parked until founder unparks: A13 Graph/Excel MCP, A14 xyflow, no-code wizard, delete `main.py`.
