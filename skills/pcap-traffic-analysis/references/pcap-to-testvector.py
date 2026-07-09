"""
Converts decoded, chain-extracted capture data into the same
OrderEntryMessage-shaped stimulus that
../../market-order-entry-conveyor/references/order-entry-cocotb-testbench.py
already uses to drive the DUT - so a real capture can be replayed
through simulation as regression input alongside the synthetic
directed/constrained-random tests, not instead of them.

Reuses OrderEntryMessage from the conveyor skill rather than redefining
the message shape here - copy that file alongside this one (or adjust
sys.path) so the import below resolves in your project layout.
"""

import os
import importlib.util
from pathlib import Path


def _load_sibling_skill_module(module_name: str, relative_path: str):
    """Loads order-entry-cocotb-testbench.py from the neighboring
    market-order-entry-conveyor skill by file path rather than a plain
    `import`, for two reasons: (1) these reference files use hyphenated
    names, matching this library's file-naming convention, and Python
    module names can't contain hyphens; (2) it avoids requiring the
    conveyor skill's references/ directory to be copied onto sys.path
    ahead of time. Adjust relative_path if your project copies these
    reference files into a different layout."""
    path = Path(__file__).parent / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_order_entry_tb = _load_sibling_skill_module(
    "order_entry_cocotb_testbench",
    os.path.join("..", "..", "market-order-entry-conveyor", "references",
                 "order-entry-cocotb-testbench.py"),
)
OrderEntryMessage = _order_entry_tb.OrderEntryMessage


def decoded_to_stimulus(decoded_msg) -> OrderEntryMessage:
    """One DecodedMessage (from order-entry-field-decoder.py) ->
    one OrderEntryMessage (replayable cocotb stimulus). Preserves the
    corrupt-checksum/reserved-bits condition observed in the real
    capture rather than normalizing it away, so a reject case seen on
    the wire replays as a reject case in simulation too."""
    return OrderEntryMessage(
        msg_type=decoded_msg.msg_type,
        order_token=decoded_msg.order_token,
        symbol=decoded_msg.symbol,
        quantity=decoded_msg.quantity,
        price=decoded_msg.price,
        side=decoded_msg.side,
        flags=decoded_msg.flags,
        timestamp=decoded_msg.timestamp,
        corrupt_checksum=not decoded_msg.checksum_ok,
    )


def chains_to_stimulus_sequence(chains: dict) -> list:
    """Flattens all order chains back into time-ordered stimulus,
    preserving the original inter-message ordering (though not the exact
    inter-message timing - see idle_cycles_before note below)."""
    all_decoded = [m for chain in chains.values() for m in chain.messages]
    all_decoded.sort(key=lambda m: m.capture_time or 0)
    return [decoded_to_stimulus(m) for m in all_decoded]


def write_replay_test(stimulus: list, out_path: str, clock_period_ns: float = 1.552):
    """Emits a cocotb test function that replays the given stimulus
    sequence, reusing the driver/scoreboard shape from
    order-entry-cocotb-testbench.py. idle_cycles_before is NOT taken from
    the pcap's real inter-message timing (per the latency-accuracy
    caveat in ../SKILL.md, pcap timestamps aren't cycle-accurate) - it
    defaults to back-to-back (0) unless you deliberately want to
    approximate relative pacing for a non-timing-critical replay test.

    NOTE: the generated test imports `order_entry_cocotb_testbench` by
    plain module name, which requires an underscore-named copy of
    order-entry-cocotb-testbench.py to sit alongside it in the actual
    cocotb test directory (cocotb's own MODULE= convention already
    expects proper Python module names for test files, so this matches
    normal project layout rather than adding a new requirement)."""
    with open(out_path, "w") as f:
        f.write('"""Auto-generated pcap replay test - see pcap-to-testvector.py.\n')
        f.write('Requires order_entry_cocotb_testbench.py (underscore-named copy of\n')
        f.write('order-entry-cocotb-testbench.py) in this same directory."""\n')
        f.write("import cocotb\n")
        f.write("from cocotb.clock import Clock\n")
        f.write("from cocotb.triggers import RisingEdge\n")
        f.write("from order_entry_cocotb_testbench import drive_message, OrderEntryScoreboard\n\n")
        f.write("REPLAY_MESSAGES = [\n")
        for msg in stimulus:
            f.write(
                f"    dict(msg_type={msg.msg_type!r}, order_token={msg.order_token}, "
                f"symbol={msg.symbol.decode().strip()!r}, quantity={msg.quantity}, "
                f"price={msg.price}, side={msg.side!r}, flags={msg.flags}, "
                f"timestamp={msg.timestamp}, corrupt_checksum={msg.corrupt_checksum}),\n"
            )
        f.write("]\n\n")
        f.write("@cocotb.test()\n")
        f.write("async def test_pcap_replay(dut):\n")
        f.write(f"    cocotb.start_soon(Clock(dut.clk, {clock_period_ns}, units='ns').start())\n")
        f.write("    scoreboard = OrderEntryScoreboard()\n")
        f.write("    from order_entry_cocotb_testbench import OrderEntryMessage as _M\n")
        f.write("    for kwargs in REPLAY_MESSAGES:\n")
        f.write("        msg = _M(**kwargs)\n")
        f.write("        scoreboard.add_stimulus(msg)\n")
        f.write("        await drive_message(dut, msg)\n")
        f.write("        await RisingEdge(dut.clk)\n")
        f.write("        scoreboard.check_observed(dut.msg_type_r.value, dut.reject_r.value)\n")
        f.write("    assert scoreboard.mismatches == 0\n")

    print(f"wrote {len(stimulus)}-message replay test to {out_path}")


if __name__ == "__main__":
    import sys as _sys
    reassemble_pcap = _load_sibling_skill_module(
        "tcp_reassembly", "tcp-reassembly.py").reassemble_pcap
    decode_stream = _load_sibling_skill_module(
        "order_entry_field_decoder", "order-entry-field-decoder.py").decode_stream
    extract_chains = _load_sibling_skill_module(
        "order_chain_extractor", "order-chain-extractor.py").extract_chains

    flows = reassemble_pcap(_sys.argv[1])
    all_messages = []
    for flow in flows.values():
        all_messages.extend(decode_stream(flow.reassembled_bytes(), flow.first_timestamp))

    chains = extract_chains(all_messages)
    stimulus = chains_to_stimulus_sequence(chains)
    write_replay_test(stimulus, _sys.argv[2] if len(_sys.argv) > 2 else "test_pcap_replay.py")
