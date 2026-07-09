# Timing report interpretation

(Distinct from `../../synthesis-implementation-vivado/references/report-interpretation.md`, which covers utilization/resource reports — this file is specifically about timing.)

## `report_timing_summary`

```tcl
report_timing_summary -max_paths 10 -delay_type max -report_unconstrained -file timing_summary.rpt
```

Read it top-down:
1. **Design Timing Summary** table at the top: WNS/TNS/WHS/THS per the whole design — a quick pass/fail, but not sufficient on its own.
2. **Per-clock-group tables further down**: check WNS/TNS for *every* path group listed, including inter-clock groups created by CDC exceptions — a design can show a clean top-line number while a specific path group (often a CDC or false-path-adjacent group) is still failing.
3. **`-report_unconstrained`**: always include this flag and check its output — an unconstrained path isn't "passing," it's invisible to the analysis entirely, which is a worse state than a known, visible failure.

## `report_timing -from ... -to ...` (single path deep-dive)

```tcl
report_timing -from [get_cells stage1_reg] -to [get_cells stage2_reg] -delay_type max
```
The output's logic/routing delay breakdown per cell is where you confirm which symptom in `qor-fix-playbook.md` actually applies — a path dominated by routing delay between two adjacent-looking registers is a placement/congestion issue; a path with many small logic-delay contributions across several LUTs is a logic-depth issue.

## `report_clock_utilization`

```tcl
report_clock_utilization -file clock_util.rpt
```
Confirms actual clock network usage and helps identify clocks sharing routing resources in ways that could introduce skew not visible in `create_clock`'s idealized period alone. Cross-check against `../../../references/clock-family-reference.md` for the expected period of any 322.265625/644.53125 MHz-class clock, since a typo in a `create_clock -period` value (e.g. rounding to 3.1 instead of 3.10303) silently changes the actual constraint being checked against.

## `report_design_analysis -congestion`

```tcl
report_design_analysis -congestion -file congestion.rpt
```
The first thing to check when the failure pattern in `qor-fix-playbook.md` looks congestion-shaped, before reaching for a Pblock.

## Cross-probing to RTL

Use `report_timing`'s cell names together with the implemented checkpoint (`open_checkpoint`) to cross-probe back into the RTL source (`highlight_objects`, or opening the schematic view) — confirms which specific RTL construct produced a failing path's logic levels, rather than guessing from the instance name alone.
