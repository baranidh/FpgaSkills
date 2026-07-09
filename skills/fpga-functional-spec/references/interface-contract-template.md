# Interface contract template

Copy this per block/interface. Every row must be filled in or explicitly marked "open question" — never left blank.

## Block identity

- **Block name:**
- **Clock domain(s) used:**
- **Reset(s) used:**

## Clock domains

| Domain name | Source (pin / MMCM-PLL output / recovered) | Nominal frequency | Notes (322.265625/644.53125 MHz-class? see clock-family-reference.md) |
|---|---|---|---|
| | | | |

## Resets

| Reset name | Domain | Assertion (sync/async) | De-assertion requirement | State guaranteed on release |
|---|---|---|---|---|
| | | | | |

## Signal table (per interface)

| Signal | Dir | Width | Clock domain | Timing relationship | Meaning when asserted |
|---|---|---|---|---|---|
| | in/out | | | comb / registered, which edge | |

## Handshake semantics

- **Protocol style:** (valid-only / valid-ready / credit-based / other — name it explicitly)
- **Backpressure behavior:** exactly how many cycles after de-asserting ready must valid stop; is data allowed to be dropped, must it stall, must it buffer
- **Reset-during-transaction behavior:** what happens to an in-flight transaction if reset asserts mid-transfer

## Error / malformed input semantics

| Condition | Detection point | Required response (drop / flag / must-never-occur) | Owner (who guarantees this can't happen upstream, if applicable) |
|---|---|---|---|
| | | | |

## Latency budget

See `latency-budget-worksheet.md` — link the completed worksheet here rather than duplicating it.

## Open questions

List every place you filled in a value without a documented source, so it's visible instead of silently assumed.
