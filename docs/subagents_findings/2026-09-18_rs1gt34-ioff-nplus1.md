keywords: rs1gt34, ioff, path-b, logic-dc, 2^n, n+1, vcc-first, leftover-honest
main_idea: Path B Ioff is VCC=0 power-off leakage, not IOZ. Output counts as a port (GT34 A+Y = 4 force combos). Measure n+1 DMM positions starting at VCC (leftover ICC), then each input, then Y. Min/max plus per-port labels.

Ioff because output is a port. RS1GT34 n=2 -> 2^n=4 (0/0, 5.5/0, 0/5.5, 5.5/5.5). n+1=3 Continues: VCC (already connected), A, Y. Judge |I|<=1 uA +25C.

leftover-honest: first live run starts VCC-only; A and Y DMM moves are later. Do not auto-Continue those prompts.
