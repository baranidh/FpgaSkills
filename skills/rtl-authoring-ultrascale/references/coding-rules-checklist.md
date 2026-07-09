# RTL coding rules checklist

Each rule is annotated with what breaks downstream if it's violated. Use this as a review checklist, not just a style guide.

| Rule | Blocks timing closure if violated because... |
|---|---|
| One clock, one reset per always_ff block; no mixed sync/async in the same block | The tool can't cleanly map to a single register primitive's control set; often falls back to fabric logic emulating the missing control, adding a logic level. |
| No combinational loops; every `case`/`if` fully assigns all outputs on all branches | Incomplete assignment infers a latch, which has no place in a synchronous timing budget and behaves unpredictably under STA. |
| Registered outputs on wide muxes/comparators (>~4:1 or >~16 bits) | An unregistered wide mux sitting right before a register eats a large slice of the period in a single logic level, disproportionate to its apparent simplicity. |
| Every CDC crossing uses a named pattern (`cdc-reset-patterns.md`) with a matching XDC exception | Unconstrained or ad hoc crossings are either invisible to STA (false confidence) or force a same-domain-style constraint across an async boundary that can never actually close. |
| Pipeline depth stated at module boundary (comment or parameter) | Without a stated depth, the latency budget (`../../fpga-functional-spec/references/latency-budget-worksheet.md`) can't be checked against real RTL, and an extra register added for timing silently invalidates a latency claim upstream. |
| DSP48E2/BRAM/URAM inference confirmed in synthesis/utilization reports, not assumed from RTL shape | A silent fallback to fabric logic (LUT multiplier, distributed RAM) is both a resource and a timing surprise that only appears in reports, never as a functional failure. |
| No `(* dont_touch *)` / manual pipeline balancing without a stated reason | Blocks `phys_opt_design -retime` from rebalancing register placement automatically during timing closure — a legitimate escape hatch for protocol-timing-critical paths, but a common self-inflicted timing closure obstacle when used by default. |
| Wide arithmetic (>48 bits, wider than one DSP48E2) is explicitly structured as a cascade or explicitly pipelined, not left as a single wide combinational expression | The tool will map it somehow, but an unstructured wide add/compare tends to produce unpredictable logic-level counts that vary between synthesis runs/tool versions. |
| Every input from outside the block (especially from another clock domain or from off-chip) is treated as untrusted for combinational use | Combinational logic fed directly by an unsynchronized or externally-sourced signal is a common source of both CDC and glitch-related bugs; register it first. |
| Reset value of every register matches what downstream logic assumes at cycle 0 after reset release | A register that "doesn't need an explicit reset value because it'll be written before it's read" is a common source of X-propagation-masked bugs in simulation that become real bugs in hardware, where there is no X. |
