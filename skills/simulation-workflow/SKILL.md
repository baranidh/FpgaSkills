---
name: simulation-workflow
description: "Use when running, debugging, or triaging SystemVerilog simulations with Vivado xsim, Questa, or VCS, writing SVA assertions, building regression scripts, or reading waveforms/UVM_INFO/UVM_ERROR logs. Trigger phrases: 'run simulation', 'xsim', 'Questa', 'VCS regression', 'SVA assertion', 'waveform debug', 'UVM_ERROR triage', 'why is my testbench hanging', 'regression script'. Use for simulate-and-debug activity, distinct from writing the testbench components themselves."
---

# Simulation workflow

This is the run-and-debug layer on top of a testbench already built by `../uvm-testbench-generation/` or `../cocotb-verification/` — if the testbench doesn't exist yet, go build it first.

## Tool selection

| Simulator | Typical invocation | Notes |
|---|---|---|
| Vivado xsim | `xvlog`/`xelab`/`xsim` (or `vivado -mode batch -source sim.tcl`) | Bundled with Vivado, no separate license; good default when the project is already Vivado-centric and doesn't need advanced UVM debug features. |
| Questa | `vlog` + `vopt` + `vsim` | Strong UVM debug/coverage tooling; typical choice for larger verification teams; requires a Mentor/Siemens license. |
| VCS | `vcs` + simv | Strong performance on large regressions; requires a Synopsys license. |

Pick based on what's already licensed on the project, not on a default habit — the RTL/testbench should be simulator-portable (avoid vendor-specific extensions outside what UVM/SV standardizes) so switching later isn't a rewrite.

## SVA assertions (full patterns in references/sva-patterns.md)

Use assertions for invariants that should hold on every cycle, independent of any specific test's stimulus — e.g. "valid must not be asserted with X data," "ready must not depend combinationally on valid in a way that creates a false handshake," "a counter must never exceed its documented max." These catch violations regardless of which test happened to be running, which is strictly more coverage-efficient than hoping a scoreboard check happens to catch the same thing. Use `disable iff (reset)` on every concurrent assertion — an assertion that fires during reset because signals are still settling is a false positive that trains people to ignore assertion failures.

## Regression scripts

Use `references/regression-script-template.tcl` as the starting point for a multi-seed batch regression runner. Key discipline: log every seed used per run so a failure is reproducible by re-running that exact seed, not just "something failed somewhere in the last 500 runs."

## Waveform and log triage (full flow in references/waveform-triage-checklist.md)

When a test fails, triage in this order — cheapest signal first:
1. Grep the log for `UVM_ERROR`/`UVM_FATAL` and the surrounding `UVM_INFO` context — often enough to identify the failing scoreboard comparison or assertion without opening a waveform at all.
2. If the failure is a scoreboard mismatch, find the specific transaction's timestamp/sequence number and open the waveform at that point, not from time zero.
3. Check assertion firings even if not fatal to the test's final `UVM_ERROR` count — an assertion firing on an unrelated signal near the time of failure is often the actual root cause the scoreboard mismatch is a downstream symptom of.
4. If the test hangs (no failure, no completion), suspect a scoreboard/monitor waiting on a `get()` that will never arrive — check for a dropped transaction on one side (see the scoreboard's mismatch/hang distinction in `../uvm-testbench-generation/references/templates/scoreboard.sv`) before assuming the DUT itself is deadlocked.

## See also

`../functional-coverage-closure/` (the merge/rank step consumes coverage databases these regression runs produce), `../rtl-authoring-ultrascale/` (when a simulation failure traces back to an RTL bug rather than a testbench bug).
