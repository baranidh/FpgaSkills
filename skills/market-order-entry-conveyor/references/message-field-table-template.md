# Generic order-entry message layout (illustrative only)

**This is not a real exchange protocol.** It's a plausible, fixed-offset binary layout used to demonstrate the conveyor pipeline's methodology. Substitute your actual exchange's published spec (field-for-field) before writing production RTL — real protocols (OUCH-style, FIX/FAST, SBE-encoded, Pillar, iLink) have their own certified layouts, checksum/framing rules, and session-layer requirements this example does not attempt to reproduce.

## Frame layout (32 bytes, fixed length, big-endian multi-byte fields)

| Offset | Width | Field | Notes |
|---|---|---|---|
| 0 | 1 byte | Message Type | `'N'`=New Order, `'C'`=Cancel, `'R'`=Replace, `'E'`=Execution Report, `'J'`=Reject |
| 1-8 | 8 bytes | Order Token | Client-assigned unique ID, uint64 |
| 9-12 | 4 bytes | Symbol | ASCII, space-padded |
| 13-16 | 4 bytes | Quantity | uint32 |
| 17-20 | 4 bytes | Price | uint32, fixed-point, scale defined per symbol (illustrative: 4 decimal places) |
| 21 | 1 byte | Side | `'B'`=Buy, `'S'`=Sell |
| 22 | 1 byte | Time-in-Force / Flags | bit 0: IOC, bit 1: post-only, bits 2-7: reserved (must be zero) |
| 23-30 | 8 bytes | Timestamp | uint64, nanoseconds since session start (illustrative — real protocols vary) |
| 31 | 1 byte | Checksum | XOR of bytes 0-30 (illustrative — real protocols typically use CRC or none at this layer, relying on transport-level integrity) |

Every field is fixed-offset by design — this is what makes single-cycle extraction possible in `framer-parser-rtl-pattern.md`. A protocol with variable-length fields (e.g. FIX's tag=value pairs) does not admit this same single-cycle approach and needs a different RTL structure (a small state machine walking variable-length fields) — know which kind of protocol you're actually implementing before assuming this pattern applies.

## Fixed-offset vs. TLV/variable-length protocols

| Property | Fixed-offset (this example) | Variable-length (e.g. FIX tag=value, TLV-encoded) |
|---|---|---|
| Parse latency | Single cycle possible for every field | Multi-cycle, proportional to field count/position |
| RTL structure | Combinational field extraction + register | Small state machine or content-addressable field scanner |
| Best fit | Exchange-native binary order-entry protocols (most are fixed-offset specifically for this reason) | Protocols with optional/repeating fields, often at higher layers (e.g. FIX session layer) |

## Corner cases to carry into the interface contract (per `../../fpga-functional-spec/`)

- Reserved bits in the Flags field set to nonzero — must-never-occur per spec, or must-reject?
- Checksum mismatch — reject silently, flag, or pass through with an error indicator?
- Message Type byte with a value outside the defined set — reject, or is this a protocol violation that should never occur given upstream guarantees (state which, explicitly)?
- Back-to-back messages with zero idle cycles between frames — does the framer need to handle a new Message Type byte arriving the cycle immediately after the previous message's checksum byte?
- Timestamp field: must it be validated (e.g. monotonically increasing) or is it opaque pass-through data from the gateway's perspective?
