#!/usr/bin/env python3
"""Parse tcpdump PCAP files into CSV rows for analysis.

This script expects PCAPs stored under a directory structure like:
  <pcap-dir>/<topology>/<algorithm>/<scenario>/<host>.pcap
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


def _load_scapy():
    try:
        from scapy.all import Ether, IP, IPv6, TCP, UDP, PcapReader  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "scapy is required to parse PCAPs. Install with: pip install scapy"
        ) from exc
    return Ether, IP, IPv6, TCP, UDP, PcapReader


def build_parser():
    parser = argparse.ArgumentParser(description="Parse tcpdump PCAPs into CSV")
    parser.add_argument("--pcap-dir", default="SPF/csv/pcap", help="Input PCAP directory")
    parser.add_argument("--output-dir", default="SPF/csv/pcap-csv", help="Output CSV directory")
    return parser


def _packet_row(pkt, meta):
    Ether, IP, IPv6, TCP, UDP, _ = meta["scapy"]

    timestamp = datetime.fromtimestamp(float(pkt.time), tz=timezone.utc).isoformat()
    src_mac = dst_mac = src_ip = dst_ip = proto = ""
    src_port = dst_port = ""

    if pkt.haslayer(Ether):
        src_mac = pkt[Ether].src
        dst_mac = pkt[Ether].dst

    if pkt.haslayer(IP):
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        if pkt.haslayer(TCP):
            proto = "TCP"
            src_port = str(pkt[TCP].sport)
            dst_port = str(pkt[TCP].dport)
        elif pkt.haslayer(UDP):
            proto = "UDP"
            src_port = str(pkt[UDP].sport)
            dst_port = str(pkt[UDP].dport)
        else:
            proto = "IP"
    elif pkt.haslayer(IPv6):
        src_ip = pkt[IPv6].src
        dst_ip = pkt[IPv6].dst
        if pkt.haslayer(TCP):
            proto = "TCP"
            src_port = str(pkt[TCP].sport)
            dst_port = str(pkt[TCP].dport)
        elif pkt.haslayer(UDP):
            proto = "UDP"
            src_port = str(pkt[UDP].sport)
            dst_port = str(pkt[UDP].dport)
        else:
            proto = "IPv6"

    return {
        "timestamp": timestamp,
        "topology": meta.get("topology", ""),
        "algorithm": meta.get("algorithm", ""),
        "scenario": meta.get("scenario", ""),
        "run_id": meta.get("run_id", ""),
        "host": meta.get("host", ""),
        "pcap_file": meta.get("pcap_file", ""),
        "src_mac": src_mac,
        "dst_mac": dst_mac,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "proto": proto,
        "src_port": src_port,
        "dst_port": dst_port,
        "length": len(pkt),
    }


def _pcap_metadata(pcap_path: Path, pcap_root: Path):
    rel = pcap_path.relative_to(pcap_root)
    parts = rel.parts
    if len(parts) >= 5:
        return {
            "topology": parts[0],
            "algorithm": parts[1],
            "scenario": parts[2],
            "run_id": parts[3],
            "host": pcap_path.stem,
            "pcap_file": str(rel),
        }
    return {
        "topology": parts[0] if len(parts) > 0 else "",
        "algorithm": parts[1] if len(parts) > 1 else "",
        "scenario": parts[2] if len(parts) > 2 else "",
        "run_id": "",
        "host": pcap_path.stem,
        "pcap_file": str(rel),
    }


def _write_csv(rows, out_path: Path, fieldnames):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv=None):
    args = build_parser().parse_args(argv)
    pcap_dir = Path(args.pcap_dir)
    output_dir = Path(args.output_dir)

    Ether, IP, IPv6, TCP, UDP, PcapReader = _load_scapy()

    fieldnames = [
        "timestamp",
        "topology",
        "algorithm",
        "scenario",
        "run_id",
        "host",
        "pcap_file",
        "src_mac",
        "dst_mac",
        "src_ip",
        "dst_ip",
        "proto",
        "src_port",
        "dst_port",
        "length",
    ]

    for pcap_path in pcap_dir.rglob("*.pcap"):
        meta = _pcap_metadata(pcap_path, pcap_dir)
        meta["scapy"] = (Ether, IP, IPv6, TCP, UDP, PcapReader)

        rows = []
        reader = PcapReader(str(pcap_path))
        try:
            for pkt in reader:
                rows.append(_packet_row(pkt, meta))
        finally:
            reader.close()

        rel = pcap_path.relative_to(pcap_dir)
        csv_path = output_dir / rel.with_suffix(".csv")
        _write_csv(rows, csv_path, fieldnames)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
