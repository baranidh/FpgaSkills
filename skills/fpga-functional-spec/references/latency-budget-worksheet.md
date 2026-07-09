# Latency budget worksheet

An end-to-end latency number ("this must be under 100 ns") is not verifiable and not actionable. A per-stage cycle count is both. Build this table before RTL starts; revisit it every time a stage's implementation needs an extra pipeline register — that's a budget renegotiation, not a free action.

## Per-stage table

| Stage | Clock domain | Frequency | Cycles | Time (cycles x period) | Running total | Notes |
|---|---|---|---|---|---|---|
| Ingress capture / SerDes gearbox | | | | | | |
| Framing / parsing | | | | | | |
| Processing / lookup | | | | | | |
| CDC crossing (if any) | | | | | | add the synchronizer's fixed cost, not just "a couple cycles" |
| Egress framing | | | | | | |
| SerDes / transceiver egress | | | | | | |
| **Total** | | | | | | compare against the spec'd requirement |

## Rules for filling this in

- **Every CDC crossing costs a known, fixed number of cycles** — a 2-flop synchronizer, an async FIFO's write-to-read latency, or a handshake's round trip. Never write "negligible" for a domain crossing; get the actual number from `../../rtl-authoring-ultrascale/references/cdc-reset-patterns.md`.
- **Pipeline depth is a design decision, not a discovered fact** — if timing closure later forces an extra register (see `../../timing-closure-ultrascale/`), that cycle goes back into this table and the total is re-checked against the requirement. A budget that silently drifts because "one more register couldn't hurt" is how "ultra-low latency" claims quietly stop being true.
- **State frequency alongside cycles**, not just cycles alone — a 3-cycle stage at 644.53125 MHz (period 1.55152 ns, see `../../../references/clock-family-reference.md`) costs half the time of the same 3 cycles at 322.265625 MHz. Reviewers comparing latency across differently-clocked stages need both numbers.
- **Distinguish best-case (cut-through, no contention) from worst-case (backpressure/arbitration loss) latency** — an ultra-low-latency claim usually means the former; make sure the spec says which one is being promised, and budget both if both matter.

## Worked micro-example

| Stage | Domain | Freq | Cycles | Time |
|---|---|---|---|---|
| GTY gearbox to fabric | rx_usrclk2 | 644.53125 MHz | 2 | 3.10 ns |
| Header parse (single-cycle, see rtl-authoring-ultrascale) | core_clk | 644.53125 MHz | 1 | 1.55 ns |
| CDC to processing domain (2FF sync) | core_clk -> proc_clk | 644.53125 -> 322.265625 MHz | 3 | ~9.3 ns (dominated by destination period) |
| Lookup / decision | proc_clk | 322.265625 MHz | 2 | 6.21 ns |
| **Total (best case)** | | | 8 stages | ~20.2 ns |

This is the pattern `market-order-entry-conveyor` uses to produce its tick-to-trade histogram — see `../../market-order-entry-conveyor/references/tick-to-trade-latency-methodology.md`.
