# Legacy file map — prefer README.md and TEST_DESIGN.md

See:
  README.md                 — overview, bench setup, how a run works
  WORKFLOW.md               — first-time install, push / PR, ownership
  TEST_DESIGN.md            — where to change code + new test tutorials (Voffset, DC sweep)
  PYVISA_OPA_DEEP_DIVE.md   — full PyVISA / OPA architecture deep dive

LabAutomation/
├── configurations.py   # Global test configuration: VCC ranges, limits, filenames
├── instruments.py      # VISA abstraction: discovery, connection, basic I/O
├── scope_setup.py      # Oscilloscope: channels, timebase, triggers, measurements
├── dmm_setup.py        # DMM: V, I, capacitance setup + read
├── psu_setup.py        # Power supply: channel config, limits, sequencing
├── generator_setup.py  # Signal generator: waveform, freq, amplitude, offset
├── logic_tests.py      # Logic device test cases
├── opa_tests.py        # OPA test cases
├── datalog.py          # Results + pass/fail Excel output
├── limits.py           # Datasheet limits only (no logic)
├── utils.py            # Timers, binary parse, helpers
└── main.py             # Entry: open instruments, run tests, cleanup

Future / product modules:
├── ldo_tests.py
└── level_shifter_tests.py
