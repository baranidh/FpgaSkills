"""
Decodes reassembled TCP payload bytes (from tcp-reassembly.py) into
order-entry messages, using the SAME generic 32-byte layout as
../../market-order-entry-conveyor/references/message-field-table-template.md
and framer-parser-rtl-pattern.md - so a decoded capture can be compared
directly against what the RTL is supposed to produce.

Adapt FRAME_SIZE and the struct.unpack format string to your real
protocol's actual layout before using this on production traffic - this
is the same generic/illustrative format disclosed in
../../market-order-entry-conveyor/SKILL.md, not a real exchange spec.
"""

import struct
from dataclasses import dataclass

FRAME_SIZE = 32   # bytes - matches message-field-table-template.md
_STRUCT_FMT = ">c Q 4s I I c B Q B"   # msg_type, order_token, symbol, qty, price, side, flags, timestamp, checksum


@dataclass
class DecodedMessage:
    msg_type: str
    order_token: int
    symbol: str
    quantity: int
    price: int
    side: str
    flags: int
    timestamp: int
    checksum: int
    checksum_ok: bool
    reserved_bits_violation: bool
    msg_type_recognized: bool
    capture_time: float   # pcap timestamp this frame was observed at (see the latency-accuracy caveat in SKILL.md)


_KNOWN_TYPES = {"N", "C", "R", "E", "J"}


def _compute_checksum(body: bytes) -> int:
    checksum = 0
    for b in body:
        checksum ^= b
    return checksum


def decode_stream(data: bytes, capture_time: float = None) -> list:
    """Splits reassembled bytes into fixed-size frames and decodes each.
    A stream length that isn't a multiple of FRAME_SIZE indicates either
    an incomplete capture (missed the tail of the last message) or that
    this isn't actually the generic layout - flag it rather than silently
    dropping the remainder."""
    messages = []
    offset = 0
    while offset + FRAME_SIZE <= len(data):
        frame = data[offset:offset + FRAME_SIZE]
        body, checksum = frame[:-1], frame[-1]
        (msg_type_b, order_token, symbol_b, quantity, price,
         side_b, flags, timestamp, _unused) = struct.unpack(_STRUCT_FMT, frame)

        msg_type = msg_type_b.decode(errors="replace")
        messages.append(DecodedMessage(
            msg_type=msg_type,
            order_token=order_token,
            symbol=symbol_b.decode(errors="replace").strip(),
            quantity=quantity,
            price=price,
            side=side_b.decode(errors="replace"),
            flags=flags,
            timestamp=timestamp,
            checksum=checksum,
            checksum_ok=(_compute_checksum(body) == checksum),
            reserved_bits_violation=bool(flags & 0b1111_1100),
            msg_type_recognized=(msg_type in _KNOWN_TYPES),
            capture_time=capture_time,
        ))
        offset += FRAME_SIZE

    leftover = len(data) - offset
    if leftover:
        print(f"warning: {leftover} trailing bytes did not form a complete "
              f"{FRAME_SIZE}-byte frame - capture may be truncated or the "
              f"layout doesn't match this decoder's assumptions")

    return messages


def _load_sibling(module_name: str, filename: str):
    """Loads a sibling reference script by file path. A plain
    `import tcp_reassembly` won't work here because these reference files
    use hyphenated names (matching this library's file-naming convention)
    and Python module names can't contain hyphens - copy this loader (or
    rename the files to underscores) when adapting these scripts into a
    real project."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).parent / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    import sys
    reassemble_pcap = _load_sibling("tcp_reassembly", "tcp-reassembly.py").reassemble_pcap

    flows = reassemble_pcap(sys.argv[1])
    for flow_id, flow in flows.items():
        msgs = decode_stream(flow.reassembled_bytes(), flow.first_timestamp)
        for m in msgs:
            status = "OK" if (m.checksum_ok and not m.reserved_bits_violation
                               and m.msg_type_recognized) else "REJECT"
            print(f"[{status}] type={m.msg_type} token={m.order_token} "
                  f"symbol={m.symbol} qty={m.quantity} price={m.price} side={m.side}")
