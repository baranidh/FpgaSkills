---
name: uvm-testbench-generation
description: "Use when scaffolding a SystemVerilog/UVM testbench, or writing driver/monitor/scoreboard/sequence components, reference models, or constrained-random/directed tests for an RTL block. Trigger phrases: 'UVM testbench', 'UVM environment', 'driver and monitor', 'scoreboard', 'sequence library', 'reference model checker', 'constrained random test', 'directed test'. Use after RTL interfaces are frozen and before simulation runs begin. For Python-based testbenches see cocotb-verification instead."
---

# UVM testbench generation

Build the environment against the interface contract from `../fpga-functional-spec/`, not against the RTL's internal state — a testbench that only checks what the RTL happens to do isn't verification.

## Environment topology (full detail in references/env-topology.md)

```
uvm_test
  -> uvm_env
       -> uvm_agent (per interface: driver + monitor + sequencer)
       -> reference_model  (predicts expected output from input transactions)
       -> scoreboard        (compares monitor-observed output against reference model)
       -> coverage subscriber (see functional-coverage-closure)
```

One agent per physical interface (input side, output side, any side-band/config interface). Keep driver and monitor separate even on the same interface — the monitor must be able to observe a transaction whether it came from this testbench's own driver or from surrounding logic, which matters the moment this block is reused in a larger integration environment.

## Component responsibilities

- **Driver**: converts sequence-item transactions into pin wiggles, respecting the interface contract's exact timing (valid/ready cycles, not just "eventually assert valid").
- **Monitor**: passively observes the interface and reconstructs transactions — must never drive a signal, so it stays reusable when this block sits inside a larger environment.
- **Sequencer + sequence library**: directed sequences for every explicitly spec'd behavior (see the functional spec's corner-case list), plus constrained-random sequences for everything else. Directed tests prove specific spec'd behavior works; constrained-random finds what you didn't think to direct.
- **Reference model**: a behavioral (non-RTL) implementation of the spec'd function — predict-then-compare, not "check a few known-good outputs." Build it from the same interface contract, ideally by someone other than the RTL author, so the same misreading of an ambiguous spec doesn't propagate into both.
- **Scoreboard**: compares monitor output against reference model prediction, transaction-by-transaction; flag both mismatches and *unexpected extra* or *missing* transactions, not just field-level mismatches on matched pairs.

## Directed vs. constrained-random

Use directed tests to prove every corner case enumerated in the functional spec (reset mid-transaction, back-to-back zero-idle transactions, arbitration ties) passes deterministically. Use constrained-random, seeded and re-run across many seeds, to find behavior nobody explicitly directed — the coverage model in `../functional-coverage-closure/` is what tells you when constrained-random has explored enough of the space to stop being useful on its own.

## Templates

Skeleton `.sv` files for each component are in `references/templates/` (`driver.sv`, `monitor.sv`, `scoreboard.sv`, `sequence.sv`) — copy and adapt rather than writing from scratch each time, so structure stays consistent across blocks in the same project.

## cocotb as an alternative

If the project prefers Python (faster iteration, easier reference-model reuse from existing Python/NumPy models, open-source simulator compatibility via Verilator, no SV testbench license needed), use `../cocotb-verification/` instead — see that skill's `uvm-vs-cocotb-decision-guide.md` for the actual tradeoffs rather than picking by habit. The two are not mutually exclusive at the project level: a DUT can have a UVM environment for full regression and a cocotb smoke test for fast local iteration, as long as both check against the same interface contract and reference-model logic isn't duplicated and allowed to drift between them.

## See also

`../functional-coverage-closure/` (coverage model lives in the monitor/subscriber built here), `../simulation-workflow/` (running and debugging what this skill builds).
