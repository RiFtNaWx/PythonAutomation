# Handover Checklist 2.docx -- full text dump

keywords: handover, checklist, docx, OA template
main_idea: Full paragraph and table extraction from Handover Checklist 2.docx

## Environment

- Source: `C:\Users\OoiJianHong\Downloads\Handover Checklist 2.docx`
- python-docx importable (before extraction): **NO** (`No module named 'docx'`)
- python-docx installed in venv (`venv\Scripts\python.exe`): **NO initially** -- installed `python-docx==1.2.0` + `lxml==6.1.3` via pip for this dump
- python-docx importable (after pip install): **YES** (version 1.2.0)
- venv python: `c:\Users\OoiJianHong\Eugene's Repo\PythonAutomation\venv\Scripts\python.exe`
- Table count: **1**
- Row counts per table: [8]

## Comparison with Handover Checklist.docx

- Other file: `C:\Users\OoiJianHong\Downloads\Handover Checklist.docx` (exists: True)
- Same layout as Handover Checklist.docx: **NO (different layout)**
- Handover Checklist.docx table count: 1
- Handover Checklist.docx row counts: [10]
- Handover Checklist 2 paragraph count: 29
- Handover Checklist paragraph count: 27

## Headers and footers

### Header -- section 1
- Para 1: ``
- Para 2: ``

### Header -- section 2
- Para 1: ``
- Para 2: ``

### Header -- section 3
- Para 1: ``
- Para 2: ``

### Header -- section 4
- Para 1: ``
- Para 2: ``

### Footer -- section 1
- Para 1: ``

### Footer -- section 2
- Para 1: ``

### Footer -- section 3
- Para 1: ``

### Footer -- section 4
- Para 1: ``


## Paragraphs (numbered)

1. (empty) [style: Normal]
2. Employee Resignation & Handover Checklist [style: Normal]
3. (empty) [style: Normal]
4. 1. Document Purpose [style: Normal]
5. To confirm full handover of job duties, documents upon employee resignation/termination. [style: Normal]
6. 2. Employee Basic Information [style: Normal]
7. (empty) [style: Normal]
8. Employee Name: OO JIAN HONG [style: Normal]
9. Employee ID: JW0031 [style: Normal]
10. Department: AE & FAE [style: Normal]
11. Position: APPLICATION ENGINEER [style: Normal]
12. Entry Date: 25/5/2026 [style: Normal]
13. Last Working Date:  21/10/2026 [style: Normal]
14. 3. Job Duty & Project Handover [style: Normal]
15. (empty) [style: Normal]
16. (empty) [style: Normal]
17. (empty) [style: Normal]
18. 4. Final Declaration & Sign-off [style: Normal]
19. Resigning Employee (Handover Person): [style: No Spacing]
20. I hereby confirm that I have fully handed over all work tasks, company documents, and data. No confidential company materials are privately retained. I shall be responsible for any losses caused by incomplete handover. [style: No Spacing]
21. Signature: OO JIAN HONG [style: No Spacing]
22. Date: 11/9/2026 [style: No Spacing]
23. (empty) [style: No Spacing]
24. Receiver (Successor): [style: No Spacing]
25. I have received all handover items and clearly understand the pending work matters. [style: No Spacing]
26. Signature: _______________ [style: No Spacing]
27. Date:  [style: No Spacing]
28. (empty) [style: No Spacing]
29. Note: This checklist is valid for company filing. [style: No Spacing]

## Tables

### Table 1 (8 rows)

**Row 1**
- Col 1: No.
- Col 2: Handover Items
- Col 3: Work Progress / Pending Tasks / Key Contacts
- Col 4: Document / File Location
- Col 5: Status
- Col 6: Remarks

**Row 2**
- Col 1: 1
- Col 2: Software + Excel
- Col 3: PIC: Eugene; Users: AE & Design Team. Local console has Setup, Run, Results, and Tags. Apply campaign is required before selections take effect. Excel uses one writer: photos through paste.photos and numbers through paste.values from sessions/report.json. Known mappings: GBW TTSOP R20:U20; GBW SOP8 C21; VOS R16/B16; Logic VOX G16; ICC D10; LIM Iplus B2. Pending: remaining Logic fill, RS0204 grids, and RS2323 rON structured mapping.
- Col 4: PythonAutomation repository docs/handover/SOFTWARE_CONSOLE.md; ate/core/campaign_outline.py; AGENTS.md; docs/handover/AGENT_PROMPTS.md
- Col 5: ☐ Completed ☒ Partial
- Col 6: (empty)

**Row 3**
- Col 1: 2
- Col 2: RS622 New Board
- Col 3: PIC: Ariff; Access: Eugene; Users: AE & Design Team. Perform preliminary testing first, then detailed testing and automation. Choose a CHAR jumper or internal wire for the VoS module connection and preserve the existing console behavior.
- Col 4: PCBToPrint; PythonAutomation repository; docs/handover/VOS_RESEARCH.md
- Col 5: ☐ Completed ☒ Partial
- Col 6: Physical PCB item. Preliminary test is required before automation; 

**Row 4**
- Col 1: 3
- Col 2: Cloud Database for Test
- Col 3: PIC: Eugene Access: AE & Design Team; Users: All Members. START writes to the local OneDrive folder and OneDrive uploads. Scalable path: #Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/. Create folders / Apply and each new version automatically creates that operator’s tree.
- Col 4: #Test_Database SharePoint folder; docs/handover/CLOUD_TEST_DATABASE.md; sharepoint.url; cloud_db.txt
- Col 5: ☐ Completed ☒ Partial
- Col 6: Windows cannot use the HTTPS link as a folder. App zip refuses a private unzip copy. No cloud Python worker.

**Row 5**
- Col 1: 4
- Col 2: Work Report
- Col 3: PIC: Kevin; Access / Users: All Members. Daily work report is available for administrative handover.
- Col 4: WorkReport-Daily-Jianhong-20260525.xlsx
- Col 5: ☒ Completed ☐ Partial 
- Col 6: (empty)

**Row 6**
- Col 1: 5
- Col 2: Lead Holder
- Col 3: PIC: Eugene. Print one improved physical version and continue with a new design if further refinement is needed.
- Col 4: Physical prototype / design files
- Col 5: ☐ Completed ☒ Partial 
- Col 6: (empty)

**Row 7**
- Col 1: 6
- Col 2: VoS Research
- Col 3: POC: Ariff; Full access: Eugene and William; Usage: OpAmp. Existing vos_sweep on the G201 research board uses test ID VOS_mV. Next: implement and test a modular VoS section on RS622 so external flying wire are no longer required. 
- Col 4: VOS Research workbook
- Col 5: ☐ Completed ☒ Partial
- Col 6: (empty)

**Row 8**
- Col 1: 7
- Col 2: Tools
- Col 3: Laptops, Bags, Toolbox
- Col 4: Will return on 21/9/2026
- Col 5: ☒  N/A
- Col 6: (empty)
