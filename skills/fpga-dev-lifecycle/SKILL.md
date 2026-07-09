---
name: fpga-dev-lifecycle
description: "Use when starting a new FPGA design task, when the user asks what stage a project should be at, wants the overall RTL-to-bitstream workflow, gate/sign-off criteria between stages, or which skill in this library applies to their current problem. Trigger phrases: 'FPGA development lifecycle', 'RTL to bitstream flow', 'what stage should I be at', 'design flow checklist', 'Vivado flow overview', 'sign-off criteria', 'what's next in this FPGA project'. Not for executing a specific stage — this routes to the stage-specific skill instead."
---

# FPGA development lifecycle (Xilinx UltraScale+)

This is the router for the rest of the library. Read this first when a task doesn't obviously belong to one stage, then hand off to the named skill for the actual work.

## Stage map

| Stage | Skill | Entry gate (don't start until...) | Exit gate (don't move on until...) |
|---|---|---|---|
| 1. Spec | `fpga-functional-spec` | Requirements/protocol doc exists | Interface contract has every signal's timing, every clock domain named + sourced, every reset documented, a per-stage latency budget, and defined backpressure/error semantics |
| 2. RTL | `rtl-authoring-ultrascale` | Interface contract signed off | RTL lints clean, DSP/BRAM/URAM inference confirmed in synth log, CDC crossings identified and protected |
| 3. Testbench | `uvm-testbench-generation` or `cocotb-verification` | RTL interfaces frozen | Driver/monitor/scoreboard operating against a reference model, directed tests for every spec'd behavior passing |
| 4. Coverage | `functional-coverage-closure` | Testbench running clean tests | Functional coverage ≥ target (commonly 100% of goals or an explicit waiver), code coverage reviewed for holes coverage alone won't catch |
| 5. Simulation | `simulation-workflow` | Coverage model wired in | Regression green across seeds, SVA assertions never fired outside expected error-injection tests |
| 6. Synthesis/Implementation | `synthesis-implementation-vivado` | Simulation-clean RTL | Utilization within budget, no unexpected critical warnings, checkpoint saved |
| 7. Timing closure | `timing-closure-ultrascale` | Post-route timing report available | WNS ≥ 0 and WHS ≥ 0 in every path group, no exceptions masking a real violation |
| 8. Bitstream & bring-up | `bitstream-and-bringup` | Timing closed | Bitstream generated with debug cores as needed, hardware bring-up checklist passed |
| (cross-cutting) | `ultra-low-latency-transceivers` | Any stage touching GTY/GTM or a 322/644 MHz-class datapath | Latency budget accounted for end-to-end |
| (cross-cutting) | `pcap-traffic-analysis` | Real captured traffic exists (lab tap, SPAN port, hardware bring-up) | Decoded/chain-extracted capture cross-checked against the RTL's expected behavior; anomalies fed back into coverage goals |
| (worked example) | `market-order-entry-conveyor` | Illustrates stages 1-5 chained into one automated pipeline for an ultra-low-latency order-entry gateway | — |

## How the loop actually runs

Stages 3-5 are not strictly linear — expect to cycle: write a test, run simulation, find a coverage hole, add a test, re-run, repeat until the stage-4 exit gate is met. Stages 6-7 also cycle: implementation reveals a timing failure, you go back to RTL (stage 2) or add an XDC exception, then re-run implementation. Treat the table's ordering as gate *sequence*, not a single-pass waterfall.

`ultra-low-latency-transceivers` isn't a discrete stage — pull it in whenever a block touches a GTY/GTM transceiver or must hit a 322.265625/644.53125 MHz-class frequency, from spec through timing closure. `pcap-traffic-analysis` isn't a stage either — it's a validation activity that only becomes available once real captured traffic exists (a lab capture, or hardware bring-up), and it feeds back into stage 4 (coverage) when it surfaces a real-traffic case the coverage model didn't yet cover.

## Picking a skill when it's ambiguous

- "Why won't this synthesize/infer a DSP" → `rtl-authoring-ultrascale`, not `synthesis-implementation-vivado`.
- "Why is timing failing" → `timing-closure-ultrascale`. "Why is utilization too high" or "how do I run Vivado in batch mode" → `synthesis-implementation-vivado`.
- "Write a testbench" → `uvm-testbench-generation` (SystemVerilog/UVM) or `cocotb-verification` (Python) — see that pair's cross-linked decision guide.
- "My simulation hangs / a UVM_ERROR fired / how do I read this waveform" → `simulation-workflow`, once a testbench already exists.
