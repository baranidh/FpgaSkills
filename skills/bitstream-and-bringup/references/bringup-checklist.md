# Hardware bring-up checklist

Work in order — each step assumes the previous one is confirmed, not assumed.

1. **Power present at every expected rail**, at the expected voltage, before applying configuration. Measure it; don't infer from "the board powered on" that every individual rail (core, I/O bank, transceiver supply) is correct.
2. **Reference clock present and at the expected frequency.** Measure with a scope/frequency counter if available — a populated-but-wrong oscillator, or a reference clock routed to the wrong pin, is a common bring-up-stopping mistake that looks identical to a configuration failure from the FPGA's perspective. For a 322.265625/644.53125 MHz-class transceiver reference clock specifically, confirm against `../../ultra-low-latency-transceivers/references/gty-gtm-config-644-322.md`'s expected reference frequency for the configured line rate.
3. **Configuration DONE pin asserts** after loading the bitstream. If it doesn't: check configuration mode setting matches the board (JTAG vs. Master SPI vs. SelectMAP), check configuration memory part matches what the bitstream was built for, check for a CRC error reported by the configuration interface.
4. **No readback CRC error.** If supported by the platform, run a readback verify after configuration to confirm the configured bitstream matches what was written — catches configuration memory or signal-integrity issues that DONE-pin assertion alone won't catch.
5. **ILA (see `debug-core-insertion.md`) confirms the expected reset sequence** before trusting any further behavior: async assertion visible, each clock domain's synchronized reset de-asserting in the expected order, no domain's logic active before its reset releases.
6. **Confirm transceiver lock (if applicable)** before trusting any datapath behavior — `../../ultra-low-latency-transceivers/` for GTY/GTM-specific lock status signals; a transceiver that hasn't achieved CDR lock will produce data that looks like a datapath bug but is actually a physical-layer bring-up issue.
7. **Only then apply real stimulus** and use ILA/VIO to confirm datapath behavior matches simulation — if it doesn't, suspect a bring-up-stage issue (steps 1-6) before assuming the RTL itself is wrong, since RTL was already simulation-verified upstream.

## When bring-up behavior doesn't match simulation

Check, in this order: (a) was the actual configured bitstream built from the RTL you think it was (rebuild and re-verify checksum/timestamp if unsure); (b) is the board's actual clock/reset/power environment what the interface contract assumed (`../../fpga-functional-spec/`); (c) is there an unconstrained or misconstrained CDC/IO path (`../../timing-closure-ultrascale/`) that simulation's idealized timing model wouldn't have caught. Hardware-only bugs are real but rarer than these three categories in practice.
