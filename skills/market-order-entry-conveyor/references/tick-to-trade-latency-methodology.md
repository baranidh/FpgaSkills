# Tick-to-trade latency methodology (worked example)

Applies `../../ultra-low-latency-transceivers/references/latency-budget-accounting.md`'s per-stage method and best-case/worst-case discipline to the order-entry framer/parser from `framer-parser-rtl-pattern.md`.

## Per-stage budget (best case, cut-through)

| Stage | Domain | Frequency | Cycles | Time |
|---|---|---|---|---|
| GTY gearbox to fabric | rx_usrclk2 | 644.53125 MHz-class | 2 | 3.10 ns |
| Single-cycle frame parse + checksum + reject check | core_clk | 644.53125 MHz-class | 1 | 1.55 ns |
| Decision logic (e.g. route New Order to matching-adjacent logic) | core_clk | 644.53125 MHz-class | 1-2 | 1.55-3.10 ns |
| CDC to any downstream processing domain, if present | core_clk -> proc_clk | 644.53125 -> 322.265625 MHz-class | 3 (2FF sync, if single-bit control; more if data must cross) | ~9.3 ns, dominated by destination period |
| **Total (best case, no downstream CDC)** | | | 4-5 cycles | ~6.2-7.75 ns |
| **Total (best case, with a downstream CDC crossing)** | | | 7-8 cycles | ~15.5-17 ns |

Whether the CDC crossing is even necessary is itself a latency decision — per `../../ultra-low-latency-transceivers/`'s cut-through principle, the fastest CDC is the one avoided by processing directly in the transceiver-facing domain if the downstream logic can be structured to run at that same frequency.

## Worst case (contention)

Add: arbitration loss cycles if this gateway multiplexes multiple upstream channels into one downstream path (get the actual worst-case wait from the arbiter's own worst-case-grant-latency bound, e.g. via the SVA pattern `a_bounded_grant_latency` in `../../simulation-workflow/references/sva-patterns.md`), plus reject-path handling cycles if a reject requires additional logic beyond the single-cycle check shown in `framer-parser-rtl-pattern.md`.

## Measuring it in simulation

```python
# Inside a cocotb test (see order-entry-cocotb-testbench.py), timestamp
# at drive and at observed output, using simulation time directly -
# this measures actual simulated latency, not just the calculated budget,
# catching any place the RTL doesn't match the intended cycle count.
import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.utils import get_sim_time

latencies_ns = []

async def measure_one(dut, msg):
    t0 = get_sim_time(units="ns")
    await drive_message(dut, msg)
    await RisingEdge(dut.clk)
    await ReadOnly()
    while not dut.frame_valid_r.value:
        await RisingEdge(dut.clk)
        await ReadOnly()
    t1 = get_sim_time(units="ns")
    latencies_ns.append(t1 - t0)
```

Run this across the full constrained-random regression (not just a handful of samples) and build a histogram (min/median/p99/max) rather than reporting a single number — the best-case/worst-case table above predicts the histogram's expected shape; a measured distribution with a long tail beyond the calculated worst case means either the budget missed a stage (go back to the per-stage table and find what's uncounted) or there's a real bug (e.g. an arbiter not actually bounding wait time the way its SVA assertion claims).

## Measuring on hardware

Once bring-up (`../../bitstream-and-bringup/`) confirms transceiver lock, repeat this measurement with real hardware timestamps (e.g. via an ILA capturing a free-running cycle counter sampled at ingress and egress, per `../../bitstream-and-bringup/references/debug-core-insertion.md`'s trigger-setup guidance) and compare against the simulated histogram — a mismatch here points to either an unmodeled hardware effect (reference clock jitter, elastic buffer behavior under real ppm offset) or a simulation environment gap, not automatically to "hardware is just slower."
