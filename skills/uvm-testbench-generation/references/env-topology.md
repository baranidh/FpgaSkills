# UVM environment topology

## Class hierarchy (typical block-level environment)

```
my_test extends uvm_test
  |-- my_env extends uvm_env
        |-- input_agent extends uvm_agent
        |     |-- input_driver extends uvm_driver #(input_txn)
        |     |-- input_monitor extends uvm_monitor
        |     |-- input_sequencer extends uvm_sequencer #(input_txn)
        |-- output_agent extends uvm_agent   (usually monitor-only: is_active = UVM_PASSIVE)
        |     |-- output_monitor extends uvm_monitor
        |-- reference_model extends uvm_component
        |-- scoreboard extends uvm_scoreboard
        |-- coverage_subscriber extends uvm_subscriber #(input_txn)   (see functional-coverage-closure)
```

## TLM connections

```
input_monitor.item_collected_port  --> reference_model.input_export
input_monitor.item_collected_port  --> coverage_subscriber.analysis_export
reference_model.predicted_port     --> scoreboard.expected_export
output_monitor.item_collected_port --> scoreboard.actual_export
```

Both the reference model and the coverage subscriber listen to the *input* monitor independently — coverage should reflect what was actually driven/observed, not what the reference model predicted, so a reference-model bug doesn't also blind the coverage model to the same case.

## Sequencer/driver arbitration

For multi-channel or multi-agent environments (e.g. multiple input ports arbitrating into one shared resource), each channel gets its own sequencer/driver pair; arbitration itself is a DUT behavior to verify, not something the testbench should pre-resolve — drive each channel independently and let the scoreboard confirm arbitration fairness/correctness matches the spec.

## Factory overrides

Keep every component type-registered (`` `uvm_component_utils ``) and instantiated via the factory (`type_id::create`) rather than direct `new()`, specifically so a test can override e.g. the sequencer with an error-injection variant, or the driver with one that injects protocol violations, without editing the environment class itself. This is what makes the "malformed input" test cases from the functional spec's error-semantics table implementable without a bespoke environment per error case.

## Config_db usage

Pass the virtual interface handle and any per-test configuration (e.g. "run in error-injection mode") through `uvm_config_db`, set in the test's `build_phase` before the environment's own `build_phase` runs — components should read config, never reach up to find their parent test.
