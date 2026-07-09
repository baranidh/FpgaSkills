"""
cocotb driver / monitor / scoreboard skeletons.
Mirrors the responsibilities in ../../uvm-testbench-generation/references/env-topology.md -
same roles, Python coroutines instead of SV classes.
"""

import random
from collections import deque

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.queue import Queue


class InputTransaction:
    def __init__(self, data: int, last: bool, idle_cycles_before: int = 0):
        self.data = data
        self.last = last
        self.idle_cycles_before = idle_cycles_before


class InputDriver:
    """Converts transactions to pin wiggles - timing must match the
    interface contract exactly (valid/ready semantics, not just
    'eventually assert valid')."""

    def __init__(self, dut):
        self.dut = dut
        self.dut.valid.value = 0

    async def send(self, txn: InputTransaction):
        for _ in range(txn.idle_cycles_before):
            await RisingEdge(self.dut.clk)

        await RisingEdge(self.dut.clk)
        self.dut.valid.value = 1
        self.dut.data.value = txn.data
        self.dut.last.value = int(txn.last)

        # Respect backpressure: hold stable until ready is seen, per the
        # interface contract's backpressure rule.
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if self.dut.ready.value:
                break

        self.dut.valid.value = 0


class InputMonitor:
    """Passive only - never drives dut signals, so this stays reusable
    if the DUT is instantiated inside a larger integration environment."""

    def __init__(self, dut, callback=None):
        self.dut = dut
        self.callback = callback
        self.observed = Queue()
        cocotb.start_soon(self._run())

    async def _run(self):
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()   # sample only after all deltas this step settle
            if self.dut.valid.value and self.dut.ready.value:
                txn = InputTransaction(
                    data=int(self.dut.data.value),
                    last=bool(self.dut.last.value),
                )
                await self.observed.put(txn)
                if self.callback:
                    self.callback(txn)


class Scoreboard:
    """Flags mismatches AND unexpected extra/missing transactions - a
    scoreboard that only compares matched pairs will silently pass a DUT
    that drops or duplicates transactions."""

    def __init__(self, reference_model):
        self.reference_model = reference_model   # a plain Python callable/class
        self.expected = deque()
        self.match_count = 0
        self.mismatch_count = 0

    def add_stimulus(self, txn: InputTransaction):
        self.expected.append(self.reference_model.predict(txn))

    def check_observed(self, actual: InputTransaction):
        if not self.expected:
            self.mismatch_count += 1
            raise AssertionError("unexpected transaction with no matching stimulus")
        expected = self.expected.popleft()
        if expected.data != actual.data or expected.last != actual.last:
            self.mismatch_count += 1
            raise AssertionError(
                f"scoreboard mismatch: expected data={expected.data:#x} "
                f"last={expected.last}, got data={actual.data:#x} last={actual.last}"
            )
        self.match_count += 1

    def check_no_pending(self):
        """Call at end of test - a non-empty expected queue means the DUT
        dropped transactions the scoreboard never got a chance to compare."""
        if self.expected:
            raise AssertionError(
                f"{len(self.expected)} expected transactions were never observed"
            )
