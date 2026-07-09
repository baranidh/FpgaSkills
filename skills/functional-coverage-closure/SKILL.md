---
name: functional-coverage-closure
description: "Use when authoring SystemVerilog covergroups/cross coverage, triaging coverage holes, merging regression coverage databases, or deciding whether coverage closure is done. Trigger phrases: 'functional coverage', 'covergroup', 'cross coverage', 'coverage closure', 'coverage holes', 'coverage waiver', 'merge coverage database', 'code coverage vs functional coverage'. Use once simulation is running and coverage collection is enabled."
---

# Functional coverage closure

Coverage answers "have we exercised the behaviors the spec cares about," which is a different question from "does the code work" — a scoreboard with zero mismatches and empty coverage just means nothing has been tried yet.

## Functional vs. code coverage

**Code coverage** (line/branch/toggle/FSM state) tells you what RTL *executed*. **Functional coverage** (covergroups) tells you what *scenarios from the spec* were exercised. Neither substitutes for the other: 100% code coverage with no functional coverage means every line ran at least once but says nothing about whether the interesting combinations (spec corner cases, protocol edge conditions) were hit; 100% functional coverage with low code coverage usually means the coverage model itself missed something the RTL implements. Close both, and treat a code-coverage hole in logic your functional model claims is fully covered as a signal the functional model itself has a gap.

## Covergroup authoring (full patterns in references/covergroup-patterns.md)

Write covergroups from the interface contract's signal table and corner-case list (`../fpga-functional-spec/`), not from reading the RTL — a coverage model derived from the RTL will only ever confirm the RTL does what the RTL does, not what the spec requires. At minimum:
- A coverpoint per field with meaningful value classes (not just "any value" — bin the legal ranges, boundary values, and known-illegal values separately).
- Cross coverage between fields that interact (e.g. transaction type x error condition x backpressure state) — most real bugs live in combinations, not single fields in isolation.
- Explicit `illegal_bins` for values the spec says can never occur, so the scoreboard's silence on them is backed by evidence they were never even generated, not just never observed.

## Closure workflow (full detail in references/closure-workflow.md)

1. Run the regression with coverage enabled across many random seeds (directed tests contribute too, but seed diversity is what fills the constrained-random-reachable bins).
2. Merge per-run coverage databases into one cumulative view.
3. Rank remaining holes — don't fix them in database order; group by root cause (e.g. "no seed ever produced back-to-back errors on two consecutive transactions" is one root cause behind possibly many individual empty bins).
4. For each hole: either add/adjust a directed test, relax a sequence's constraints to make the case reachable by constrained-random, or write a documented waiver if the case is provably unreachable in this configuration (state why, not just that it's inconvenient to hit).
5. Re-run and re-merge. Repeat until every goal is closed or waived — "we'll come back to it" holes have a way of surviving into production.

## When cocotb is the testbench language

If verification is being done in `../cocotb-verification/` instead of SV/UVM, the same closure workflow applies using `cocotb-coverage`'s `CoverPoint`/`CoverCross` decorators — see that skill's `references/cocotb-coverage-patterns.py`. Don't build two divergent coverage models for the same block; pick one verification language per block and keep its coverage model as the single source of truth.

## See also

`../uvm-testbench-generation/references/env-topology.md` (coverage subscriber wiring), `../simulation-workflow/` (running the regression that generates the coverage data), `../market-order-entry-conveyor/references/order-entry-coverage-model.md` (a worked coverage model example).
