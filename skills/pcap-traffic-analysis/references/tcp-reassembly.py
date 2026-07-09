"""
TCP stream reassembly from a pcap/pcapng capture, using scapy.
Produces ordered, de-duplicated payload bytes per flow - the required
input to order-entry-field-decoder.py. Decoding payload bytes straight
from raw packet order (without this step) silently misaligns field
offsets whenever a single retransmission or out-of-order segment is
present in the capture - it won't error, it'll just decode garbage that
looks plausible.

Requires: pip install scapy
"""

from collections import defaultdict
from dataclasses import dataclass, field

from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP


@dataclass
class TCPFlow:
    """One direction of one TCP connection, identified by 4-tuple."""
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    segments: dict = field(default_factory=dict)   # seq -> payload bytes
    first_timestamp: float = None
    last_timestamp: float = None

    @property
    def flow_id(self):
        return (self.src_ip, self.src_port, self.dst_ip, self.dst_port)

    def add_segment(self, seq: int, payload: bytes, timestamp: float):
        if not payload:
            return
        if seq not in self.segments:          # de-duplicate retransmissions by sequence number
            self.segments[seq] = payload
        if self.first_timestamp is None:
            self.first_timestamp = timestamp
        self.last_timestamp = timestamp

    def reassembled_bytes(self) -> bytes:
        """Reorders by sequence number and concatenates - does not attempt
        to resolve overlapping-but-differing retransmitted segments beyond
        first-seen-wins, which is sufficient for order-entry traffic where
        retransmissions are expected to be byte-identical."""
        ordered_seqs = sorted(self.segments.keys())
        return b"".join(self.segments[s] for s in ordered_seqs)


def reassemble_pcap(pcap_path: str) -> dict:
    """Returns {flow_id: TCPFlow} for every TCP flow direction seen in the
    capture. Each direction of a connection is reassembled separately -
    order-entry traffic is normally asymmetric (client sends orders,
    exchange sends executions on the same connection), so decode each
    flow_id's reassembled bytes independently in order-entry-field-decoder.py."""
    packets = rdpcap(pcap_path)
    flows = {}

    for pkt in packets:
        if IP not in pkt or TCP not in pkt:
            continue
        ip_layer = pkt[IP]
        tcp_layer = pkt[TCP]
        payload = bytes(tcp_layer.payload)

        flow_key = (ip_layer.src, tcp_layer.sport, ip_layer.dst, tcp_layer.dport)
        if flow_key not in flows:
            flows[flow_key] = TCPFlow(
                src_ip=ip_layer.src, src_port=tcp_layer.sport,
                dst_ip=ip_layer.dst, dst_port=tcp_layer.dport,
            )
        flows[flow_key].add_segment(tcp_layer.seq, payload, float(pkt.time))

    return flows


if __name__ == "__main__":
    import sys
    flows = reassemble_pcap(sys.argv[1])
    for flow_id, flow in flows.items():
        data = flow.reassembled_bytes()
        print(f"{flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port}: "
              f"{len(data)} reassembled bytes, {len(flow.segments)} segments")
