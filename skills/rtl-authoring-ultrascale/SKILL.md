---
name: rtl-authoring-ultrascale
description: "Use when writing or reviewing SystemVerilog/Verilog RTL targeting Xilinx UltraScale/UltraScale+ parts, or when synthesis timing/utilization quality depends on coding style. Trigger phrases: 'DSP48E2 inference', 'URAM inference', 'BRAM inference', 'retiming-friendly RTL', 'pipeline this datapath', 'CDC synchronizer', 'reset synchronizer', 'UltraScale+ coding guidelines', 'why won't this infer a DSP', 'why won't this infer a BRAM'. Use for any RTL edit that could affect downstream timing closure."
---

# RTL authoring for UltraScale+

Coding style choices made here are the cheapest lever on the whole lifecycle for fixing timing later — a well-pipelined, inference-friendly block synthesizes predictably; a poorly structured one turns every subsequent stage into a fight. Write against the interface contract from `../fpga-functional-spec/`, not from memory of "how this protocol usually works."

## Coding rules checklist (quick form — full list in references/coding-rules-checklist.md)

- Every register has a single clock and, if asynchronous, a single async reset — no mixed sync/async reset logic in one always block.
- No combinational loops; no latches from incomplete `case`/`if` assignment.
- Wide muxes and comparators get a registered output — don't let a "just one more input" mux grow into the critical path.
- Every CDC crossing uses a named pattern from `references/cdc-reset-patterns.md` — never a bare wire between clock domains "because it's basically stable."
- Pipeline depth is stated as a comment/parameter at the module boundary so the latency budget (`../fpga-functional-spec/references/latency-budget-worksheet.md`) can be checked against actual RTL, not assumed.
- DSP48E2/BRAM/URAM inference is *checked in the synthesis log*, not assumed from "the code looks like it should map" — see below.

## DSP48E2 inference

Use `references/dsp48e2-patterns.md` for the exact coding templates (pre-adder, cascade chain, pattern detect). The two failure modes worth flagging up front:
- **Broken cascade**: inserting any logic between cascaded DSP stages (even a mux) usually kicks the chain out of hard cascade routing and back onto fabric interconnect — instant timing risk at 644.53125 MHz-class frequencies where the fabric route budget is already tight (see `../../references/clock-family-reference.md`).
- **Missing input/output registers**: DSP48E2 has dedicated input (A/B/C/D), pipeline (M), and output (P) registers that cost zero extra latency if used but must be *directly* connected — extra combinational logic on those paths forces the tool to abandon the dedicated register and place a fabric flop instead, which is both worse timing and a wasted resource.

## BRAM/URAM inference

Use `references/bram-uram-inference.md` for exact templates. Read-before-write vs. write-before-read behavior must match the coded read-address-registration pattern exactly, or the tool infers fabric distributed RAM instead of a block/ultra RAM — a silent, expensive downgrade that only shows up in the utilization report, not a functional failure.

## CDC and reset patterns

Every clock domain crossing identified in the interface contract gets one of the named patterns in `references/cdc-reset-patterns.md` (2FF synchronizer, handshake, async FIFO) — chosen by data width and whether the value must be sampled coherently as a group. Reset synchronization (assert async, de-assert sync, one domain at a time) is in the same file; get this wrong and CDC bugs appear as rare, unreproducible hardware failures, not simulation failures.

## Retiming-friendly structure

Vivado's `phys_opt_design -retime` (see `../timing-closure-ultrascale/`) can move register boundaries automatically, but only across logic it's allowed to touch — don't defeat it with `(* dont_touch *)` or manual pipeline balancing unless there's a specific reason (e.g. a path that must stay exactly N cycles for protocol reasons). Prefer expressing "this needs to be fast" as clean, evenly-balanced combinational stages and let retiming redistribute registers, rather than hand-placing every flop.

## Verification hook

Once a block passes its own lint/inference checks, hand it to `../uvm-testbench-generation/` or `../cocotb-verification/` — RTL authoring and testbench authoring should happen against the same interface contract, not be reconciled after the fact.

## See also

`../fpga-functional-spec/` (source of the contract), `../timing-closure-ultrascale/references/qor-fix-playbook.md` (what to do when this RTL still fails timing after following these rules), `../ultra-low-latency-transceivers/` (GTY/GTM-facing datapath specifics).
