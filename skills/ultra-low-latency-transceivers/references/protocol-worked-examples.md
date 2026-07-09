# Protocol worked examples (illustrative — verify against each protocol's own spec)

Each example is a plausible, illustrative cycle accounting to demonstrate the accounting *method* from `latency-budget-accounting.md`. Verify exact field layouts, encoding overhead, and IP-specific latency numbers against the actual product guide before relying on specifics in a real design.

## Aurora 64B/66B (point-to-point, low-latency link)

Aurora is a relatively thin framing protocol over a raw serial link — a natural fit for the cut-through principle since there's little mandatory framing overhead to parse before data is usable.

| Stage | Frequency class | Illustrative cycles |
|---|---|---|
| SerDes/CDR | — | fixed, per UG578 |
| Gearbox to fabric | 322.265625 MHz-class (wide datapath chosen for easier timing closure on the framing logic) | 2 |
| Aurora frame/idle detection | 322.265625 MHz-class | 1 (single-cycle if frame boundary is fixed-offset) |
| User data available to application logic | — | total: gearbox + frame detection, no additional buffering if the application consumes data as it streams |

Aurora's main lever for "ultra-low" vs. "low" latency is exactly this: whether the application logic downstream processes the streaming data directly (cut-through) or waits for a full frame to buffer first (adds a frame-length's worth of latency for no protocol-mandated reason).

## Interlaken (multi-lane, striped, higher throughput)

Interlaken stripes data across multiple lanes with periodic control words, which mandates a small amount of unavoidable buffering to reassemble the striped data before it's usable — a case where a fully cut-through design isn't achievable, only a minimized one.

| Stage | Frequency class | Illustrative cycles |
|---|---|---|
| Per-lane SerDes/CDR | — | fixed, per UG578 |
| Per-lane gearbox | 644.53125 MHz-class (narrower datapath chosen to minimize the lane-reassembly buffer's contribution, per the tradeoff in `gty-gtm-config-644-322.md`) | 2 per lane |
| Lane deskew/reassembly buffer | 644.53125 MHz-class | 3-6, depending on inter-lane skew tolerance configured — this is the stage worth minimizing deliberately, not a fixed cost |
| Control word removal / data extraction | 644.53125 MHz-class | 1 |

## JESD204B/C-style / segmented 100G MAC-style datapath

Both share the pattern of a wide, segmented internal bus (e.g. multiple 64-bit segments processed per cycle) specifically to keep the fabric clock at the more timing-comfortable 322.265625 MHz-class rate despite a very high aggregate data rate.

| Stage | Frequency class | Illustrative cycles |
|---|---|---|
| Gearbox to segmented fabric bus | 322.265625 MHz-class | 2-3 |
| Per-segment header/preamble handling | 322.265625 MHz-class | 1, if each segment's header is at a fixed, predictable offset |
| Segment-to-single-stream reassembly (if downstream logic needs one linear stream rather than segments) | 322.265625 MHz-class | 1-2 — avoidable entirely if downstream logic is itself written to consume the segmented form directly, which is the lower-latency option when feasible |

The segmented-bus pattern is why `../../rtl-authoring-ultrascale/` emphasizes checking actual logic-level budgets per `../../../references/clock-family-reference.md` rather than assuming "wide bus, wide clock period" is automatically comfortable — a segmented design does more parallel work per cycle, which can reintroduce the same logic-depth pressure a narrower/faster design has, just distributed across parallel segments instead of concentrated in a single narrow path.
