# Strategy selection guide

Vivado ships built-in synthesis and implementation strategies that bias tool effort toward different goals. Pick by observed symptom, confirm the exact strategy names available against the installed Vivado version (`list_property [get_runs synth_1]` / the Implementation Strategies list in the GUI, or `report_property` in batch mode) since exact names can shift slightly between releases.

## Selection table

| Symptom | Strategy family | Why |
|---|---|---|
| New design, no QoR problem yet | Default synthesis + Default implementation | Reasonable baseline; don't reach for an aggressive strategy before there's a known problem to solve. |
| Timing close but not closing, especially after floorplanning and RTL fixes are already applied | `Performance_ExplorePostRoutePhysOpt` (or similarly named post-route-focused strategies) | Spends extra effort on post-route physical optimization (retiming, replication) once placement/routing is otherwise reasonable. |
| Congestion-shaped failures (see `../../timing-closure-ultrascale/references/qor-fix-playbook.md`) | `Performance_SpreadLogic_high` (or similarly named congestion-oriented strategies) | Biases placement to spread logic more, trading density for routability, before manual floorplanning. |
| Iterating quickly during early RTL bring-up, final QoR not yet the goal | `Flow_RuntimeOptimized` | Prioritizes wall-clock turnaround over final timing/utilization quality — appropriate for fast inner-loop iteration, not for sign-off runs. |
| Area/utilization is the binding constraint, not timing | Area-oriented strategies (e.g. resource-sharing-favorable synthesis options) | Trades some timing margin for reduced LUT/FF/DSP/BRAM count. |

## Discipline

- Try strategy changes **after** confirming the design's RTL and constraints are otherwise sound — a strategy change that "fixes" a QoR problem masking a real RTL or constraint issue (per `qor-fix-playbook.md`) just makes that design fragile to the next change, since the same aggressive strategy may not find a similar workaround next time.
- Record which strategy a sign-off build used, alongside the checkpoint (`write_checkpoint`) — reproducing a specific QoR result later depends on both the RTL/constraints *and* the strategy used to build it.
- Re-running the same strategy can itself produce slightly different QoR (placer/router have some randomized tie-breaking) — don't chase a specific run's exact numbers; chase a strategy+RTL combination that closes reliably across a few re-runs.
