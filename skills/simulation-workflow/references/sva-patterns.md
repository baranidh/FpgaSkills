# SVA assertion patterns

## Basic protocol invariant

```systemverilog
// valid must not carry unknown (X) data - catches uninitialized-register
// bugs that a scoreboard might never notice if X happens to compare
// equal to itself in a lax check.
a_no_x_on_valid_data: assert property (
  @(posedge clk) disable iff (!rst_n)
  (valid |-> !$isunknown(data))
) else `uvm_error("SVA", "data is X while valid is asserted")
```

## Valid must hold stable until accepted (no "valid withdrawal")

```systemverilog
a_valid_stable_until_ready: assert property (
  @(posedge clk) disable iff (!rst_n)
  (valid && !ready) |=> valid
) else `uvm_error("SVA", "valid deasserted before being accepted by ready")
```

## Data must not change while valid is asserted and not yet accepted

```systemverilog
a_data_stable_until_accepted: assert property (
  @(posedge clk) disable iff (!rst_n)
  (valid && !ready) |=> $stable(data)
) else `uvm_error("SVA", "data changed while a transfer was pending")
```

## Bounded response time (useful for arbitration/lookup latency guarantees)

```systemverilog
// request must be granted (or explicitly rejected) within N cycles -
// use this to make a latency budget from fpga-functional-spec
// machine-checked, not just documented
a_bounded_grant_latency: assert property (
  @(posedge clk) disable iff (!rst_n)
  request |-> ##[1:MAX_GRANT_LATENCY] (grant || reject)
) else `uvm_error("SVA", $sformatf("no grant/reject within %0d cycles", MAX_GRANT_LATENCY))
```

## Mutual exclusion (e.g. one-hot state, exactly-one-winner arbitration)

```systemverilog
a_onehot_grant: assert property (
  @(posedge clk) disable iff (!rst_n)
  $onehot0(grant_vector)
) else `uvm_error("SVA", "more than one channel granted simultaneously")
```

## Reset discipline

`disable iff (!rst_n)` (or the equivalent for the block's actual reset polarity/domain) on every concurrent assertion is not optional — without it, assertions evaluate during reset while signals are still settling and produce false failures that train reviewers to start ignoring assertion output altogether, which defeats the entire purpose of having them.

## Where these live

Bind assertions into the DUT module (via a separate `bind` statement from a verification-only file) rather than editing RTL directly, so the assertion set can evolve independently of the RTL file and isn't accidentally included in synthesis if the bind file is properly scoped to simulation-only sources.
