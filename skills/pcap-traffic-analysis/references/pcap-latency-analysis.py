"""
Inter-message and inter-packet timing analysis from pcap capture
timestamps. Read the latency-accuracy caveat in ../SKILL.md before
treating any number this script produces as a cycle-accurate latency
measurement - standard OS-captured pcap timestamps carry microsecond-to-
millisecond jitter and are suited to coarse/relative analysis, not to
validating a sub-microsecond FPGA latency budget.
"""

import statistics
from dataclasses import dataclass


@dataclass
class LatencyHistogram:
    samples_ns: list

    @property
    def count(self):
        return len(self.samples_ns)

    def summary(self) -> dict:
        if not self.samples_ns:
            return {"count": 0}
        sorted_samples = sorted(self.samples_ns)
        return {
            "count": len(sorted_samples),
            "min_ns": sorted_samples[0],
            "median_ns": statistics.median(sorted_samples),
            "p99_ns": sorted_samples[int(len(sorted_samples) * 0.99)],
            "max_ns": sorted_samples[-1],
            "mean_ns": statistics.mean(sorted_samples),
        }

    def print_summary(self, label: str = "latency"):
        s = self.summary()
        if s["count"] == 0:
            print(f"{label}: no samples")
            return
        print(f"{label}: n={s['count']} "
              f"min={s['min_ns']:.0f}ns median={s['median_ns']:.0f}ns "
              f"p99={s['p99_ns']:.0f}ns max={s['max_ns']:.0f}ns "
              f"mean={s['mean_ns']:.0f}ns")


def inter_message_gaps(decoded_messages: list) -> LatencyHistogram:
    """Gap between consecutive messages on the same flow, in nanoseconds -
    useful for order chain pacing analysis (e.g. how long after a New
    Order does a Replace typically arrive), not for sub-microsecond
    gateway latency claims."""
    ordered = sorted(decoded_messages, key=lambda m: m.capture_time or 0)
    gaps_ns = [
        (b.capture_time - a.capture_time) * 1e9
        for a, b in zip(ordered, ordered[1:])
        if a.capture_time is not None and b.capture_time is not None
    ]
    return LatencyHistogram(gaps_ns)


def request_response_latency(requests: list, responses: list, match_key="order_token") -> LatencyHistogram:
    """Pairs each request (e.g. New Order, msg_type == 'N') with its first
    matching response (e.g. Execution Report, msg_type == 'E') by
    order_token, and reports the gap - the pcap-based analogue of the
    tick-to-trade measurement in
    ../../market-order-entry-conveyor/references/tick-to-trade-latency-methodology.md,
    with the accuracy caveat from ../SKILL.md applying in full."""
    response_by_key = {}
    for resp in responses:
        key = getattr(resp, match_key)
        response_by_key.setdefault(key, resp)   # first response only

    samples_ns = []
    for req in requests:
        key = getattr(req, match_key)
        resp = response_by_key.get(key)
        if resp and req.capture_time is not None and resp.capture_time is not None:
            samples_ns.append((resp.capture_time - req.capture_time) * 1e9)

    return LatencyHistogram(samples_ns)


def _load_sibling(module_name: str, filename: str):
    """See the identical helper in order-entry-field-decoder.py - loads a
    hyphenated-filename sibling script by path, since a plain `import`
    statement can't reference a module name containing hyphens."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).parent / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    import sys
    reassemble_pcap = _load_sibling("tcp_reassembly", "tcp-reassembly.py").reassemble_pcap
    decode_stream = _load_sibling("order_entry_field_decoder", "order-entry-field-decoder.py").decode_stream

    flows = reassemble_pcap(sys.argv[1])
    all_messages = []
    for flow in flows.values():
        all_messages.extend(decode_stream(flow.reassembled_bytes(), flow.first_timestamp))

    inter_message_gaps(all_messages).print_summary("inter-message gap")

    new_orders = [m for m in all_messages if m.msg_type == "N"]
    executions = [m for m in all_messages if m.msg_type == "E"]
    request_response_latency(new_orders, executions).print_summary(
        "New Order -> Execution (pcap-derived, NOT cycle-accurate — see SKILL.md caveat)"
    )
