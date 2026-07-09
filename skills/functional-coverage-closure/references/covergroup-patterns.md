# Covergroup patterns

## Basic covergroup with meaningful bins (not just range coverage)

```systemverilog
covergroup cg_input_txn with function sample(input_txn tr);
  option.per_instance = 1;

  cp_data_class: coverpoint tr.data {
    bins zero        = {0};
    bins max_val     = {{DATA_W{1'b1}}};
    bins typical     = {[1:{DATA_W{1'b1}}-1]};   // everything else, coarse-grained on purpose
  }

  cp_last: coverpoint tr.last;

  cp_idle_gap: coverpoint tr.idle_cycles_before {
    bins zero_idle       = {0};      // back-to-back, the tight-timing case
    bins small_idle[]    = {[1:3]};
    bins large_idle      = {[4:$]};
  }

  // Cross coverage: the interesting bugs are usually combinations
  cx_last_x_idle: cross cp_last, cp_idle_gap;
endgroup
```

## Illegal bins for spec-defined "can never occur" values

```systemverilog
covergroup cg_error_injection with function sample(input_txn tr);
  cp_error_code: coverpoint tr.error_code {
    bins legal_codes[] = {[0:3]};
    illegal_bins reserved_codes = {[4:7]};   // spec says these are reserved/never sent
  }
endgroup
```
An `illegal_bins` hit is a testbench/generator bug (it generated something the spec forbids), not a DUT bug — treat it as a `uvm_error` in the monitor/subscriber, not a silent coverage entry.

## Cross coverage across component boundaries (agent-level, not just per-transaction)

```systemverilog
covergroup cg_arbitration with function sample(int unsigned winner_ch, bit contested);
  cp_winner: coverpoint winner_ch { bins ch[] = {[0:NUM_CHANNELS-1]}; }
  cp_contested: coverpoint contested;
  cx_winner_contested: cross cp_winner, cp_contested;
  // proves every channel can win, AND every channel can win under contention -
  // these are different and both matter for an arbiter
endgroup
```

## Sampling discipline

Sample from the monitor/subscriber on the analysis port write (see `../../uvm-testbench-generation/references/env-topology.md`), not from inside the driver — coverage should reflect what was actually observed on the interface, which is what will also be true when this block is reused inside a larger integration environment with a different (or no) local driver.
