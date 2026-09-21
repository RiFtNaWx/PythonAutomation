# Handover Checklist 2 - filled.docx -- full text dump

keywords: handover, checklist-2, filled, kevin, oa, docx
main_idea: Filled OA handover checklist with 9 table rows (incl header), Kevin as Cloud PIC, and guide sections 3b-3e.

## Source

- Path: `C:\Users\OoiJianHong\Downloads\Handover Checklist 2 - filled.docx`
- Size: 63241 bytes
- Table count: 1
- Table 0 row count: 9
- Table 0 col count: 6

## Table 0 (all cells)

### Row 0
- **Col 0:**
  No.
- **Col 1:**
  Handover Items
- **Col 2:**
  Work Progress / Pending Tasks / Key Contacts
- **Col 3:**
  Document / File Location
- **Col 4:**
  Status
- **Col 5:**
  Remarks

### Row 1
- **Col 0:**
  1
- **Col 1:**
  1. Software (test program + Excel fill)
- **Col 2:**
  PIC: Eugene. Users: AE and Design.
  
  What it is: one program on the laptop. Four tabs -- Setup, Run, Results, Tags. Pick your name, click Apply, then run. Excel fills photos and numbers by itself. Do not type the numbers.
  
  What I built: product switch (OpAmp, Logic, Analog switch, Level), people folders so two people do not overwrite each other, tags, who-ran-what list, STS PDF after a run, zip START.bat for AE, PSU safety (OVP/OCP), DEMO dry-run without real instruments.
  
  How to use: unzip the console (or git clone eugene-console). Add OneDrive shortcut to #Test_Database. Double-click START.bat. Pick your name -- not All. Apply campaign. Discover, Open Session, START. Results -> Fill Excel numbers if the sheet did not fill.
  
  Still open (Eugene): Logic Excel only fills voltages that exist on the sheet. RS0204 Icc/VOH not mapped yet. RS2323 rON is still a picture in the PDF. Comparator and other stub families are parked. Do not promise those.
- **Col 3:**
  PythonAutomation, branch eugene-console.
  docs/handover/SOFTWARE_CONSOLE.md
  AGENTS.md
  STATUS.md
  docs/VIBE_CODE.md
  Git: git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git
  (Old link on the Excel also lists jian-hong/Python_Automation_JH -- confirm with Eugene which remote AE use.)
- **Col 4:**
  ☐ Completed  ☒ Partial
- **Col 5:**
  Next owner: Eugene. I built the console. He keeps it.

### Row 2
- **Col 0:**
  2
- **Col 1:**
  2. RS622 new board
- **Col 2:**
  PIC: Ariff. Access: Eugene. Users: AE and Design.
  
  What it is: a new physical board. Not a software job.
  
  What I did: software already has RS622 folders, GBW / VOS / ORT maps, and the VOS sweep test. Campaign can run once the board and fixture are ready.
  
  How to continue: Ariff does preliminary test first, then detailed test, then automation. Do not skip the first test. Keep using this same program -- do not build a second one.
- **Col 3:**
  PCBToPrint (pictures / Gerber).
  PythonAutomation
  docs/handover/VOS_RESEARCH.md
- **Col 4:**
  ☐ Completed  ☒ Partial
- **Col 5:**
  Hardware. Preliminary test before automation.

### Row 3
- **Col 0:**
  3
- **Col 1:**
  3. Cloud Database for Test
- **Col 2:**
  PIC: Kevin. Users: everyone who runs a test.
  
  What it is: a shared OneDrive folder named #Test_Database. Not a website. Not SQL. Nothing runs in the cloud. The program runs on each laptop. The scope stays on the desk.
  
  What I built: folder shape Component / Part / Package / Person / Version_N. Apply / Create folders makes that person's tree. START writes into it. OneDrive uploads. App zip refuses a private copy inside the unzip. Windows cannot use the https link as a folder -- each PC needs cloud_db.txt with the local path.
  
  How to use (teach this):
  1. SharePoint #Test_Database -> Add shortcut to OneDrive. Do not click Sync. Do not drag-copy.
  2. Always keep on this device.
  3. Open the console. Pick your name. Apply.
  4. Two people, two folders. Example: Logic/RS1G08/SC70-5/Ariff/Version_1 and .../ChangThong/Version_1.
  5. New test code still needs a zip or git pull. This folder only holds results.
  
  Work Report is a different Excel. Do not put it in this folder.
- **Col 3:**
  SharePoint: RD / Handover / Jianhong / #Test_Database
  docs/handover/CLOUD_TEST_DATABASE.md
  ate/config/sharepoint.url (browser link)
  ate/config/cloud_db.txt (local folder path on this PC)
  Handover.xlsx sheet Cloud Database -- read-aloud page
- **Col 4:**
  ☐ Completed  ☒ Partial
- **Col 5:**
  Kevin takes over teaching + SharePoint access. Structure is in place.

### Row 4
- **Col 0:**
  4
- **Col 1:**
  4. Work Report
- **Col 2:**
  PIC: Kevin. Users: all members.
  
  Daily work Excel for admin / HR. Not the lab test folder.
  
  What I did: handed over the file. Do not store it inside #Test_Database.
- **Col 3:**
  WorkReport-Daily-Jianhong-20260525.xlsx
- **Col 4:**
  ☒ Completed  ☐ Partial
- **Col 5:**
  Admin file. Separate from lab results.

### Row 5
- **Col 0:**
  5
- **Col 1:**
  5. Lead Holder
- **Col 2:**
  PIC: Eugene.
  
  Physical print (plastic/metal). Not software.
  
  What I left: print a better one if needed. New design if the current one is not enough.
  
  I did not own a second software tool for this.
- **Col 3:**
  Physical prototype / design files
- **Col 4:**
  ☐ Completed  ☒ Partial
- **Col 5:**
  Hardware. Out of the software pack.

### Row 6
- **Col 0:**
  6
- **Col 1:**
  6. VoS Research
- **Col 2:**
  PIC: Ariff. Access: Eugene, William. Users: OpAmp.
  
  What it is: input offset test. Already in the program. Tick VOS DC Sweep and run. Numbers go to the lab Excel VOS sheet (R16 / B16).
  
  The Downloads file VOS Research.xlsx is the long 101-point research table, not the daily AE report. Latest sweep sheet in that file: vos sweep 2026-09-14 100753.
  
  Next: put the gain block on the new RS622 board so we stop using flying wires. Same test. No second program. Ariff board, William sim, Eugene signs so VOS and GBW do not fight.
- **Col 3:**
  C:\Users\OoiJianHong\Downloads\VOS Research.xlsx
  (copy also on OneDrive)
  docs/handover/VOS_RESEARCH.md
  Handover.xlsx sheet RS622 New board
- **Col 4:**
  ☐ Completed  ☒ Partial
- **Col 5:**
  Software sweep exists. Board module is next.

### Row 7
- **Col 0:**
  7
- **Col 1:**
  7. Tools
- **Col 2:**
  Laptops, bags, toolbox.
- **Col 3:**
  Return on 21/9/2026
- **Col 4:**
  ☒ N/A
- **Col 5:**
  Physical return. Not a software item.

### Row 8
- **Col 0:**
  8
- **Col 1:**
  8. Docs / how to continue after I leave
- **Col 2:**
  Read AGENTS.md first. Stop at the first matching row. That file says where to change.
  
  AE: unzip + START.bat. Engineer: git clone eugene-console, then START.bat.
  
  Add a person from Setup (Save person). Add a Version by typing Version_N then Apply. Add a test: docs/VIBE_CODE.md (do not edit runner.py). Do not start work in main.py.
  
  Cursor paste blocks: docs/handover/AGENT_PROMPTS.md and docs/PROMPT_GUIDE.md.
  
  Lunch talk order: Kevin (this folder) -> Eugene (software) -> Ariff (board + VoS).
- **Col 3:**
  docs/handover/2026-09-11_jianhong_checklist.md
  docs/handover/CLOUD_TEST_DATABASE.md
  docs/handover/SOFTWARE_CONSOLE.md
  docs/handover/VOS_RESEARCH.md
  docs/handover/AGENT_PROMPTS.md
  C:\Users\OoiJianHong\Downloads\Handover.xlsx
- **Col 4:**
  ☒ Completed  ☐ Partial
- **Col 5:**
  Print pack is in the repo + OneDrive.

## Paragraphs (body)

- Para 0: _(empty)_
- Para 1 **[bold]**:
  Employee Resignation & Handover Checklist
- Para 2: _(empty)_
- Para 3 **[bold]**:
  1. Document Purpose
- Para 4:
  To confirm full handover of job duties, documents upon employee resignation/termination.
- Para 5 **[bold]**:
  2. Employee Basic Information
- Para 6: _(empty)_
- Para 7:
  Employee Name: OO JIAN HONG
- Para 8:
  Employee ID: JW0031
- Para 9:
  Department: AE & FAE
- Para 10:
  Position: APPLICATION ENGINEER
- Para 11:
  Entry Date: 25/5/2026
- Para 12:
  Last Working Date:  21/10/2026
- Para 13 **[bold]**:
  3. Job Duty & Project Handover
- Para 14: _(empty)_
- Para 15: _(empty)_
- Para 16: _(empty)_
- Para 17: _(empty)_
- Para 18:
  Receiver of software + cloud: Kevin for the folder, Eugene for the program, Ariff for the board. Kevin signs below when he has seen the Cloud page and the #Test_Database folder.
- Para 19:
  Handover.xlsx -- the 6-item sheet plus Cloud / Software / RS622 talk pages. VOS Research.xlsx -- long sweep table. This Word -- OA filing. WorkReport-Daily-Jianhong-20260525.xlsx -- daily admin, not the lab folder.
- Para 20 **[bold]**:
  3e. Files on OneDrive / this PC
- Para 21:
  Parked on purpose: cloud Python worker, OneDrive Excel robot (A13), website scrape into #Test_Database. Do not promise those.
- Para 22:
  Hardware: RS622 new board (Ariff). Lead holder reprint (Eugene). VoS module on the new board so we stop flying wires (Ariff / William / Eugene).
- Para 23:
  Software: Logic Excel does not yet fill every voltage. RS0204 grids not mapped. RS2323 rON table is still a picture. Comparator / Interface / Vref suites parked. OpAmp noise is 0.1-10 Hz Vpp, not nV/rtHz.
- Para 24 **[bold]**:
  3d. Still not finished (say out loud, do not hide)
- Para 25:
  First-day PC: Add shortcut to #Test_Database (not Sync). Always keep on this device. START.bat. Setup -> pick name -> Apply -> Open DB folder and check you are in your own Version.
- Para 26:
  Chinese: 就是 OneDrive 里一个共用文件夹，名字叫 #Test_Database。程序装在电脑上，示波器插在桌上。按 START，文件进你自己名字的文件夹，OneDrive 自己上传。两个人就两个文件夹，不要共用一个 Version。Work Report 是另一份 Excel，不要丢进这个文件夹。
- Para 27:
  English: It's just a shared folder on OneDrive named #Test_Database. The program is on your laptop. The scope stays on the desk. Press START, files go under your name. OneDrive uploads. Two people, two folders. Don't share one Version. Work Report is a different Excel.
- Para 28 **[bold]**:
  3c. How to guide Kevin / next person (say this)
- Para 29:
  I wrote the handover pack: Handover.xlsx, this checklist, CLOUD_TEST_DATABASE.md, SOFTWARE_CONSOLE.md, VOS_RESEARCH.md, AGENT_PROMPTS.md. VOS Research.xlsx is the research long table.
- Para 30:
  I made Excel fill from the run (photos + numbers), STS PDF after a run, tags, and a run list. AE can unzip START.bat. Engineers clone branch eugene-console.
- Para 31:
  I put all test results in one shared OneDrive folder #Test_Database, with one folder per person and Version, so Eugene and Ariff do not overwrite each other.
- Para 32:
  I built the operator console that the lab uses now. Old main.py is leftover only. Live program: ate folder, worker port 8766, screen port 5174.
- Para 33 **[bold]**:
  3b. What I did (Jian Hong)
- Para 34 **[bold]**:
  4. Final Declaration & Sign-off
- Para 35:
  Resigning Employee (Handover Person):
- Para 36:
  I hereby confirm that I have fully handed over all work tasks, company documents, and data. No confidential company materials are privately retained. I shall be responsible for any losses caused by incomplete handover.
- Para 37:
  Signature: OO JIAN HONG
- Para 38:
  Date: 11/9/2026
- Para 39: _(empty)_
- Para 40:
  Receiver (Successor):
- Para 41:
  I have received all handover items and clearly understand the pending work matters.
- Para 42:
  Signature: _______________
- Para 43:
  Date: 
- Para 44: _(empty)_
- Para 45:
  Note: This checklist is valid for company filing.
