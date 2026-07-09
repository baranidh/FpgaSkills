# Clock family reference: 322.265625 MHz and 644.53125 MHz

Canonical derivation and period math for the two clock families this library targets. Every skill that needs this math links here instead of re-deriving it — if you're editing constraint or latency numbers anywhere in this repo, this is the file to change.

## Where these numbers come from

Both frequencies fall out of the same 25.78125 Gbps-class SerDes line rate that Xilinx UltraScale+ GTY/GTM transceivers use for 25GbE-class lanes (and by extension CAUI4/100GbE-over-4-lanes, Interlaken, and JESD204B/C at comparable lane rates). A line rate is brought into fabric logic through a "gearbox" that widens the serial bit stream into a parallel bus; the fabric clock frequency is the line rate divided by that parallel width:

```
322.265625 MHz = 25.78125 Gbps / 80   (80-bit-class gearbox -> wider datapath, e.g. 512-bit bus at 1/8 rate)
644.53125  MHz = 25.78125 Gbps / 40   (40-bit-class gearbox -> narrower datapath, e.g. 256-bit bus at 1/8 rate)
```

The two frequencies are exactly a 2:1 ratio: halving the datapath width doubles the required clock frequency for the same aggregate throughput. This is the one fact worth memorizing — it's why a design that's comfortable at 322 MHz can become timing-critical simply by narrowing its datapath for area/pipeline reasons, and it's the first question to ask when a block's target frequency looks unfamiliar ("is this the wide-datapath or narrow-datapath variant of the same throughput?").

Confirm the exact width/frequency pairing against the specific IP's product guide (CMAC: UG1478; Interlaken: PG212; JESD204: PG066) before relying on it for a real design — the ratio is architectural and reliable, the specific bit-width-to-IP-configuration mapping can vary by IP version.

## Period math

| Frequency | Period | Half-period (DDR budget) |
|---|---|---|
| 322.265625 MHz | 3.10303 ns | 1.55152 ns |
| 644.53125 MHz | 1.55152 ns | 0.77576 ns |

Derivation, for when you need more digits than the table:
```
period(322.265625 MHz) = 80 / 25.78125 ns  = 3.103030303... ns
period(644.53125  MHz) = 40 / 25.78125 ns  = 1.551515151... ns   (exactly half)
```

## What this means for timing closure

At 322.265625 MHz (3.1 ns period), a design with typical UltraScale+ interconnect delay has a comfortable budget for **4-6 levels of LUT logic** between registers, depending on fanout and placement. At 644.53125 MHz (1.55 ns period), that budget drops to roughly **2-3 levels of logic** — half the period buys you noticeably less than half the usable logic depth once fixed routing/setup overhead is accounted for. This is why 644.53125 MHz-class blocks lean much harder on retiming, pipelining, and DSP48E2/SRL-based structures than their 322.265625 MHz-class counterparts — see `skills/rtl-authoring-ultrascale/` and `skills/timing-closure-ultrascale/`.

## Consumers of this file

- `skills/timing-closure-ultrascale/SKILL.md` — XDC `create_clock` periods, exception budgeting
- `skills/rtl-authoring-ultrascale/references/dsp48e2-patterns.md` — cascade stage budget at each frequency
- `skills/ultra-low-latency-transceivers/` — GTY/GTM `TXUSRCLK2`/`RXUSRCLK2` frequency selection
- `skills/market-order-entry-conveyor/` — tick-to-trade cycle accounting
