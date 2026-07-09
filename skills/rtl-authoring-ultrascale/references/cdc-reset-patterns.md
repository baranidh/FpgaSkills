# CDC and reset patterns

Every crossing named in the interface contract's clock domain table (`../../fpga-functional-spec/references/interface-contract-template.md`) must use exactly one of these patterns. "It's basically stable so a bare wire is fine" is the single most common source of CDC bugs that pass simulation and fail only intermittently on hardware — simulation's zero-delay clock model can't expose metastability.

## Pattern 1: 2-flop synchronizer (single control bit, or a bus with a stable/qualified capture point)

```systemverilog
(* ASYNC_REG = "TRUE" *) logic sync_ff1, sync_ff2;
always_ff @(posedge dst_clk) begin
  sync_ff1 <= async_signal;
  sync_ff2 <= sync_ff1;
end
// use sync_ff2 downstream, never sync_ff1
```
Fixed cost: 2 destination-domain cycles of latency. Only safe for **single-bit** signals, or multi-bit buses where the source guarantees the bus is Gray-coded or otherwise safe against bit-tearing (see Pattern 3 for the general multi-bit case). `ASYNC_REG` (or `dont_touch`/placement constraints as appropriate) tells the tool to place the two flops close together and exempt the crossing from being merged/retimed in a way that breaks the synchronizer.

## Pattern 2: handshake (req/ack) for wide, infrequent transfers

```systemverilog
// source domain
always_ff @(posedge src_clk) begin
  if (send && !req_pending) begin
    data_hold <= data_in;
    req <= ~req;         // toggle, not pulse - survives being re-synchronized
    req_pending <= 1'b1;
  end
  if (ack_sync2 == req) req_pending <= 1'b0;
end
// destination domain: synchronize req with a 2FF sync (Pattern 1), then toggle ack back
```
Fixed cost: at least 2-3 destination cycles to see `req`, plus 2-3 source cycles to see `ack` — budget the full round trip in the latency worksheet, not just the one-way synchronizer cost. Use this when data is wide and transfers are infrequent relative to either clock; don't use it for back-to-back streaming data, where it becomes a throughput bottleneck.

## Pattern 3: asynchronous FIFO for streaming/bursty multi-bit data

Use a vendor-verified async FIFO (Xilinx FIFO Generator / AXI FIFO IP, or a Gray-coded pointer FIFO if hand-built) rather than hand-rolling pointer synchronization — Gray-code pointer synchronization has enough subtlety (pointer width vs. depth, full/empty flag generation across the boundary) that reinventing it is a common source of subtle bugs. Fixed cost: write-to-read latency is FIFO-depth-and-implementation-specific; get the number from the IP's product guide and put it in the latency table, don't estimate it.

## Reset synchronization

Assert asynchronously (so a stuck/dead clock domain can still be reset), de-assert synchronously (so no register in that domain sees the release edge outside its own clock's setup/hold window):

```systemverilog
(* ASYNC_REG = "TRUE" *) logic rst_sync1, rst_sync2;
always_ff @(posedge clk, posedge async_rst_in) begin
  if (async_rst_in) begin
    rst_sync1 <= 1'b1;
    rst_sync2 <= 1'b1;
  end else begin
    rst_sync1 <= 1'b0;
    rst_sync2 <= rst_sync1;
  end
end
// rst_sync2 is this domain's synchronized reset - one instance of this per clock domain
```
Every clock domain gets its own instance of this synchronizer fed from the same async source — never share one synchronized reset output across multiple clock domains, and never let one domain's reset de-assert before verifying every domain it feeds has its own synchronizer (a single global "reset done" signal without per-domain synchronization is a common corner-case bug, matching the "reset during in-flight transaction" case called out in the functional spec template).

## What to hand to timing closure

Every crossing built from these patterns needs a matching XDC exception (`set_false_path` for the async input into a synchronizer's first flop, or `set_max_delay -datapath_only` for the synchronizer's own output going forward) — see `../../timing-closure-ultrascale/references/xdc-snippet-library.md`. Do not let these paths go unconstrained; an unconstrained CDC path is invisible to timing analysis, which is different from (and worse than) correctly-constrained.
