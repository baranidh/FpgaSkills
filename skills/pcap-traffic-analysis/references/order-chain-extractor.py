"""
Groups decoded order-entry messages (from order-entry-field-decoder.py)
by order token into per-order lifecycle chains, and flags anomalies.

An anomaly found here that isn't yet a covered case in
../../functional-coverage-closure/ is a signal to add it there as a
coverage goal, not just a one-off observation to note and forget.
"""

from collections import defaultdict
from dataclasses import dataclass, field

# Expected lifecycle transitions for this generic layout's message types
# (N=New, C=Cancel, R=Replace, E=Execution, J=Reject) - adapt to your
# real protocol's actual state machine.
_VALID_FOLLOWERS = {
    "N": {"C", "R", "E", "J"},
    "R": {"C", "R", "E", "J"},
    "C": set(),      # terminal
    "E": {"E"},      # partial fills can repeat
    "J": set(),      # terminal
}


@dataclass
class OrderChain:
    order_token: int
    messages: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)

    def add(self, msg):
        if self.messages:
            prev_type = self.messages[-1].msg_type
            if msg.msg_type not in _VALID_FOLLOWERS.get(prev_type, set()):
                self.anomalies.append(
                    f"unexpected transition {prev_type} -> {msg.msg_type} "
                    f"for token {self.order_token}"
                )
        elif msg.msg_type != "N":
            # first message seen for this token isn't a New Order -
            # either capture started mid-session, or this is a genuine
            # protocol violation (a Replace/Cancel with no matching New
            # Order ever seen in this capture).
            self.anomalies.append(
                f"token {self.order_token} first seen as {msg.msg_type}, "
                f"no New Order observed in this capture"
            )
        self.messages.append(msg)


def extract_chains(decoded_messages: list) -> dict:
    """Returns {order_token: OrderChain}. Call after decode_stream() on
    every flow direction in the capture and merge the message lists
    (order-entry traffic on one connection typically carries both client
    requests and exchange responses, which share order tokens)."""
    chains = {}
    seen_new_order_tokens = set()

    for msg in sorted(decoded_messages, key=lambda m: m.capture_time or 0):
        chain = chains.setdefault(msg.order_token, OrderChain(order_token=msg.order_token))

        if msg.msg_type == "N":
            if msg.order_token in seen_new_order_tokens:
                chain.anomalies.append(
                    f"duplicate New Order token {msg.order_token}"
                )
            seen_new_order_tokens.add(msg.order_token)

        chain.add(msg)

    return chains


def report_anomalies(chains: dict):
    """Prints every anomaly found, grouped by order token - this is the
    list to triage against the coverage model in
    ../../functional-coverage-closure/references/covergroup-patterns.md:
    an anomaly type seen here but not represented as a coverage goal
    there is a hole in the coverage model, not just noise from this one
    capture."""
    total = 0
    for token, chain in chains.items():
        for anomaly in chain.anomalies:
            print(f"token {token}: {anomaly}")
            total += 1
    print(f"\n{total} anomalies across {len(chains)} order chains")
    return total


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

    chains = extract_chains(all_messages)
    report_anomalies(chains)
