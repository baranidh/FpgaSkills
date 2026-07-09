# Debug core insertion (ILA / VIO)

## MARK_DEBUG attribute (pre-synthesis, RTL-driven)

```systemverilog
(* mark_debug = "true" *) logic [31:0] internal_state_reg;
(* mark_debug = "true" *) logic        fsm_error_flag;
```
Marks signals to survive synthesis optimization and remain probe-able. Cheap to add broadly during bring-up, but remove or gate behind a debug-build parameter before a final production bitstream — marked-debug signals prevent certain optimizations and add some logic/routing overhead.

## ILA insertion via Tcl (post-synthesis netlist insertion)

```tcl
open_run synth_1 -name synth_1
create_debug_core u_ila_0 ila
set_property C_DATA_DEPTH 4096 [get_debug_cores u_ila_0]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_0]

connect_debug_port u_ila_0/clk [get_nets core_clk]
set_property port_widths {32} [get_debug_ports u_ila_0/probe0]
connect_debug_port u_ila_0/probe0 [get_nets internal_state_reg[*]]

implement_debug_core
write_debug_probes -force debug_probes.ltx
```
Use this route when you need to add debug visibility to an already-built design without re-running synthesis, or when the signal to probe wasn't marked `mark_debug` in RTL ahead of time.

## VIO (Virtual I/O) for interactive stimulus/control during bring-up

```tcl
create_debug_core u_vio_0 vio
set_property C_NUM_PROBE_OUT 4 [get_debug_cores u_vio_0]
connect_debug_port u_vio_0/probe_out0 [get_nets debug_force_reset]
```
Useful for toggling a control signal (force a reset, override a config register) from Hardware Manager without recompiling — common during hardware bring-up to isolate whether a bring-up issue is in the reset sequence, a config register default, or the datapath itself.

## The `.ltx` file discipline

`write_debug_probes` produces the `.ltx` probes file that Hardware Manager needs to map bitstream probe positions back to signal names. **A `.ltx` file only matches the exact bitstream it was generated alongside** — loading a mismatched `.ltx`/`.bit` pair produces either an error or, worse, silently-wrong-looking probe data. Name/version them together (same filename stem, committed or archived together) rather than treating `.ltx` as an afterthought.

## Trigger setup for a specific bring-up hypothesis

Set the ILA trigger condition to the specific behavior under investigation (e.g. `fsm_error_flag == 1` or a specific counter value) rather than free-running capture — free-running capture at 322.265625/644.53125 MHz-class frequencies fills the ILA's limited depth (`C_DATA_DEPTH`) in a tiny fraction of a second, making it very unlikely to have captured the moment of interest without a targeted trigger.
