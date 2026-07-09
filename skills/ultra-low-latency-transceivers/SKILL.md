---
name: ultra-low-latency-transceivers
description: "Use when configuring GTY/GTM transceivers for 644.53125 MHz-class or 322.265625 MHz-class reference/line rates, designing cut-through low-latency datapaths, accounting for end-to-end latency budgets, or implementing Aurora, Interlaken, JESD204, or segmented 100G MAC-style interfaces. Trigger phrases: 'GTY transceiver', 'GTM transceiver', 'transceiver latency', 'cut-through datapath', 'latency budget', 'Aurora protocol', 'Interlaken', 'JESD204', 'CAUI4', '100G MAC segmented interface', 'minimize CDC latency'. Use during spec/architecture and again during timing closure of transceiver-adjacent clock domains."
---

# Ultra-low-latency transceiver design (UltraScale+ GTY/GTM)

Cross-cutting: pull this in from `fpga-functional-spec` (architecture time) through `timing-closure-ultrascale` (closing the transceiver-adjacent fabric clock domains), whenever a block touches a GTY/GTM transceiver or must hit a 322.265625/644.53125 MHz-class frequency.

## GTY/GTM configuration for the two frequency families

Full detail in `references/gty-gtm-config-644-322.md`. Both frequencies derive from a 25.78125 Gbps-class line rate (see `../../references/clock-family-reference.md`); the fabric-facing `TXUSRCLK2`/`RXUSRCLK2` frequency is that line rate divided by the datapath width you configure the transceiver for — wider internal datapath (e.g. 64-bit) gives the 322.265625 MHz-class fabric clock, narrower (e.g. 32-bit) gives the 644.53125 MHz-class one, at the same line rate. Choosing between them is a real architectural tradeoff: wider/slower gives fabric logic more time per cycle (easier timing closure) at the cost of more parallel logic and often more latency (deeper gearbox, wider structures); narrower/faster is the opposite.

## Cut-through datapath architecture

The core ultra-low-latency principle: **every FIFO, elastic buffer, or CDC stage you add costs fixed cycles that a cut-through design avoids by construction.** Concretely:
- Only insert an elastic buffer where clock domain rate-matching genuinely requires it (e.g. transceiver recovered clock vs. a fixed-frequency fabric clock) — not defensively "just in case."
- Size elastic buffers to the minimum depth that covers actual expected clock frequency offset (typically a small number of words for a well-matched, spec-compliant reference clock) — an oversized buffer doesn't cost average latency but does cost worst-case latency and jitter in the latency measurement.
- Process data as it streams through rather than buffering a full frame/packet before beginning to act on it, wherever the protocol's framing allows partial processing (e.g. acting on a message header before the full message payload has arrived) — this is the single biggest lever for genuinely "ultra-low" (as opposed to merely "low") latency, and it's an architectural decision that has to be made in `fpga-functional-spec`, not retrofitted later.

## Latency budget accounting (full method in references/latency-budget-accounting.md)

Extend the per-stage worksheet from `../fpga-functional-spec/references/latency-budget-worksheet.md` specifically through the transceiver: SerDes/CDR latency, gearbox latency, any elastic buffer's average and worst-case contribution, and the CDC crossing into the processing clock domain, each as a stated cycle count at a stated frequency — not a single lumped "transceiver latency" number, which hides which piece would need to change if the budget doesn't meet the requirement.

## Worked protocol examples

`references/protocol-worked-examples.md` gives one numeric example each for Aurora, Interlaken, and JESD204/segmented-100G-MAC-style interfaces — illustrative latency accounting, not a substitute for each protocol's own spec (verify against the actual Xilinx product guide: Aurora 64B/66B PG074, Interlaken PG212, JESD204 PG066, before relying on specifics in a real design).

## See also

`../market-order-entry-conveyor/` (applies this skill's cut-through/latency-accounting method to a worked order-entry gateway example), `../timing-closure-ultrascale/` (closing timing on the fabric-side clock domains this skill's frequency choice creates).
