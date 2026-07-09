# Coverage closure workflow

## The loop

1. **Run** the full regression (directed + constrained-random, multiple seeds) with coverage enabled.
2. **Merge** per-run coverage databases into a cumulative model (e.g. Vivado simulator's `xcrg`/coverage merge utilities, or the equivalent for the simulator in use — see `../../simulation-workflow/`).
3. **Rank holes by root cause, not by bin count.** Pull the list of unhit bins/crosses and group them: often 20 individually-empty bins trace back to one missing stimulus pattern (e.g. "nothing ever tested reset asserting mid-burst"), and fixing that one sequence closes all 20 at once.
4. **Close each root cause** one of three ways:
   - Add or adjust a **directed test** for a specific spec'd case that constrained-random is unlikely to hit on its own (deep corner cases, specific timing races).
   - **Relax constraints** on an existing constrained-random sequence so the case becomes reachable (e.g. widen the `idle_cycles_before` distribution so `zero_idle` combined with an error condition actually gets generated together).
   - **Document a waiver**: state precisely why the case is unreachable in this configuration (e.g. "this cross requires two clock domains this instance doesn't have — valid in the SoC-level environment, not here") — a waiver without a stated reason is indistinguishable from a hole nobody looked at.
5. **Re-run, re-merge, re-rank.** Repeat until every functional coverage goal is either closed or has a dated, reasoned waiver on file.

## Sign-off bar

State the target explicitly per project (commonly 100% of defined functional coverage goals, since an incomplete-but-high percentage invites exactly the "we'll come back to it" holes that survive into production) — and require every waiver to be reviewed, not just self-declared by whoever wrote the covergroup.

## Common anti-patterns

- **Coverage goals written after the fact to match what regression already hit** — inverts the purpose; goals come from the spec's corner-case list (`../../fpga-functional-spec/`), not from a post-hoc description of what happened to run.
- **Waiving a hole because "constrained-random hasn't hit it in N runs"** without checking whether the constraint distribution actually makes it reachable — often the fix is a distribution change, not a waiver.
- **Merging coverage across unrelated configurations** (e.g. combining a narrow-datapath and wide-datapath build's coverage into one number) — hides configuration-specific holes; keep coverage databases segmented by configuration and only compare like-for-like.
