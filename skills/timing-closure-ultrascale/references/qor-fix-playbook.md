# QoR fix playbook

A symptom-driven decision tree. Diagnose before fixing — applying the wrong fix (e.g. floorplanning a logic-depth problem, or pipelining a congestion problem) burns iteration time without closing timing.

## Step 1: read the failure pattern, not just the worst number

Open `report_timing_summary` and look at the **shape** of the failure list, not just WNS:
- **Many paths failing, similar magnitude, concentrated in one or two hierarchical instances** → almost always congestion or a genuinely too-deep logic structure in that instance, not a scattered set of unrelated bugs.
- **One or a few isolated failing paths** → usually a specific structural issue (a wide mux that grew, a broken DSP cascade, a missed pipeline stage) — find that one path with `report_timing -from ... -to ...` and inspect its logic-level breakdown directly.
- **Failures only on CDC-exception-scoped paths** → re-examine the exception itself before touching RTL; a too-tight or wrongly-scoped exception can manufacture a failure that isn't really there.

## Step 2: match cause to fix

### Congestion (high routing delay, clustered failures)
1. Check `report_design_analysis -congestion` for the specific region.
2. Floorplan the offending hierarchy into a Pblock sized to reduce placement distance — see `pblock-floorplanning.md`. Don't shrink it further than needed; an over-constrained Pblock creates the congestion it's meant to fix.
3. If congestion stems from too much logic crammed into too little area rather than bad placement freedom, consider whether the block itself needs to be split or its resource usage reduced (fewer wide muxes, more DSP-mapped arithmetic) — a floorplan can't fix a genuine density problem.

### Logic depth (high logic delay, few levels but each one costly, or many levels)
1. Count logic levels on the specific failing path (`report_timing -to <endpoint>` shows the level-by-level breakdown).
2. Compare against the period budget in `../../../references/clock-family-reference.md` — at 644.53125 MHz-class frequencies the usable budget is much tighter than at 322.265625 MHz-class, so a structure that closed comfortably at the wider period may need an extra pipeline stage at the narrower one.
3. Add a pipeline register in RTL (preferred — see `../../rtl-authoring-ultrascale/`) and re-verify the latency budget in `../../fpga-functional-spec/references/latency-budget-worksheet.md`, or let `phys_opt_design -retime` redistribute existing register boundaries if the RTL structure allows it (i.e. no `dont_touch` blocking it).

### Broken DSP48E2 cascade
1. `report_timing -through` the specific DSP-to-DSP path; a cascade path with unexpectedly high routing delay (rather than the near-zero delay of true dedicated cascade routing) indicates the cascade broke.
2. Check `../../rtl-authoring-ultrascale/references/dsp48e2-patterns.md` for what disqualifies cascade inference and remove the intervening logic.

### Clock skew / CDC-adjacent failures
1. `report_clock_utilization` to see actual achieved skew per clock.
2. If skew between two related clocks is the issue, check the MMCM's phase relationship (`create_generated_clock` parameters) rather than trying to fix it with logic changes.
3. If the failure is on a path that should have been exempted by a CDC exception, re-examine that exception's scope (`xdc-snippet-library.md`) rather than assuming it's a genuine skew problem.

### Hold violations after clean setup closure
Usually resolved automatically by the router; if a hold violation persists specifically on a path with a `set_false_path` or `set_multicycle_path` exception, re-examine that exception — a false path incorrectly applied to a path the design does depend on will surface as an uncorrected hold violation, since the tool isn't inserting the delay it would otherwise add.

## Step 3: re-run, re-check every path group

After any fix, re-run implementation and check **every** path group's WNS/TNS again, not just the one that was failing — a floorplan change or added pipeline stage can shift congestion or skew elsewhere.
