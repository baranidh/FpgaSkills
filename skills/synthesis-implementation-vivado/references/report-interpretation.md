# Utilization / resource report interpretation

(Distinct from `../../timing-closure-ultrascale/references/timing-report-interpretation.md`, which covers timing-specific reports — this file is specifically about resource utilization.)

## `report_utilization`

```tcl
report_utilization -file post_route_util.rpt
report_utilization -hierarchical -file post_route_util_hier.rpt
```

- **Top-level summary**: LUT/FF/DSP48E2/BRAM/URAM/IO usage against the part's total — check this against the project's resource budget, not just "did it fit."
- **`-hierarchical`**: per-instance breakdown, which is how you catch a specific instance that silently fell back to fabric logic instead of inferring a DSP/BRAM/URAM (see `../../rtl-authoring-ultrascale/references/dsp48e2-patterns.md` and `bram-uram-inference.md`) — an unexpected LUT spike in one instance, with a corresponding missing/lower-than-expected DSP or RAMB/URAM count in that same instance, is the signature of a failed inference.
- **DSP/BRAM/URAM specifically**: compare actual counts against the number you expect from the RTL structure (one DSP per pipelined multiply-accumulate tap, one BRAM/URAM per memory instance at its expected tile count) — a mismatch here is a synthesis-stage bug to fix before implementation, not something implementation will resolve.

## Resource budget tracking

Keep a running expected-vs-actual table per major block, especially for a design with a tight utilization target (e.g. multiple 644.53125 MHz-class datapaths sharing a device with headroom reserved for a 322.265625 MHz-class control plane) — a utilization report read in isolation, without a budget to compare against, won't catch a slow creep toward over-utilization across incremental RTL changes.

## Congestion cross-check

High LUT/FF utilization concentrated in a small physical region (visible via `report_utilization`'s per-clock-region breakdown, or cross-referenced with `report_design_analysis -congestion`) is often the root cause behind a congestion-shaped timing failure — read this report alongside `../../timing-closure-ultrascale/references/qor-fix-playbook.md`'s congestion branch rather than only after a timing failure prompts you to look.

## Power (if relevant to the project)

`report_power` isn't a substitute for utilization/timing analysis but is worth running alongside these reports for designs with a power budget — high-toggle-rate logic at 644.53125 MHz-class frequencies can dominate dynamic power in ways that aren't obvious from utilization counts alone.
