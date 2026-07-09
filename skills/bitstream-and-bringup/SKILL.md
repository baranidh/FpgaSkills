---
name: bitstream-and-bringup
description: "Use when generating a Vivado bitstream, choosing configuration mode/memory, inserting ILA/VIO debug cores or MARK_DEBUG probes, or bringing up a design on hardware. Trigger phrases: 'generate bitstream', 'write_bitstream', 'config mode', 'configuration memory', 'ILA', 'VIO', 'MARK_DEBUG', '.ltx probes', 'hardware bring-up', 'readback verify', 'partial reconfiguration'. Use as the final stage after timing closure, or when debugging a design already on hardware."
---

# Bitstream generation and hardware bring-up

The final stage — only reachable once `../timing-closure-ultrascale/` reports WNS/WHS ≥ 0 across every path group. Generating a bitstream from a design that hasn't closed timing produces hardware that may work by luck under specific voltage/temperature conditions and fail unpredictably otherwise; don't skip the gate.

## Bitstream generation options

```tcl
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property CONFIG_VOLTAGE 1.8 [current_design]
set_property BITSTREAM.CONFIG.UNUSEDPIN Pullup [current_design]
write_bitstream -force top_module.bit
```
Confirm `CONFIG_VOLTAGE`, compression, and unused-pin behavior against the actual board/config-memory combination — these aren't universal defaults, they depend on the specific configuration memory and board design. See `references/debug-core-insertion.md` and `references/bringup-checklist.md` for the full workflow.

## Configuration mode and memory

Configuration mode (JTAG, Master SPI, Master SelectMAP, etc.) and configuration memory part must be declared before bitstream generation for modes other than JTAG-only bring-up (`CONFIG_MODE`, `BITSTREAM.CONFIG.*` properties) — an interactive JTAG-only bring-up doesn't need this, but any design intended to boot standalone from flash does. Get the config memory part number from the board design, not assumed from the FPGA part alone.

## Debug core insertion (full workflow in references/debug-core-insertion.md)

Mark internal signals for debug visibility with `MARK_DEBUG` (RTL attribute) before synthesis, or insert ILA/VIO cores directly in the implemented netlist via the Vivado IP integrator/`create_debug_core` Tcl flow after the fact. Either way, the `.ltx` probes file generated alongside the bitstream is required by Vivado Hardware Manager to correlate probe names back to signal names — losing track of which `.ltx` matches which `.bit` is a common, entirely avoidable source of bring-up confusion; name and version them together.

## Hardware bring-up checklist (full checklist in references/bringup-checklist.md)

In order: power present at expected rails, reference clock present and at expected frequency (measure it — don't assume the oscillator is right just because it's populated), configuration DONE pin asserts, no configuration CRC/readback error, ILA shows expected reset sequence and idle-state behavior before applying any real stimulus.

## Partial reconfiguration

Out of scope for a full treatment here — see `references/partial-reconfiguration-notes.md` for a short pointer to the relevant Vivado flow (`UG909`) if a design specifically needs it; it's a substantially larger topic (reconfigurable partitions, static/PR region floorplanning) than this skill covers in depth.

## See also

`../timing-closure-ultrascale/` (the gate before this stage), `../ultra-low-latency-transceivers/` (transceiver-specific bring-up considerations, e.g. confirming actual line rate lock before trusting any latency measurement).
