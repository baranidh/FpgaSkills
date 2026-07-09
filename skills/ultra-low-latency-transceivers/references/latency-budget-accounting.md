# Latency budget accounting for transceiver-facing datapaths

Extends `../../fpga-functional-spec/references/latency-budget-worksheet.md` with the transceiver-specific stages. Never lump these into one "transceiver latency" line — each has a distinct owner and a distinct lever if the budget doesn't meet the requirement.

## Stage breakdown

| Stage | What determines it | Typical lever if too slow |
|---|---|---|
| Serial-to-parallel (SerDes/CDR) | Fixed by transceiver architecture at the chosen line rate; get the number from UG578, don't estimate | Not adjustable by the user design; a hard floor on latency |
| Gearbox (internal datapath width conversion) | Internal datapath width choice (see `gty-gtm-config-644-322.md`) | Narrower internal width generally reduces gearbox latency at the cost of a faster, tighter-timing fabric clock |
| Elastic buffer (rate-matching to fixed fabric clock) | Buffer depth, sized to reference clock ppm tolerance | Reduce depth to the minimum the actual ppm spec requires; don't oversize defensively |
| CDC into processing clock domain (if fabric clock differs from processing clock) | Synchronizer/FIFO pattern chosen (`../../rtl-authoring-ultrascale/references/cdc-reset-patterns.md`) | Eliminate the crossing entirely by processing directly in the transceiver-facing clock domain, if feasible — the fastest CDC is the one you don't need |
| Header/field parsing | Logic levels per `../../timing-closure-ultrascale/` budget at the operating frequency | Single-cycle parse if the frame format allows it (fixed-offset fields); avoid a multi-cycle state machine parse for latency-critical fields |
| Decision/lookup logic | Design-specific (arithmetic, table lookup) | DSP48E2/BRAM structuring per `../../rtl-authoring-ultrascale/` to keep this to the minimum cycle count the operation needs |
| Egress framing + gearbox + SerDes | Mirror of ingress | Same levers, applied symmetrically |

## Best-case vs. worst-case

State both explicitly:
- **Best case (cut-through, no contention/backpressure)**: the number that matters for an "ultra-low latency" claim — the sum of the table above with every stage at its minimum.
- **Worst case (under contention, arbitration loss, elastic buffer at max fill)**: what actually happens under load — a design that only reports best-case latency is not fully specified per `../../fpga-functional-spec/`'s definition of done.

## Measuring, not just calculating

Once hardware bring-up (`../../bitstream-and-bringup/`) confirms transceiver lock, measure actual latency with a timestamp captured at ingress and again at egress (via ILA, or a dedicated latency-measurement counter in the design) and compare against the calculated budget — a mismatch here usually means either a miscounted stage or a buffer behaving differently under real reference-clock jitter than assumed. This measured-vs-calculated comparison is exactly the method `../../market-order-entry-conveyor/references/tick-to-trade-latency-methodology.md` applies to a full worked example.
