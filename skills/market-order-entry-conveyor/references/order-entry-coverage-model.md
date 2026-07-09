# Order-entry functional coverage model (worked example)

Applies `../../functional-coverage-closure/` using the `cocotb-coverage` path from `../../cocotb-verification/references/cocotb-coverage-patterns.py`, to the message layout in `message-field-table-template.md`.

## Coverage goals (derived from the spec's corner-case list, not from the RTL)

```python
from cocotb_coverage.coverage import CoverPoint, CoverCross

@CoverPoint(
    "order_entry.msg_type",
    xf=lambda msg: msg.msg_type,
    bins=["N", "C", "R", "E", "J"],
    at_least=5,   # every message type seen at least 5 times, not just once
)
def cover_msg_type(msg):
    pass

@CoverPoint(
    "order_entry.reject_reason",
    xf=lambda msg: (
        "checksum" if msg.corrupt_checksum else
        "reserved_bits" if msg.reserved_bits_violation() else
        "bad_type" if not msg.msg_type_recognized() else
        "none"
    ),
    bins=["checksum", "reserved_bits", "bad_type", "none"],
    at_least=3,
)
def cover_reject_reason(msg):
    pass

@CoverPoint(
    "order_entry.idle_gap",
    xf=lambda idle_cycles: "zero" if idle_cycles == 0 else ("small" if idle_cycles <= 3 else "large"),
    bins=["zero", "small", "large"],
    at_least=3,
)
def cover_idle_gap(idle_cycles):
    pass

@CoverCross(
    "order_entry.type_x_reject",
    items=["order_entry.msg_type", "order_entry.reject_reason"],
    at_least=1,
)
def cover_type_x_reject(msg):
    cover_msg_type(msg)
    cover_reject_reason(msg)

@CoverCross(
    "order_entry.reject_x_zero_idle",
    items=["order_entry.reject_reason", "order_entry.idle_gap"],
    at_least=1,
)
def cover_reject_x_idle(msg, idle_cycles):
    """The specific combination that matters most for an ultra-low-latency
    gateway: does a reject case get handled correctly even when it
    arrives back-to-back with zero idle cycles after the prior message?
    This cross is exactly the kind of combination a functional coverage
    model exists to force visibility on - neither dimension alone would
    catch a bug that only appears in this combination."""
    cover_reject_reason(msg)
    cover_idle_gap(idle_cycles)
```

## Why the cross matters more than the individual points

Each `CoverPoint` alone would be satisfied by, for example, always testing reject cases with a large idle gap and never back-to-back — passing both individual coverage goals while never actually exercising the case most likely to expose a real bug (a reject condition detected on a frame arriving immediately after another, with no time for the framer's registered state from the previous frame to have any effect... or, if there's a bug, exactly enough time for it to interfere). This is the general argument for cross coverage from `../../functional-coverage-closure/`, made concrete: single-field coverage goals are necessary but not sufficient.

## Closure workflow applied here

Run `test_constrained_random_regression` (from `order-entry-cocotb-testbench.py`) across many seeds, call `report_and_check_closure()` from `../../cocotb-verification/references/cocotb-coverage-patterns.py` at the end of the regression (not per-test), and treat any remaining hole in `order_entry.reject_x_zero_idle` as the highest-priority item to close — per the general closure workflow, group holes by root cause (here, likely "the random idle-gap distribution rarely produces zero specifically alongside a reject case") and fix the generator's distribution rather than writing one narrow directed test per empty bin.
