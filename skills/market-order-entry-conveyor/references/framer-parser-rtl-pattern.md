# Single-cycle framer/parser RTL pattern

Applies `../../rtl-authoring-ultrascale/` coding rules and `../../ultra-low-latency-transceivers/`'s cut-through principle to the fixed-offset layout in `message-field-table-template.md`.

## Structure: combinational field extraction, registered output

```systemverilog
// Assumes the full 32-byte frame is available on a wide bus in one cycle
// (e.g. from a 256-bit-wide transceiver-facing datapath at a
// 322.265625/644.53125 MHz-class frequency, per ../../ultra-low-latency-transceivers/) -
// this is what makes single-cycle extraction possible: every field's
// byte offset maps directly to a fixed bit range of the wide bus, so
// extraction is pure wiring plus a register, not a multi-cycle walk.

logic [255:0] frame_bus;   // bytes 0-31, byte 0 in [255:248] (big-endian framing)

logic [7:0]   msg_type_r;
logic [63:0]  order_token_r;
logic [31:0]  symbol_r;
logic [31:0]  quantity_r;
logic [31:0]  price_r;
logic [7:0]   side_r;
logic [7:0]   flags_r;
logic [63:0]  timestamp_r;
logic [7:0]   checksum_r;
logic         frame_valid_r;
logic         checksum_ok_r;

// Combinational extraction (pure wiring - zero logic levels of real work)
wire [7:0]  msg_type_w    = frame_bus[255:248];
wire [63:0] order_token_w = frame_bus[247:184];
wire [31:0] symbol_w      = frame_bus[183:152];
wire [31:0] quantity_w    = frame_bus[151:120];
wire [31:0] price_w       = frame_bus[119:88];
wire [7:0]  side_w        = frame_bus[87:80];
wire [7:0]  flags_w       = frame_bus[79:72];
wire [63:0] timestamp_w   = frame_bus[71:8];
wire [7:0]  checksum_w    = frame_bus[7:0];

// Checksum computed combinationally over the wide bus (XOR reduction is
// cheap and shallow - one logic level regardless of width) then
// registered alongside the fields it validates, so downstream logic
// gets both the fields and their validity in the same cycle.
wire [7:0] computed_checksum = frame_bus[255:8] ^ /* XOR-reduce all preceding bytes, illustrative */ 8'h00;

always_ff @(posedge clk) begin
  if (frame_start) begin
    msg_type_r    <= msg_type_w;
    order_token_r <= order_token_w;
    symbol_r      <= symbol_w;
    quantity_r    <= quantity_w;
    price_r       <= price_w;
    side_r        <= side_w;
    flags_r       <= flags_w;
    timestamp_r   <= timestamp_w;
    checksum_r    <= checksum_w;
    checksum_ok_r <= (computed_checksum == checksum_w);
    frame_valid_r <= 1'b1;
  end else begin
    frame_valid_r <= 1'b0;
  end
end
```

## Why this hits the latency budget

Every field is a wire slice, not a computation — the only combinational logic in the cycle is the checksum XOR-reduction, which is shallow (a handful of logic levels regardless of the 31-byte width, since XOR-reduction trees are logarithmic in depth). This keeps the whole parse at **one cycle**, matching the "header/field parsing: 1 cycle if fixed-offset" line in `../../ultra-low-latency-transceivers/references/protocol-worked-examples.md`'s segmented-datapath example.

## Reserved-bit and malformed-message handling

```systemverilog
wire reserved_bits_violation = |flags_w[7:2];   // per the spec's must-be-zero rule
wire msg_type_recognized = (msg_type_w inside {"N", "C", "R", "E", "J"});

always_ff @(posedge clk) begin
  if (frame_start) begin
    reject_r <= reserved_bits_violation || !msg_type_recognized || (computed_checksum != checksum_w);
  end
end
```
Match this exactly against whatever the interface contract's error-semantics table (`../../fpga-functional-spec/references/interface-contract-template.md`) says the required response is (drop / flag / must-never-occur) — don't default to "just drop it" without confirming that's actually the spec'd behavior, since silently dropping a message the spec says should be flagged is itself a functional bug.

## Back-to-back frames

Since extraction is single-cycle and purely combinational-into-register, a new `frame_start` pulse the cycle immediately following the previous frame's registration is handled correctly with no additional state — this is the direct payoff of the fixed-offset, single-cycle structure: the "zero idle cycles between messages" corner case from the message layout template requires no special-casing here, only confirmation via a directed test (`../../cocotb-verification/`) that it was actually exercised.

## Where this stops being single-cycle

A field whose meaning depends on another field's value (e.g. a variable-length payload whose length is given by an earlier field) cannot use pure wire-slice extraction — that's the TLV/variable-length case from `message-field-table-template.md`'s comparison table, and needs a small state machine instead. Don't force this pattern onto a protocol that doesn't have fixed offsets throughout.
