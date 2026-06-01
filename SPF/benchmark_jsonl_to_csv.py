#!/usr/bin/env python3
"""Convert SPF benchmark JSONL into CSV files.

By default the script writes one combined CSV.  Use --split-by to generate
multiple CSVs grouped by fields such as topology and algorithm.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import sys

from benchmark_core import jsonl_records_to_csv_rows, load_jsonl


DEFAULT_COLUMNS = [
    "timestamp",
    "benchmark_mode",
    "run_id",
    "topology",
    "topology_seed",
    "algorithm",
    "repeat_index",
    "source_host",
    "destination_host",
    "source_switch",
    "destination_switch",
    "status",
    "runtime_ms",
    "hop_count",
    "path_cost",
    "path_string",
    "path_switches",
    "bottleneck_mbps",
    "throughput_estimate_mbps",
    "throughput_mbps",
    "traffic_tool",
    "traffic_protocol",
    "iperf_duration_s",
    "iperf_parallel",
    "controller_pid",
    "controller_port",
    "iperf_summary",
    "iperf_port",
    "scenario_name",
    "scenario_phase",
    "scenario_index",
    "scenario_seed",
    "link_action",
    "link_target",
    "switch_target",
    "link_timing_s",
    "pingall_loss_pct",
    "tcpdump_pcap_paths",
    "tcpdump_csv_paths",
    "event_timestamps",
    "throttle_bw_mbps",
    "throttle_delay_ms",
    "first_port",
    "final_port",
    "negative_cycle",
    "error",
    "note",
]


def build_parser():
    parser = argparse.ArgumentParser(description="Convert SPF benchmark JSONL into CSV")
    parser.add_argument("--input", default="-", help="Input JSONL file or - for stdin")
    parser.add_argument("--output", help="Combined CSV output path")
    parser.add_argument("--output-dir", help="Directory for split CSVs")
    parser.add_argument("--split-by", default="topology,algorithm", help="Comma-separated grouping fields for split CSVs")
    return parser


def _read_records(path: str):
    if path == "-":
        yield from load_jsonl(sys.stdin)
        return

    with open(path, "r", encoding="utf-8") as stream:
        yield from load_jsonl(stream)


def _write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _group_name(row, split_fields):
    if not split_fields:
        return "combined"
    parts = []
    for field in split_fields:
        parts.append(f"{field}-{row.get(field, 'unknown')}")
    return "_".join(parts)


def main(argv=None):
    args = build_parser().parse_args(argv)
    split_fields = [field.strip() for field in args.split_by.split(",") if field.strip()]

    records = list(jsonl_records_to_csv_rows(_read_records(args.input)))
    if not records:
        return 0

    fieldnames = list(DEFAULT_COLUMNS)
    for record in records:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    if args.output_dir:
        grouped = defaultdict(list)
        for record in records:
            grouped[_group_name(record, split_fields)].append(record)

        output_dir = Path(args.output_dir)
        for group_name, group_rows in grouped.items():
            _write_csv(output_dir / f"{group_name}.csv", group_rows, fieldnames)
        return 0

    if not args.output:
        raise SystemExit("either --output or --output-dir must be provided")

    _write_csv(Path(args.output), records, fieldnames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
