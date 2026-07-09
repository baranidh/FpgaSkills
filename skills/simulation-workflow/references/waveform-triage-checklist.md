# Waveform and log triage checklist

Work top-down; most failures are resolved before step 3.

1. **Grep the log first.** `grep -E "UVM_ERROR|UVM_FATAL" <log>` and read the `UVM_INFO` lines immediately preceding it — component name and phase are usually enough to know which agent/scoreboard/assertion fired.
2. **Identify the specific transaction, not just "a mismatch happened."** Scoreboards should log enough (sequence number, timestamp, or a transaction ID) to jump straight to the relevant waveform window instead of scrubbing from time zero.
3. **Open the waveform at the identified time**, not earlier — trace backward from the mismatch/assertion point to find where behavior diverged from expectation, rather than replaying the whole test forward.
4. **Check for assertion firings near the failure time even if they weren't the reported UVM_ERROR** — a same-vicinity assertion (e.g. a stability violation a few cycles before the scoreboard mismatch) is very often the actual root cause; the scoreboard mismatch is the downstream symptom.
5. **Hangs (no error, no completion) usually mean a blocked `get()`** on a TLM FIFO that will never receive an item — check whether one side of the scoreboard (expected or actual) stopped receiving transactions, which usually traces to a dropped transaction on the monitor/driver side rather than DUT-level deadlock. Confirm by checking whether the DUT itself is still toggling (clock activity, internal state changing) — if the DUT is alive and only the testbench is stuck, the bug is almost always in the environment, not the RTL.
6. **Re-run the specific seed in isolation** once a suspect is found — confirms reproducibility and gives a minimal repro for debugging without regression noise around it (see `regression-script-template.tcl` for seed logging discipline that makes this possible).
7. **When the DUT genuinely behaves differently than the reference model**, go to `../../rtl-authoring-ultrascale/` or back to `../../fpga-functional-spec/` to determine whether the RTL or the reference model itself misread the spec — don't assume the RTL is wrong by default; reference models have bugs too.
