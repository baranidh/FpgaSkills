---
name: market-order-entry-conveyor
description: "Use when building an ultra-low-latency market/order-entry gateway on FPGA and the user wants the full spec-to-simulation conveyor: capturing a binary order-entry message spec as an interface contract, generating a low-latency RTL framer/parser, generating a cocotb testbench with protocol-accurate stimulus, wiring functional coverage, and running simulation with tick-to-trade latency measurement. Trigger phrases: 'market order entry', 'order entry protocol', 'order entry gateway FPGA', 'exchange gateway FPGA', 'spec to simulation conveyor', 'tick-to-trade', 'FPGA trading latency'. This is a capstone worked example chaining the other skills in this library into one pipeline, not a substitute for any single stage's own skill."
---

# Market order-entry conveyor: spec -> RTL -> TB -> sim, worked end to end

**Read this first**: this skill uses a generic, illustrative binary order-entry message format to demonstrate the pipeline method. It is deliberately **not** a reproduction of any specific exchange's certified protocol (not OUCH, not FIX/FAST, not SBE, not Pillar, not iLink). A real gateway must be built against the actual exchange's published, certified specification — use this skill for the *pipeline methodology* (how to chain the other skills together) and substitute the real spec's field layout into step 1 before writing production RTL.

## Why this exists

Market order-entry gateways are a canonical ultra-low-latency FPGA application: a fixed-format binary message arrives over a transceiver, must be parsed and acted on (or forwarded) in as few cycles as possible, and every stage from spec to bitstream is timing- and latency-sensitive in a way that rewards exactly the discipline the rest of this library builds — this skill is the worked example that chains it all together instead of invoking each stage ad hoc.

## The conveyor (five stages, each handing off to the next)

1. **Capture the message/field layout as an interface contract** using `../fpga-functional-spec/references/interface-contract-template.md`, filled in with the generic layout in `references/message-field-table-template.md` (or the real exchange spec, in production). Every field's offset, width, and endianness must be nailed down before RTL — this is the step where "the parser is basically the same as X" ambiguity gets removed.
2. **Generate a single-cycle, cut-through framer/parser RTL skeleton** using the low-latency patterns from `../rtl-authoring-ultrascale/` and the cut-through principle from `../ultra-low-latency-transceivers/` — see `references/framer-parser-rtl-pattern.md`. Fixed-offset fields get extracted combinationally/in one cycle wherever the layout allows it; only variable-length or checksum-dependent fields justify an extra pipeline stage.
3. **Generate a cocotb testbench** (`../cocotb-verification/`) with a protocol packet generator and a Python reference-model scoreboard — see `references/order-entry-cocotb-testbench.py`. cocotb is the natural fit here specifically because a reference-model message encoder/decoder is easy to express as plain Python and easy to keep in lockstep with a test packet generator.
4. **Wire functional coverage** (`../functional-coverage-closure/`, using the cocotb-coverage path from `../cocotb-verification/references/cocotb-coverage-patterns.py`) over message types, field boundary values, and malformed/reject cases — see `references/order-entry-coverage-model.md`.
5. **Run simulation and produce a tick-to-trade latency histogram** — see `references/tick-to-trade-latency-methodology.md`, which extends `../ultra-low-latency-transceivers/references/latency-budget-accounting.md`'s per-stage method with a concrete measurement technique.

## What "done" looks like for this pipeline

Same gates as `../fpga-dev-lifecycle/`, applied specifically here: interface contract complete (step 1), RTL lint-clean with confirmed single-cycle parse of fixed-offset fields (step 2), testbench passing directed tests for every message type and every malformed-input case (step 3), functional coverage closed on message-type x error-condition crosses (step 4), and a measured best-case and worst-case tick-to-trade latency that matches the budget from `../fpga-functional-spec/references/latency-budget-worksheet.md` (step 5) — not just "simulation passes."

## Chaining, not replacing

Every step above is a pointer to an existing skill's method applied to this specific worked example — this skill intentionally does not re-explain interface contract methodology, RTL coding rules, cocotb architecture, or coverage closure workflow; it shows how those pieces click together for a message-based, latency-critical protocol. When something in a step needs deeper treatment than shown here, go to that step's linked skill directly.

## See also

`../fpga-functional-spec/`, `../rtl-authoring-ultrascale/`, `../cocotb-verification/`, `../functional-coverage-closure/`, `../ultra-low-latency-transceivers/`, `../timing-closure-ultrascale/` (once this parser needs to close timing at a specific 322/644 MHz-class frequency).
