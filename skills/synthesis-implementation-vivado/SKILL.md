---
name: synthesis-implementation-vivado
description: "Use when running Vivado synthesis or implementation in non-project (batch Tcl) mode, choosing a synthesis/implementation strategy, setting up out-of-context synthesis for hierarchical blocks, configuring incremental compile, or interpreting utilization/QoR reports. Trigger phrases: 'Vivado batch mode', 'non-project Tcl flow', 'synthesis strategy', 'Performance_ExplorePostRoutePhysOpt', 'Flow_RuntimeOptimized', 'out-of-context synthesis', 'OOC synthesis', 'incremental compile', 'utilization report'. Use between RTL/TB completion and timing closure iteration."
---

# Synthesis and implementation (Vivado, UltraScale+)

Sits between "RTL and testbench are simulation-clean" and "timing is closed" — this skill runs the tool; `../timing-closure-ultrascale/` diagnoses and fixes what the tool reports.

## Non-project batch Tcl flow

Full runnable skeleton in `references/non-project-tcl-flow.tcl`. Non-project mode (vs. the Vivado project GUI/`.xpr` flow) is preferred for reproducibility and CI: every setting is explicit in a script, not stored in a GUI-editable project file that can drift.

```tcl
read_verilog -sv [glob ./rtl/*.sv]
read_xdc ./constraints/top.xdc
synth_design -top top_module -part xcvu9p-flga2104-2L-e

opt_design
place_design
route_design

report_timing_summary -file post_route_timing.rpt
report_utilization -file post_route_util.rpt
write_checkpoint -force post_route.dcp
write_bitstream -force top_module.bit
```

## Strategy selection (full table in references/strategy-selection-guide.md)

Vivado's built-in strategies bias the tool's effort differently — picking by symptom, not by habit:
- **Default** (`Vivado Synthesis Defaults` / `Vivado Implementation Defaults`) — reasonable starting point for a new design before any QoR problem has appeared.
- **`Performance_ExplorePostRoutePhysOpt`** — when timing is close but not closing, and post-route physical optimization (additional retiming/replication passes after routing) has room to help.
- **Congestion-oriented strategies** (e.g. `Performance_SpreadLogic_high`) — when the failure pattern is congestion-shaped per `../timing-closure-ultrascale/references/qor-fix-playbook.md`, before manually floorplanning.
- **`Flow_RuntimeOptimized`** — when iteration speed during RTL bring-up matters more than final QoR (early-stage development, not final sign-off runs).

Strategy selection is a tuning knob, not a substitute for fixing an actual RTL/logic-depth/congestion issue — if a design needs an aggressive strategy just to barely close, treat that as a signal to revisit the RTL via `../rtl-authoring-ultrascale/`, since the same design will likely be fragile to any future change under that same strategy.

## Out-of-context (OOC) synthesis

For hierarchical reuse (a block synthesized independently of the top-level context, with its own clock constraints applied by the block's own `.xdc`), use `synth_design -mode out_of_context`. This lets a sub-block's synthesis QoR be checked and iterated on independently — especially valuable for a 644.53125 MHz-class sub-block inside an otherwise 322.265625 MHz-class design, since it isolates that block's tighter timing budget for focused iteration rather than re-running full top-level implementation on every change.

## Incremental compile

`write_checkpoint`/`read_checkpoint` plus `-directive` incremental options let a later implementation run reuse a previous run's placement as a starting point, reducing run-to-run QoR variation — use this once a design has a known-good implementation checkpoint and only small RTL changes are being iterated on, not as a substitute for a clean full run before sign-off.

## Utilization / resource reports

`references/report-interpretation.md` covers `report_utilization` reading (LUT/FF/DSP/BRAM/URAM usage vs. budget, per-hierarchy breakdown) — kept separate from `../timing-closure-ultrascale/references/timing-report-interpretation.md`, which covers timing-specific reports, so the two don't duplicate.

## See also

`../timing-closure-ultrascale/` (diagnosing what these reports reveal), `../bitstream-and-bringup/` (the next stage after implementation closes), `../rtl-authoring-ultrascale/` (the source-level fixes strategy tuning can't substitute for).
