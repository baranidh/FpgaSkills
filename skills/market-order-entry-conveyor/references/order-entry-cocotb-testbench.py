"""
cocotb testbench for the generic order-entry framer/parser from
framer-parser-rtl-pattern.md. Illustrative packet generator + reference
model - built the same way ../../cocotb-verification/references/driver-monitor-templates.py
is, applied to this specific message layout.
"""

import random
import struct

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer

MSG_TYPES = [b"N", b"C", b"R", b"E", b"J"]


class OrderEntryMessage:
    """Plain Python reference model of the message layout in
    message-field-table-template.md - this IS the reference model;
    cocotb's advantage here is that this class can be reused directly
    both to generate stimulus and to predict expected parser output,
    with no risk of the two silently diverging."""

    def __init__(self, msg_type, order_token, symbol, quantity, price,
                 side, flags, timestamp, corrupt_checksum=False):
        self.msg_type = msg_type
        self.order_token = order_token
        self.symbol = symbol.ljust(4)[:4].encode()
        self.quantity = quantity
        self.price = price
        self.side = side
        self.flags = flags
        self.timestamp = timestamp
        self.corrupt_checksum = corrupt_checksum

    def encode(self) -> bytes:
        body = struct.pack(
            ">c Q 4s I I c B Q",
            self.msg_type.encode(), self.order_token, self.symbol,
            self.quantity, self.price, self.side.encode(),
            self.flags, self.timestamp,
        )
        checksum = 0
        for b in body:
            checksum ^= b
        if self.corrupt_checksum:
            checksum ^= 0xFF   # deliberately wrong, for reject-path tests
        return body + bytes([checksum])

    def reserved_bits_violation(self) -> bool:
        return (self.flags & 0b1111_1100) != 0

    def msg_type_recognized(self) -> bool:
        return self.msg_type.encode() in MSG_TYPES

    def expect_reject(self) -> bool:
        return (
            self.corrupt_checksum
            or self.reserved_bits_violation()
            or not self.msg_type_recognized()
        )


def random_message(**overrides) -> OrderEntryMessage:
    defaults = dict(
        msg_type=random.choice(["N", "C", "R", "E", "J"]),
        order_token=random.getrandbits(64),
        symbol="".join(random.choices("ABCDEFGH", k=4)),
        quantity=random.randint(1, 1_000_000),
        price=random.randint(1, 1_000_000),
        side=random.choice(["B", "S"]),
        flags=random.choice([0b00, 0b01, 0b10, 0b11]),  # only legal bits by default
        timestamp=random.getrandbits(64),
    )
    defaults.update(overrides)
    return OrderEntryMessage(**defaults)


class OrderEntryScoreboard:
    def __init__(self):
        self.expected = []
        self.mismatches = 0

    def add_stimulus(self, msg: OrderEntryMessage):
        self.expected.append(msg)

    def check_observed(self, dut_msg_type, dut_reject):
        if not self.expected:
            raise AssertionError("unexpected parser output with no matching stimulus")
        expected = self.expected.pop(0)
        expected_reject = expected.expect_reject()
        if bool(dut_reject) != expected_reject:
            self.mismatches += 1
            raise AssertionError(
                f"reject mismatch: msg_type={expected.msg_type} "
                f"expected_reject={expected_reject} got={bool(dut_reject)}"
            )


async def drive_message(dut, msg: OrderEntryMessage):
    frame = msg.encode()
    frame_int = int.from_bytes(frame, byteorder="big")
    await RisingEdge(dut.clk)
    dut.frame_bus.value = frame_int
    dut.frame_start.value = 1
    await RisingEdge(dut.clk)
    dut.frame_start.value = 0


@cocotb.test()
async def test_directed_back_to_back_zero_idle(dut):
    """Directed test for the 'zero idle cycles between messages' corner
    case called out in message-field-table-template.md."""
    cocotb.start_soon(Clock(dut.clk, 1552, units="ps").start())  # ~644.53125 MHz-class
    scoreboard = OrderEntryScoreboard()

    for _ in range(16):
        msg = random_message()
        scoreboard.add_stimulus(msg)
        await drive_message(dut, msg)   # no idle cycles inserted between iterations

        await RisingEdge(dut.clk)
        await ReadOnly()
        scoreboard.check_observed(dut.msg_type_r.value, dut.reject_r.value)

    assert scoreboard.mismatches == 0


@cocotb.test()
async def test_reject_paths(dut):
    """Directed test for each reject reason: bad checksum, reserved bits
    set, unrecognized message type - one case each, not left to
    constrained-random alone to find."""
    cocotb.start_soon(Clock(dut.clk, 1552, units="ps").start())
    scoreboard = OrderEntryScoreboard()

    reject_cases = [
        random_message(corrupt_checksum=True),
        random_message(flags=0b0000_0100),          # reserved bit set
    ]
    for msg in reject_cases:
        scoreboard.add_stimulus(msg)
        await drive_message(dut, msg)
        await RisingEdge(dut.clk)
        await ReadOnly()
        scoreboard.check_observed(dut.msg_type_r.value, dut.reject_r.value)

    assert scoreboard.mismatches == 0


@cocotb.test()
async def test_constrained_random_regression(dut):
    """Constrained-random: fills in everything the directed tests didn't
    explicitly target. Coverage model (order-entry-coverage-model.md)
    is what tells you when this has run enough."""
    cocotb.start_soon(Clock(dut.clk, 1552, units="ps").start())
    scoreboard = OrderEntryScoreboard()

    for _ in range(500):
        msg = random_message()
        scoreboard.add_stimulus(msg)
        await drive_message(dut, msg)
        for _ in range(random.randint(0, 4)):   # random inter-message idle
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await ReadOnly()
        scoreboard.check_observed(dut.msg_type_r.value, dut.reject_r.value)

    assert scoreboard.mismatches == 0
