keywords: rs1gt34, datasheet, icc, icct, 2.0-5.5, 3.0-5.5, 0-5.6, leftover-honest
main_idea: Datasheet ICC is VI=VCC or GND, IO=0, VCC 2.0-5.5, +25C max 1 uA. ICCT spec row is VCC=5.5, one input 3.4 V, Full 500 uA. Golden 0-5.6 ICC and ICCT 3.0-5.5 are lab plots. Path B default is datasheet ICC 2.0-5.5/0.1 plus ICCT 3.0-5.5/0.1 (includes spec 5.5). Golden 0-5.6 stays overlay.

Datasheet extract (RS1GT34 Rev A.1.1):
- ICC VI=5.5V or GND, IO=0, 2.0V to 5.5V, +25C 0.1 typ / 1 max uA, Full 10
- ICCT One input at 3.4V, Other inputs at VCC or GND, 5.5V, Full 500 uA
- Recommended VCC 2.0-5.5. Abs max 6.5. Ioff is VCC=0.

Golden/template 0-5.6: IDD vs VCC plot including Ioff (VCC=0) and 5.6 OVP headroom. Not the ICC limit row. Judge 1 uA only inside 2.0-5.5.
Golden/template ICCT 3.0-5.5 A=3.4: TTL mid-level vs VCC curve. Spec is 5.5. Apply 500 uA across the plot (template).

leftover-honest: datasheet text says VI=5.5V or GND; golden loop uses VI=0 or this VCC. Path B keeps this-VCC (same as golden). VI=5.5 at VCC=2.0 is input overdrive, not ICC quiet state.
