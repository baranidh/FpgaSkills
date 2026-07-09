---
name: fpga-functional-spec
description: "Use before writing any RTL, when the user provides a protocol spec, requirements doc, or a vague feature request that needs to become an unambiguous microarchitecture. Trigger phrases: 'functional spec', 'interface contract', 'turn this spec into RTL', 'define the microarchitecture', 'latency budget', 'clock domain plan', 'reset strategy', 'define done criteria', 'what does correct mean here'. Use whenever signal timing, valid/ready semantics, or reset behavior is ambiguous before implementation starts."
---

# Functional spec correctness

Most "the RTL doesn't match the spec" bugs are actually "the spec was ambiguous and RTL made a silent choice" bugs. This skill's job is to remove every silent choice before RTL exists — not to write RTL.

## Definition of done

A functional spec is ready for RTL when every one of these is true. Treat any "no" as the next thing to fix, not a note for later:

1. **Every signal** has direction, width, and its exact timing relationship to the clock (which edge, combinational vs. registered, valid/ready or valid-only semantics).
2. **Every clock domain** is named, with its source (external pin, MMCM/PLL output, recovered clock from a transceiver) and nominal frequency stated. See `../../references/clock-family-reference.md` if a domain is 322.265625/644.53125 MHz-class.
3. **Every reset** is documented: which domain it lives in, synchronous or asynchronous assertion, synchronous de-assertion requirement, and what state each block must reach before de-assertion is legal.
4. **A latency budget** exists per pipeline stage (not just an end-to-end number) — see `references/latency-budget-worksheet.md`.
5. **Backpressure and error semantics are defined**: what happens when a downstream consumer isn't ready, what constitutes a malformed/illegal input, and whether it's dropped, flagged, or must never occur (and who guarantees that).
6. **Corner cases are enumerated**, not implied: reset during an in-flight transaction, back-to-back transactions with zero idle cycles, simultaneous multi-channel arbitration ties.

## Working method

1. Start from whatever the user gives you (a protocol doc, a paragraph, a diagram) and fill in `references/interface-contract-template.md` field by field. Do not skip a field by inventing a "reasonable default" silently — flag it as an open question back to the user; a wrong silent assumption here is the most expensive bug class in the whole lifecycle because it survives all the way to hardware bring-up looking correct.
2. Build the per-stage latency table using `references/latency-budget-worksheet.md`, especially for anything claimed to be "ultra-low latency" — a spec that says "low latency" without a cycle-accounted budget isn't actually specified yet.
3. Draw (in text/ASCII, in the contract doc) the clock domain topology: every domain, its source, and every point data crosses between domains. Every crossing found here becomes a required CDC pattern in `rtl-authoring-ultrascale`.
4. Hand the finished contract to `rtl-authoring-ultrascale` for implementation and to `uvm-testbench-generation`/`cocotb-verification` for verification planning — both should be written against this contract, not against the RTL.

## Anti-patterns to flag back to the user

- "Standard AXI-Stream, you know how it works" — width, `TUSER`/`TLAST`/`TKEEP` usage, and backpressure latency (how many cycles after de-asserting `tready` must `tvalid` stop) still need to be nailed down; AXI-Stream is a signal list, not a full timing contract.
- A latency number with no per-stage breakdown — can't be verified, can't be budgeted against when something later needs an extra pipeline stage.
- A reset strategy described only as "active-low reset" with no statement of sync/async or which domain it's native to — this is the single most common source of CDC bugs downstream.

## See also

`../rtl-authoring-ultrascale/` (implements this contract), `../ultra-low-latency-transceivers/` (if any interface is transceiver-facing), `../market-order-entry-conveyor/` (a full worked example of this template applied to a message-based protocol).
