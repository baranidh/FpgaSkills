---
name: timing-closure-ultrascale
description: "Use for anything related to Vivado timing closure on UltraScale/UltraScale+ parts, especially 322.265625 MHz-class (100G/CAUI4-style segmented) and 644.53125 MHz-class (Aurora/JESD204-style) clock domains. Trigger phrases: 'timing closure', 'XDC constraints', 'setup violation', 'hold violation', 'WNS', 'multicycle path', 'false path', 'clock skew', 'report_timing_summary', 'report_clock_utilization', 'Pblock floorplan', 'route congestion', '322 MHz timing', '644 MHz timing', 'why won't this path close'. Use whenever implementation reports negative slack, or before implementation to pre-constrain a design."
---

# Timing closure on UltraScale+

The centerpiece skill of this library. Read `../../references/clock-family-reference.md` and `../../references/timing-glossary.md` first if the terms below aren't already second nature.

## XDC authoring quick reference (full library in references/xdc-snippet-library.md)

```tcl
# Primary clock at 322.265625 MHz-class period
create_clock -name core_clk -period 3.10303 [get_ports core_clk_p]

# Primary clock at 644.53125 MHz-class period
create_clock -name fast_clk -period 1.55152 [get_ports fast_clk_p]

# Multicycle path: a slow control update reaching a fast pipeline every N cycles by design
set_multicycle_path -setup 4 -from [get_cells slow_ctrl_reg] -to [get_cells fast_pipe_reg]
set_multicycle_path -hold  3 -from [get_cells slow_ctrl_reg] -to [get_cells fast_pipe_reg]

# False path: genuinely async, protected by a synchronizer already (see rtl-authoring-ultrascale)
set_false_path -from [get_cells async_source_reg] -to [get_cells sync_ff1]

# CDC path bounded on data arrival only, not skew - typical for a synchronizer's onward path
set_max_delay -datapath_only 3.0 -from [get_cells sync_ff2] -to [get_cells consumer_reg]
```

**Scoping discipline**: always scope exceptions as narrowly as the specific cells/pins involved (`-from`/`-to` on specific cells, not blanket clock-to-clock exceptions) — a false path or multicycle exception scoped too broadly silently un-times paths you didn't intend to exempt, which is how "timing closed" reports hide real bugs. Every exception here should trace back to a named CDC crossing or an explicitly-stated slow-path relationship in the interface contract (`../fpga-functional-spec/`) — never added purely because a path was failing and the exception made the number go away.

## The QoR fix playbook (full decision tree in references/qor-fix-playbook.md)

When a path fails, diagnose by symptom before reaching for a fix:

| Symptom | Likely cause | Fix |
|---|---|---|
| Many failing paths clustered in one region, high routing delay | Placement congestion | Floorplan with a Pblock (`references/pblock-floorplanning.md`) to shrink placement distance |
| One or few paths failing, high logic delay, moderate route delay | Too many logic levels for the period | Add a pipeline register / retime (`../rtl-authoring-ultrascale/`), or let `phys_opt_design -retime` redistribute existing registers |
| Failing paths specifically between cascaded DSP48E2 stages | Broken cascade (logic inserted between stages) | Remove the intervening logic; re-verify cascade inference (`../rtl-authoring-ultrascale/references/dsp48e2-patterns.md`) |
| Hold violations after otherwise-clean setup closure | Normal post-route artifact, or a false-path exception masking a real issue | Let the router's automatic hold-fixing run; if hold fails only where an exception exists, re-examine that exception's scope |
| Failures concentrated on one clock domain's boundary paths | Clock skew / MMCM phase relationship | Adjust MMCM phase, or add/adjust a CDC exception per `rtl-authoring-ultrascale`'s patterns |

## Reading the reports (full detail in references/timing-report-interpretation.md)

`report_timing_summary` first: check **every** path group's WNS/TNS, not just the first one printed — a design can show WNS ≥ 0 on its main clock and still be failing on a secondary or CDC-exception path group. `report_clock_utilization` next, to confirm actual achieved skew/clock network usage matches what the XDC assumed.

## Floorplanning

Reach for `references/pblock-floorplanning.md` when the symptom table above points to congestion — Pblocks are a targeted fix for placement distance, not a default first move; try letting the tool place freely first, since an unnecessary Pblock can itself create the congestion it's meant to solve by fencing logic into too small a region.

## See also

`../synthesis-implementation-vivado/` (running the implementation that produces these reports; utilization/resource reports specifically live there, not here), `../rtl-authoring-ultrascale/` (the source-level fixes most QoR playbook entries point back to), `../ultra-low-latency-transceivers/` (transceiver-adjacent timing at these same frequencies).
