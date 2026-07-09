# UVM vs. cocotb decision guide

Not mutually exclusive at the project level, but pick one per block — don't build two divergent testbenches (and two divergent reference models that can silently drift apart) for the same DUT.

## Favor SV/UVM (`../../uvm-testbench-generation/`) when...

- The project/team's existing verification IP, sequence libraries, or scoreboards are already SV/UVM, and reuse outweighs a rewrite.
- You need UVM-specific mechanisms directly: the factory/override system for swapping components per test without touching the environment, `uvm_config_db`-style hierarchical configuration, or a virtual sequence layered across many interacting agents in a complex SoC-level environment.
- The commercial simulator's UVM-specific debug tooling (transaction-level debug, built-in UVM-aware waveform annotation) is part of the team's existing debug workflow.
- Coverage and verification sign-off tooling in the existing project pipeline expects SV coverage databases (e.g. integrated into an existing merge/report pipeline that's SV-specific).

## Favor cocotb (this skill) when...

- Faster iteration matters more than reuse of existing SV infrastructure — no compile step for the testbench itself (only the RTL), and Python's edit-run cycle is typically faster than SV recompilation for testbench-only changes.
- A reference model already exists in Python (or NumPy/SciPy, existing DSP/protocol libraries) and reimplementing it in SV would be pure duplication with drift risk.
- The project wants to run on Verilator for cost/license-free CI, and doesn't need full commercial-simulator-only SV constructs for the testbench layer.
- The team's verification engineers are more fluent in Python than SV, and the block's complexity doesn't specifically need UVM's factory/config-db machinery (e.g. a single block-level testbench rather than a large multi-agent SoC environment).

## Mixed strategy (legitimate, not a compromise)

A DUT can have a full UVM regression environment for sign-off coverage closure, and a separate lightweight cocotb smoke test for fast local iteration during RTL bring-up — as long as both are built from the same interface contract (`../../fpga-functional-spec/`) and neither reference model is allowed to silently diverge from the other. If they do diverge, that's a bug in one of the two testbenches, not a natural consequence of using two languages.

## What doesn't change either way

The functional coverage closure workflow (`../../functional-coverage-closure/references/closure-workflow.md`), the SVA assertion discipline (`../../simulation-workflow/references/sva-patterns.md`), and the waveform/log triage method (`../../simulation-workflow/references/waveform-triage-checklist.md`) all apply identically regardless of which testbench language drives the simulation.
