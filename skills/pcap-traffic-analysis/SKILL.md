---
name: pcap-traffic-analysis
description: "Use when analyzing a .pcap/.pcapng capture of TCP order-entry traffic: reassembling TCP streams, decoding order-entry message fields, extracting per-order chains, measuring real-world timing, or converting captured traffic into testbench replay stimulus. Trigger phrases: 'pcap analysis', 'tcp reassembly', 'order entry field decoder', 'order chain extraction', 'packet capture analysis', 'wire capture', 'replay pcap into testbench', 'tick to trade from pcap capture'. Verification-adjacent, not a lifecycle stage — use once real captured traffic exists, alongside cocotb-verification and functional-coverage-closure."
---

# Pcap traffic analysis for order-entry gateways

Analyzes real captured traffic rather than generating stimulus — the counterpart to `../market-order-entry-conveyor/`, which builds and simulates the gateway. Use this skill once a `.pcap`/`.pcapng` capture exists (from a lab tap, a switch SPAN port, or a hardware bring-up session) and you need to understand or reuse what actually crossed the wire.

**Same disclosure as `../market-order-entry-conveyor/`**: the field decoder here targets the same generic, illustrative message layout from `../market-order-entry-conveyor/references/message-field-table-template.md`, not any real exchange's certified protocol. Adapt the decoder's field offsets to your actual protocol spec before using this on production traffic.

**Dependency**: this skill uses Python with `scapy` or `dpkt` for pcap parsing — neither is part of the Vivado/simulator toolchain used elsewhere in this library; install with `pip install scapy` or `pip install dpkt` before running any of the reference scripts.

## The pipeline

1. **TCP reassembly** (`references/tcp-reassembly.py`) — identify flows by 4-tuple (src IP/port, dst IP/port), reorder out-of-order segments, and de-duplicate retransmissions *before* attempting to decode payload bytes. Decoding an unreassembled stream doesn't fail loudly — it silently misaligns field offsets and produces plausible-looking garbage, which is a worse failure mode than a crash.
2. **Order-entry field decoding** (`references/order-entry-field-decoder.py`) — apply the fixed-offset field table to reassembled payload bytes, reusing the same layout `../market-order-entry-conveyor/references/framer-parser-rtl-pattern.md` implements in RTL. Decoding real traffic against the same field table the RTL was built from is what makes this useful as a cross-check, not just a log viewer.
3. **Order chain extraction** (`references/order-chain-extractor.py`) — group decoded messages by order token into their expected lifecycle (New -> Replace -> Cancel/Execution), and flag anomalies: a Replace or Cancel with no prior New Order token seen in this capture, or a duplicate New Order token. An anomaly found in real traffic that isn't yet a covered case in `../functional-coverage-closure/` is a signal to add it there, not just a one-off observation.
4. **Latency/timing analysis** (`references/pcap-latency-analysis.py`) — inter-message and inter-packet gaps from capture timestamps, reported as a histogram, not a single number (same discipline as `../market-order-entry-conveyor/references/tick-to-trade-latency-methodology.md`).
5. **Pcap-driven test vector generation** (`references/pcap-to-testvector.py`) — convert a decoded, chain-extracted capture into the same `OrderEntryMessage`-shaped stimulus `../market-order-entry-conveyor/references/order-entry-cocotb-testbench.py` already drives the DUT with, so real captured traffic can be replayed through simulation as regression input alongside (not instead of) synthetic directed/constrained-random tests.

## Latency accuracy caveat — read before quoting a pcap-derived latency number

Standard OS-level pcap capture timestamps have microsecond-to-millisecond jitter (kernel scheduling, NIC driver buffering) and are **not** a substitute for the hardware ILA-based cycle-accurate measurement method in `../market-order-entry-conveyor/references/tick-to-trade-latency-methodology.md`. Pcap-derived timing is appropriate for coarse/relative analysis — order chain pacing, session-level gaps, whether a burst of messages arrived back-to-back or spread out — not for validating a sub-microsecond FPGA latency budget, unless the capture itself came from hardware/PTP-timestamping taps built for that purpose (e.g. dedicated low-latency capture appliances). Don't let a pcap-derived number get quoted as if it were a cycle-accurate measurement; state the capture method's timestamp resolution alongside any latency figure reported from this skill.

## See also

`../market-order-entry-conveyor/` (shared message layout and testbench shapes — this skill decodes/replays against the same model, it doesn't redefine it), `../cocotb-verification/` (replay integration target), `../functional-coverage-closure/` (anomalies found here become coverage goals), `../ultra-low-latency-transceivers/references/latency-budget-accounting.md` (measured-vs-calculated comparison method).
