#!/usr/bin/env python3
"""Run SPF benchmark sweeps and emit JSON Lines.

Example:
    python3 SPF/benchmark_algorithms.py \
        --topologies ring5 jellyfish \
        --algorithms astar widest_path bellman_ford \
        > benchmark-results.jsonl
"""

from __future__ import annotations

import argparse
import sys

from benchmark_core import BenchmarkConfig, benchmark_records, benchmark_records_live, write_jsonl


def build_parser():
    parser = argparse.ArgumentParser(description="Benchmark SPF algorithms on existing topologies")
    parser.add_argument("--mode", choices=["graph", "live"], default="graph", help="graph = pure algorithm sweep, live = Mininet + iperf3 throughput")
    parser.add_argument("--topologies", nargs="+", default=["ring5", "jellyfish"], choices=["ring5", "jellyfish"], help="Topologies to benchmark")
    parser.add_argument("--algorithms", nargs="+", default=["astar", "widest_path", "bellman_ford"], choices=["astar", "widest_path", "bellman_ford"], help="Algorithms to benchmark")
    parser.add_argument("--repetitions", type=int, default=1, help="Number of times to repeat each source/destination pair")
    parser.add_argument("--jellyfish-seed", type=int, default=42, help="Deterministic seed for jellyfish topology generation")
    parser.add_argument("--jellyfish-switches", type=int, default=10, help="Number of switches in jellyfish topology")
    parser.add_argument("--jellyfish-ports", type=int, default=4, help="Ports per switch in jellyfish topology")
    parser.add_argument("--jellyfish-sw-ports", type=int, default=3, help="Switch-switch ports in jellyfish topology")
    parser.add_argument("--default-bandwidth-mbps", type=float, default=100.0, help="Fallback bandwidth used when a link has no bw metadata")
    parser.add_argument("--max-pairs", type=int, help="Limit the number of host pairs in live mode")
    parser.add_argument("--iperf-duration", type=int, default=5, help="iperf3 duration in seconds for live mode")
    parser.add_argument("--iperf-parallel", type=int, default=1, help="iperf3 parallel streams for live mode")
    parser.add_argument("--iperf-port", type=int, default=5201, help="iperf3 TCP port for live mode")
    parser.add_argument("--warmup-ping", action=argparse.BooleanOptionalAction, default=True, help="Send a single ping before iperf3 in live mode")
    parser.add_argument("--controller-log", help="Optional path to store controller stdout/stderr in live mode")
    parser.add_argument("--output", help="Optional output file. Defaults to stdout for easy piping")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = BenchmarkConfig(
        topologies=tuple(args.topologies),
        algorithms=tuple(args.algorithms),
        repetitions=args.repetitions,
        jellyfish_seed=args.jellyfish_seed,
        jellyfish_switches=args.jellyfish_switches,
        jellyfish_ports=args.jellyfish_ports,
        jellyfish_sw_ports=args.jellyfish_sw_ports,
        default_bandwidth_mbps=args.default_bandwidth_mbps,
    )

    if args.mode == "live":
        if len(args.topologies) != 1:
            raise SystemExit("live mode currently supports exactly one topology per run")
        if len(args.algorithms) != 1:
            raise SystemExit("live mode currently supports exactly one algorithm per run")
        records = benchmark_records_live(
            config,
            max_pairs=args.max_pairs,
            iperf_duration=args.iperf_duration,
            iperf_parallel=args.iperf_parallel,
            iperf_port=args.iperf_port,
            warmup_ping=args.warmup_ping,
            controller_log_path=args.controller_log,
        )
    else:
        records = benchmark_records(config)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            try:
                write_jsonl(records, stream)
            except BrokenPipeError:
                return 0
        return 0

    try:
        write_jsonl(records, sys.stdout)
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
