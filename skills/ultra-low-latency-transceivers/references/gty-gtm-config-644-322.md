# GTY/GTM configuration for 322.265625 / 644.53125 MHz-class fabric clocks

## The relationship

Line rate is fixed by the protocol (e.g. 25.78125 Gbps-class for a 25GbE/CAUI4 lane). The transceiver's internal gearbox converts that serial rate into a parallel word at `TXUSRCLK2`/`RXUSRCLK2`. The fabric clock frequency is:

```
fabric_clock = line_rate / internal_datapath_width
```

Per `../../../references/clock-family-reference.md`: an 80-bit-class internal width gives 322.265625 MHz; a 40-bit-class internal width gives 644.53125 MHz, at the same 25.78125 Gbps line rate. This is set via the transceiver's internal data width configuration (`TX_DATA_WIDTH`/`RX_DATA_WIDTH`-class GTY/GTM attributes, exact names per the UltraScale+ GTY/GTM Transceivers User Guide, UG578) at IP customization time, not something chosen independently of the line rate.

## Practical configuration checklist

1. **Confirm the reference clock frequency the line rate actually requires** — GTY/GTM reference clock inputs (`GTREFCLK0`/`GTREFCLK1` or `MGTREFCLK`) must match what the transceiver's PLL (CPLL/QPLL as applicable) expects for the target line rate; verify against the specific IP customization (Transceiver Wizard / CMAC / Aurora IP, depending on protocol) rather than assuming a round number.
2. **Choose internal datapath width deliberately** (see the SKILL.md tradeoff: wider/slower vs. narrower/faster) rather than accepting a default — this choice determines whether downstream fabric logic operates at 322.265625 MHz-class or 644.53125 MHz-class, with the timing-budget consequences in `../../../references/clock-family-reference.md`.
3. **Confirm `TXUSRCLK2`/`RXUSRCLK2` actually drives the fabric logic's `create_clock` constraint** with the exact period from `../../../references/clock-family-reference.md`, not a rounded approximation — a constraint typo here (e.g. 3.1 ns instead of 3.10303 ns) either over- or under-constrains every path in that domain.
4. **CDR/PLL lock status** (`RXPMARESETDONE`, `RXBYTEISALIGNED`/protocol-specific lock indicators) must be checked before trusting any data on the receive side — during bring-up (`../../bitstream-and-bringup/`) this is the first thing to confirm, before debugging what looks like a datapath bug.
5. **Elastic buffer sizing** for rate-matching between the recovered/transceiver clock and the fixed fabric reference clock — see the cut-through architecture principle in the parent SKILL.md; size to the minimum the reference clock's actual tolerance (ppm spec) requires.

## Common misconfiguration

Choosing internal datapath width to match "what the rest of my design already runs at" rather than what the latency/timing tradeoff actually needs — a design with an otherwise 322.265625 MHz-class control plane doesn't need to force its transceiver-facing datapath to the same width if a narrower, faster, lower-latency 644.53125 MHz-class front end would better serve an ultra-low-latency requirement; the mismatch just needs a properly-budgeted CDC crossing (`../../rtl-authoring-ultrascale/references/cdc-reset-patterns.md`) between the two.
