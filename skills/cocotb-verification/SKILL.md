---
name: cocotb-verification
description: "Use when the user wants Python-based FPGA verification via cocotb, as an alternative or complement to SystemVerilog/UVM. Trigger phrases: 'cocotb', 'python testbench', 'cocotb-coverage', 'cocotb regression', 'pytest simulation', 'Verilator cocotb', 'coroutine-based testbench', 'python driver monitor scoreboard'. Use for coroutine-based drivers/monitors, cocotb-coverage functional coverage in Python, and Makefile-based simulator integration (Verilator/xsim/Questa/VCS)."
---

# cocotb verification

Python-based verification for the same DUT and interface contract `../uvm-testbench-generation/` targets — pick one language per block (see `references/uvm-vs-cocotb-decision-guide.md`), don't split a single block's verification across both.

## Architecture

cocotb drives simulation from Python coroutines that get a handle to the DUT's ports directly (no SV testbench wrapper required for basic access, though a thin SV/Verilog top-level is still typical for clock/reset generation and interface bundling). Core building blocks:
- **`dut` handle**: attribute access to every port (`dut.data_in.value = 0x42`), hierarchical access into internal signals for whitebox checks when needed.
- **Triggers**: `RisingEdge(dut.clk)`, `FallingEdge(dut.clk)`, `Timer(10, units="ns")`, `ReadOnly()` (wait until all deltas in the current time step have settled, before sampling — the Python equivalent of sampling in the observed region), `Combine`/`First` for waiting on multiple conditions.
- **Coroutines** (`async def`) replace SV `always`/`initial` blocks and UVM's `run_phase` tasks — a driver is just an `async def` loop that awaits `RisingEdge(dut.clk)` and assigns signal values.

## Makefile-based simulator integration

Templates in `references/makefile-templates/` for Verilator, Vivado xsim, and Questa. Common shape:

```makefile
TOPLEVEL_LANG = verilog
SIM ?= verilator
TOPLEVEL = dut_top
MODULE = test_dut          # the Python file containing your cocotb tests
VERILOG_SOURCES = $(shell find ../rtl -name "*.sv")

include $(shell cocotb-config --makefiles)/Makefile.sim
```
`SIM=verilator` gives fast, open-source, license-free iteration (good default for local development and CI); switch to `SIM=xsim`/`questa`/`vcs` when a feature Verilator doesn't support is needed (certain SV constructs, mixed-language sims, or vendor-specific primitives that need to actually simulate rather than just synthesize).

## Driver / monitor / scoreboard patterns

Full templates in `references/driver-monitor-templates.py`. The same responsibilities as the UVM equivalents (`../uvm-testbench-generation/references/env-topology.md`) apply: driver converts transactions to pin wiggles respecting the interface contract's exact timing, monitor passively observes, scoreboard compares against a reference model. The Python equivalent of a reference model is often just a plain Python function or class — this is cocotb's biggest practical advantage when the reference behavior is naturally expressed as software (e.g. a checksum, a protocol state machine, or reusing an existing Python/NumPy golden model that already exists outside the FPGA project).

## Functional coverage: `cocotb-coverage`

Full patterns in `references/cocotb-coverage-patterns.py`. `cocotb_coverage.coverage.CoverPoint`/`CoverCross` decorators provide the same functional-coverage concept as SystemVerilog covergroups (see `../functional-coverage-closure/`) — bins, cross coverage, and a coverage database that can be reported and checked against a closure target. Apply the exact same closure workflow (`../functional-coverage-closure/references/closure-workflow.md`): derive coverage goals from the spec's corner-case list, not from the RTL, and don't skip merge/rank/close just because the mechanics are Python instead of SV.

## Mixing with SVA

SVA assertions can still run underneath a cocotb testbench (bound into the DUT exactly as in `../simulation-workflow/references/sva-patterns.md`) since assertions are a simulator/RTL-level feature independent of which language drives the testbench — cocotb doesn't replace the value of always-on invariant checking, it replaces the driver/monitor/scoreboard layer.

## See also

`../uvm-testbench-generation/` (the SV/UVM alternative and its decision guide), `../functional-coverage-closure/` (closure workflow shared across both), `../simulation-workflow/` (triage discipline applies whichever language the testbench is written in), `../market-order-entry-conveyor/` (uses cocotb as its verification layer in the worked pipeline).
