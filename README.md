# FpgaSkills

A Claude Code skill library for the Xilinx UltraScale+ FPGA development lifecycle: functional spec correctness, RTL authoring, UVM and cocotb testbench generation, functional coverage closure, simulation, Vivado synthesis/implementation, timing closure at 322.265625 MHz and 644.53125 MHz clock families, bitstream generation and hardware bring-up, ultra-low-latency transceiver design, a market order-entry spec-to-simulation worked pipeline, and pcap-based TCP order-entry traffic analysis for replay-based verification.

## Install

As a Claude Code plugin, from any project:

```
/plugin marketplace add baranidh/FpgaSkills
/plugin install fpga-skills
```

Claude then picks up the relevant skill automatically based on what you ask — you don't invoke these by name.

## Skill catalog

| Skill | Purpose |
|---|---|
| `fpga-dev-lifecycle` | Orchestrator: routes "what's next"/lifecycle questions to the right stage skill; stage->skill->gate-criteria table. |
| `fpga-functional-spec` | Turns a spec/requirements doc into an unambiguous interface contract (signal timing, clock/reset domains, latency budget, error semantics) before any RTL is written. |
| `rtl-authoring-ultrascale` | SystemVerilog/Verilog coding patterns for UltraScale+: DSP48E2/BRAM/URAM inference, CDC/reset patterns, retiming-friendly pipelining, a timing-closure-blocking coding checklist. |
| `uvm-testbench-generation` | SV/UVM environment scaffolding: driver/monitor/scoreboard/sequence templates, reference-model integration, directed vs. constrained-random guidance. |
| `cocotb-verification` | Python-based verification (cocotb) as an alternative/complement to UVM: coroutine driver/monitor/scoreboard patterns, Makefile-based Verilator/xsim/Questa integration, `cocotb-coverage` functional coverage. |
| `functional-coverage-closure` | Covergroup/cross-coverage authoring (SV and cocotb-coverage), the run-merge-rank-close workflow, functional-vs-code-coverage distinction, waivers. |
| `simulation-workflow` | Running/debugging simulations (xsim/Questa/VCS), SVA assertion patterns, regression scripting, waveform/log triage. |
| `timing-closure-ultrascale` | The centerpiece: XDC authoring, 322.265625/644.53125 MHz clock math, a symptom-driven QoR fix playbook, Pblock floorplanning, timing report interpretation. |
| `synthesis-implementation-vivado` | Non-project batch Tcl flow, synthesis/implementation strategy selection, out-of-context synthesis, incremental compile, utilization report interpretation. |
| `bitstream-and-bringup` | Bitstream generation options, ILA/VIO debug core insertion, hardware bring-up checklist, a partial-reconfiguration pointer. |
| `ultra-low-latency-transceivers` | GTY/GTM configuration for the 322/644 MHz-class frequency families, cut-through datapath architecture, latency-budget accounting, Aurora/Interlaken/JESD204 worked examples. |
| `market-order-entry-conveyor` | Capstone worked example: chains the above into one spec-to-RTL-to-cocotb-TB-to-coverage-to-sim pipeline for an ultra-low-latency order-entry gateway, using a generic illustrative message format. |
| `pcap-traffic-analysis` | Analyzes real `.pcap` captures of TCP order-entry traffic: TCP stream reassembly, order-entry field decoding, order chain extraction with anomaly detection, capture-timestamp latency analysis (with an explicit accuracy caveat), and converting captured traffic into cocotb replay stimulus. |

## Lifecycle at a glance

```
spec --> RTL --> testbench (UVM or cocotb) <--> simulation <--> coverage closure
                                                                       |
                                                                       v
                              synthesis/implementation --> timing closure --> bitstream & bring-up
```

Stages 3-5 cycle (write test -> simulate -> find a coverage hole -> add test -> repeat); stages 6-7 cycle (implementation reveals a timing failure -> RTL/XDC change -> re-implement). See `skills/fpga-dev-lifecycle/SKILL.md` for entry/exit gate criteria per stage.

Once real traffic exists (a lab capture or hardware bring-up session), `pcap-traffic-analysis` closes the loop back into the coverage/simulation stages: anomalies found in real traffic become coverage goals, and decoded captures can be replayed as cocotb stimulus alongside synthetic tests.

## Known limitation

This library was authored without access to a live Vivado/simulator toolchain. The architectural principles, workflow ordering, and general engineering reasoning throughout are sound, but specific syntax, exact IP primitive names/parameters, and precise timing numbers (XDC constraint syntax, DSP48E2/GTY/GTM primitive details, exact clock-to-datapath-width mappings for specific IP cores) should get a toolchain- and documentation-verified pass — against Xilinx UG471 (UltraScale Architecture SLICE), UG903 (Constraints), UG974 (Transceivers), UG578 (GTY/GTM Transceivers), UG909 (Partial Reconfiguration), and the relevant IP product guides — before being relied on for a production design.

`market-order-entry-conveyor` additionally uses a deliberately generic, illustrative message format rather than any real exchange's certified protocol — see that skill's own disclosure before using it as a template for a production gateway.
