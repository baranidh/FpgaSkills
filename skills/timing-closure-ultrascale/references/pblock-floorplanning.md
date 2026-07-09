# Pblock floorplanning

## When to reach for this

Only after `report_design_analysis -congestion` (or a clearly congestion-shaped failure pattern per `qor-fix-playbook.md`) confirms placement/routing distance is the actual problem — not as a default response to any timing failure.

## Basic Pblock creation

```tcl
create_pblock pblock_fast_datapath
add_cells_to_pblock [get_pblocks pblock_fast_datapath] \
    [get_cells -hierarchical -filter {NAME =~ "*fast_datapath_inst*"}]
resize_pblock [get_pblocks pblock_fast_datapath] -add {SLICE_X50Y100:SLICE_X90Y180}
resize_pblock [get_pblocks pblock_fast_datapath] -add {DSP48E2_X2Y40:DSP48E2_X4Y72}
resize_pblock [get_pblocks pblock_fast_datapath] -add {RAMB36_X2Y20:RAMB36_X4Y36}
```

Include every resource type (`SLICE`, `DSP48E2`, `RAMB36`/`RAMB18`, `URAM288`) the instance actually uses — a Pblock that only bounds `SLICE` ranges while the instance also uses DSPs outside that range doesn't reduce the placement distance you intended to fix, it just moves where the unconstrained resources land.

## Sizing discipline

Size the Pblock generously enough to give the placer freedom to avoid *creating* new congestion by over-constraining — a Pblock sized exactly to the instance's resource count with zero slack tends to force a dense, hard-to-route placement, trading one congestion problem for another. Start loose, tighten only if the loose version doesn't help.

## `CONTAIN_ROUTING` and `EXCLUDE_PLACEMENT`

```tcl
set_property CONTAIN_ROUTING true [get_pblocks pblock_fast_datapath]
```
`CONTAIN_ROUTING` forces routing (not just placement) to stay within the Pblock's bounds — useful when the goal is specifically to bound the physical distance data travels (directly relevant to a latency budget from `../../fpga-functional-spec/references/latency-budget-worksheet.md`), but it further restricts the router's freedom, so apply it only where the latency/timing goal specifically requires bounding routing distance rather than just placement.

## Nested / hierarchical Pblocks

For a large design with one especially timing-critical sub-block (e.g. a 644.53125 MHz-class datapath inside an otherwise 322.265625 MHz-class design), a nested Pblock scoped just to that sub-hierarchy is usually more effective than one large Pblock covering the whole design — it gives the placer maximum freedom everywhere that isn't actually timing-critical.

## Verification after floorplanning

Re-run `report_design_analysis -congestion` and `report_timing_summary` — confirm the floorplan actually reduced routing delay on the target paths rather than just moving the problem to the Pblock's boundary (a common symptom of a too-tightly-sized Pblock).
