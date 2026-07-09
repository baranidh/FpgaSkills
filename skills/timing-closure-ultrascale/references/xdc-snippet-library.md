# XDC snippet library

Copy-paste starting points. Always confirm exact syntax/options against the Vivado version in use (`Vivado Design Suite User Guide: Using Constraints`, UG903) before relying on these in a production constraint set — see the README's known-limitations note.

## Clock definition

```tcl
create_clock -name core_clk -period 3.10303 [get_ports core_clk_p]
create_clock -name fast_clk -period 1.55152 [get_ports fast_clk_p]

# Generated clock from an MMCM/PLL output
create_generated_clock -name proc_clk -source [get_pins mmcm_inst/CLKIN1] \
    -multiply_by 1 -divide_by 2 [get_pins mmcm_inst/CLKOUT0]
```

## Clock groups (declare unrelated clocks as truly asynchronous)

```tcl
set_clock_groups -asynchronous \
    -group [get_clocks core_clk] \
    -group [get_clocks fast_clk]
```
Only use `-asynchronous` when the two clocks genuinely have no fixed phase relationship (e.g. independent free-running oscillators, or a recovered clock vs. a local reference) — declaring related clocks asynchronous by mistake hides real timing relationships the design actually depends on.

## Multicycle path

```tcl
# Setup: destination register only needs to sample every N cycles
set_multicycle_path -setup 4 -from [get_cells slow_ctrl_reg] -to [get_cells fast_pipe_reg]
# Hold: must match, typically setup-1, unless the actual launch/capture relationship differs
set_multicycle_path -hold 3 -from [get_cells slow_ctrl_reg] -to [get_cells fast_pipe_reg]
```
Both setup and hold multicycle values must be specified together and reasoned about jointly — specifying only the setup value and leaving hold at its default is a common source of an unexpected hold requirement that doesn't match the design's actual intent.

## False path

```tcl
set_false_path -from [get_cells async_source_reg] -to [get_cells sync_ff1]
# Or scoped by clock, when an entire clock relationship is genuinely irrelevant:
set_false_path -from [get_clocks slow_debug_clk] -to [get_clocks core_clk]
```

## Max delay for CDC datapaths (protected by a synchronizer already)

```tcl
set_max_delay -datapath_only 3.0 \
    -from [get_cells sync_ff2] -to [get_cells consumer_reg]
```
`-datapath_only` is the key option: it bounds data arrival time without also constraining clock-to-clock skew between the two registers, which is correct for a path a synchronizer already protects functionally — using a plain `set_max_delay` (without `-datapath_only`) here over-constrains and can make the tool work to close a skew relationship that doesn't matter.

## Input/output delay (I/O timing to an external device)

```tcl
create_clock -name ext_ref_clk -period 3.10303 [get_ports ext_ref_clk]
set_input_delay  -clock ext_ref_clk 1.2 [get_ports data_in[*]]
set_output_delay -clock ext_ref_clk 0.8 [get_ports data_out[*]]
```
Get these numbers from the external device's datasheet timing, not a guess — an unconstrained or under-constrained I/O boundary is invisible to STA in the same way an unconstrained CDC path is.

## Physical constraints referenced from timing closure

```tcl
# ASYNC_REG equivalent enforced structurally via a physical constraint,
# in addition to the (* ASYNC_REG = "TRUE" *) RTL attribute:
set_property ASYNC_REG TRUE [get_cells {sync_ff1_reg sync_ff2_reg}]
```
