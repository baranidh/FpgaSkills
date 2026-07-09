"""
cocotb-coverage functional coverage patterns.
Same concept as SystemVerilog covergroups (../../functional-coverage-closure/) -
bins, cross coverage, closure workflow - expressed as Python decorators.
Requires the `cocotb-coverage` package.
"""

from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db


DATA_WIDTH = 32
DATA_MAX = (1 << DATA_WIDTH) - 1


@CoverPoint(
    "top.data_class",
    xf=lambda txn: txn.data,
    bins=["zero", "max_val", "typical"],
    bins_labels=["zero", "max", "typical"],
    at_least=1,
)
def _classify_data(txn):
    # cocotb-coverage calls the xf lambda to get the sampled value, then
    # bins it - for non-range bins like these, prefer CoverPoint's `rel`
    # (relation) argument in real code; this stub shows the intent.
    if txn.data == 0:
        return "zero"
    if txn.data == DATA_MAX:
        return "max_val"
    return "typical"


@CoverPoint(
    "top.idle_gap",
    xf=lambda txn: txn.idle_cycles_before,
    bins=[0, 1, 2, 3, "large"],
    at_least=1,
)
def _classify_idle(txn):
    return txn.idle_cycles_before if txn.idle_cycles_before <= 3 else "large"


@CoverCross(
    "top.data_x_idle",
    items=["top.data_class", "top.idle_gap"],
    at_least=1,
)
def sample_coverage(txn):
    """Call this once per observed transaction, from the monitor's
    callback (see driver-monitor-templates.py's InputMonitor callback
    argument) - coverage should reflect what was actually observed on the
    interface, matching the SV covergroup sampling discipline."""
    _classify_data(txn)
    _classify_idle(txn)


def report_and_check_closure(target_percentage: float = 100.0):
    """Call at end of regression (not end of a single test) - matches the
    merge/rank/close loop in ../../functional-coverage-closure/references/closure-workflow.md.
    """
    coverage_db.report_coverage(print, bins=True)
    total_coverage = coverage_db["top"].cover_percentage
    if total_coverage < target_percentage:
        holes = [
            name for name, item in coverage_db.items()
            if hasattr(item, "cover_percentage") and item.cover_percentage < 100.0
        ]
        raise AssertionError(
            f"coverage closure not met: {total_coverage:.1f}% < {target_percentage}%, "
            f"open items: {holes}"
        )


def export_coverage_xml(path: str = "coverage.xml"):
    """Export for merging across regression runs / archiving, same
    purpose as merging SV coverage databases across seeds."""
    coverage_db.export_to_xml(filename=path)
