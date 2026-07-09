# Timing glossary

Shared vocabulary for every skill that touches Vivado timing reports or clock design. Defined once here; skills link to this file instead of restating definitions.

| Term | Meaning |
|---|---|
| **WNS** (Worst Negative Slack) | The single worst (most negative, or least positive) slack value across all timing paths in a path group. Vivado's headline "did timing close" number — WNS ≥ 0 for every path group is the sign-off bar. |
| **TNS** (Total Negative Slack) | Sum of all negative slack across every failing endpoint in a path group. WNS tells you the worst offender; TNS tells you how widespread the problem is — one bad path vs. hundreds of marginal ones need different fixes. |
| **WHS / THS** | Same as WNS/TNS but for **hold** instead of setup. Hold violations don't scale with clock period and can't be fixed by lowering frequency — they need buffer/delay insertion or routing changes, and Vivado normally fixes them automatically post-route unless something (e.g. a bad false-path exception) is masking them. |
| **Setup slack** | `required_time - arrival_time` at a register's data input, checked against the *next* active clock edge. Negative setup slack = the data didn't arrive in time; the classic "timing failure." |
| **Hold slack** | Checked against the *same* clock edge that launched the data — guards against data racing through too fast. Independent of clock frequency. |
| **Logic levels** | Count of combinational LUT stages between two registers on a path. The primary lever you control in RTL — fewer levels between registers at a given frequency is the single biggest thing an RTL author can do to help timing closure. |
| **Clock skew** | Difference in clock arrival time at the launch vs. capture register. UltraScale+ clock regions and MMCM/PLL phase settings both affect this; large skew eats directly into setup slack budget. |
| **Clock uncertainty** | Margin Vivado reserves for jitter and skew it can't otherwise model precisely; shows up as a fixed subtraction from your period budget on every path — this is part of why the "logic levels" budget in `clock-family-reference.md` is conservative rather than a naive period/delay division. |
| **Multicycle path (MCP)** | A `set_multicycle_path` exception telling the tool a specific path is allowed N cycles instead of 1 to reach its destination — legitimate when the *design* only needs the data every N cycles (e.g. a slow control update into a fast pipeline), not a workaround for a path that's simply too slow. |
| **False path** | A `set_false_path` exception marking a path as functionally never sensitized or crossing an async boundary handled by a synchronizer — tells the tool to stop timing it at all. Misusing this to silence a real violation is the single most common way "closed" timing hides a live bug. |
| **`-datapath_only` max delay** | `set_max_delay -datapath_only` constrains a path's data arrival without also constraining clock skew between the two registers — the standard way to bound a CDC path that a synchronizer already protects functionally. |
| **Path group** | Vivado's bucketing of timing paths by clock domain (and by exception scope). `report_timing_summary` reports WNS/TNS per group — always check every group, not just the first one printed. |
| **Pblock** | A `create_pblock` floorplanning constraint that confines a hierarchical instance to a physical region of the die, used to reduce placement/routing distance (and therefore delay) for congestion- or skew-sensitive logic. |
| **MMCM / PLL phase** | Mixed-Mode Clock Manager / Phase-Locked Loop primitives that generate on-chip clocks with controlled phase and frequency relationships; phase-shifting an MMCM output is a legitimate way to trade skew between two related clock domains. |
| **Retiming** | Moving register boundaries across combinational logic (by tool `phys_opt_design -retime` or by hand in RTL) to rebalance logic levels between pipeline stages without changing function — the primary automated lever for closing marginal paths after placement. |
| **QoR** (Quality of Results) | Umbrella term for timing/utilization/power outcome of a synthesis+implementation run; "QoR playbook" means a decision procedure for improving these outcomes. |
