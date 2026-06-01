#!/usr/bin/env python3
"""Shared helpers for SPF benchmark runs and result parsing.

The benchmark harness in this repository is intentionally lightweight: it
reuses the existing Mininet topology definitions, runs the pure-Python path
algorithms, and emits structured JSON Lines that can be redirected to a file.
That keeps the data collection pipeline easy to reproduce and easy to convert
into CSV for visualisation.
"""

from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from itertools import permutations
from pathlib import Path
from typing import Any, Callable, Iterable

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController

from algorithms.astar import astar, build_reverse_hop_heuristic
from algorithms.bellman_ford import bellman_ford
from algorithms.widest_path import widest_path


ROOT_DIR = Path(__file__).resolve().parent
LIVE_CONTROLLER_PORTS = (6653, 6633)
CONTROLLER_SCRIPTS = {
    "astar": "astar_osken_controller.py",
    "bellman_ford": "bellman_ford_osken_controller.py",
    "widest_path": "widest_path_osken_controller.py",
}


@dataclass(frozen=True)
class TopologyGraph:
    """Normalized topology view used by the benchmark harness."""

    name: str
    adjacency: dict[str, list[tuple[str, int]]]
    weights: dict[tuple[str, str], float]
    host_attachments: dict[str, tuple[str, int]]
    switch_names: tuple[str, ...]
    host_names: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a single benchmark sweep."""

    topologies: tuple[str, ...]
    algorithms: tuple[str, ...]
    repetitions: int = 1
    jellyfish_seed: int = 42
    jellyfish_switches: int = 10
    jellyfish_ports: int = 4
    jellyfish_sw_ports: int = 3
    default_bandwidth_mbps: float = 100.0


def _load_module(module_name: str, file_name: str):
    path = ROOT_DIR / file_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load {file_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_ring5_module():
    return _load_module("spf_topo_ring5_lab", "topo-ring5_lab.py")


@lru_cache(maxsize=1)
def _load_jellyfish_module():
    return _load_module("spf_jellyfish_topo", "jellyfish_topo.py")


def load_topology(topology_name: str, config: BenchmarkConfig):
    """Instantiate one of the existing topologies from the project."""

    if topology_name == "ring5":
        return _load_ring5_module().Ring5Topo()
    if topology_name == "jellyfish":
        return _load_jellyfish_module().JellyfishTopo(
            num_switches=config.jellyfish_switches,
            num_ports=config.jellyfish_ports,
            num_sw_ports=config.jellyfish_sw_ports,
            seed=config.jellyfish_seed,
        )
    raise ValueError(f"unknown topology: {topology_name}")


def build_topology_graph(topology_name: str, config: BenchmarkConfig) -> TopologyGraph:
    """Normalize a Mininet Topo into adjacency, weights, and host mappings."""

    topo = load_topology(topology_name, config)
    switch_names = tuple(sorted(topo.switches()))
    host_names = tuple(sorted(topo.hosts()))
    switch_set = set(switch_names)
    host_set = set(host_names)

    adjacency: dict[str, list[tuple[str, int]]] = defaultdict(list)
    weights: dict[tuple[str, str], float] = {}
    host_attachments: dict[str, tuple[str, int]] = {}

    for node1, node2, info in topo.iterLinks(withInfo=True):
        if node1 in switch_set and node2 in switch_set:
            port1 = int(info["port1"])
            port2 = int(info["port2"])
            adjacency[node1].append((node2, port1))
            adjacency[node2].append((node1, port2))
            bandwidth = info.get("bw")
            if bandwidth is not None:
                weights[(node1, node2)] = float(bandwidth)
                weights[(node2, node1)] = float(bandwidth)
            continue

        if node1 in switch_set and node2 in host_set:
            host_attachments[node2] = (node1, int(info["port1"]))
            continue

        if node2 in switch_set and node1 in host_set:
            host_attachments[node1] = (node2, int(info["port2"]))
            continue

    normalized_adjacency = {
        node: sorted(neighbours, key=lambda item: (item[0], item[1]))
        for node, neighbours in adjacency.items()
    }

    return TopologyGraph(
        name=topology_name,
        adjacency=normalized_adjacency,
        weights=weights,
        host_attachments=host_attachments,
        switch_names=switch_names,
        host_names=host_names,
    )


def _ordered_host_pairs(host_names: Iterable[str], attachments: dict[str, tuple[str, int]]):
    for src_host, dst_host in permutations(sorted(host_names), 2):
        if attachments[src_host][0] == attachments[dst_host][0]:
            continue
        yield src_host, dst_host


def _limited_host_pairs(graph: TopologyGraph, max_pairs: int | None = None):
    pairs = list(_ordered_host_pairs(graph.host_names, graph.host_attachments))
    if max_pairs is None:
        return pairs
    return pairs[:max_pairs]


def _reconstruct_switch_path(previous: dict[str, str | None], src: str, dst: str):
    if src == dst:
        return [src]

    path = [dst]
    current = previous.get(dst)
    while current is not None:
        path.append(current)
        if current == src:
            break
        current = previous.get(current)

    if path[-1] != src:
        return []

    path.reverse()
    return path


def _path_bottleneck(path_nodes: list[str], weights: dict[tuple[str, str], float], default_bandwidth_mbps: float):
    if len(path_nodes) < 2:
        return None

    capacities: list[float] = []
    for left, right in zip(path_nodes[:-1], path_nodes[1:]):
        capacities.append(weights.get((left, right), default_bandwidth_mbps))

    return min(capacities) if capacities else None


def _throughput_estimate(path_nodes: list[str], weights: dict[tuple[str, str], float], default_bandwidth_mbps: float):
    bottleneck = _path_bottleneck(path_nodes, weights, default_bandwidth_mbps)
    if bottleneck is None:
        return None
    hop_count = max(len(path_nodes) - 1, 1)
    return bottleneck / hop_count


def _run_astar(graph: TopologyGraph, src_switch: str, dst_switch: str):
    heuristic = build_reverse_hop_heuristic(graph.adjacency, dst_switch)
    distance, previous = astar(graph.adjacency, src_switch, dst_switch, heuristic)
    return distance, previous, None


def _run_bellman_ford(graph: TopologyGraph, src_switch: str, dst_switch: str):
    distance, previous, has_negative_cycle = bellman_ford(graph.adjacency, src_switch)
    return distance, previous, has_negative_cycle


def _run_widest_path(graph: TopologyGraph, src_switch: str, dst_switch: str, default_bandwidth_mbps: float):
    weights = dict(graph.weights)
    for left, neighbours in graph.adjacency.items():
        for right, _ in neighbours:
            weights.setdefault((left, right), default_bandwidth_mbps)

    max_bw, previous = widest_path(graph.adjacency, src_switch, weights)
    return max_bw, previous, None


ALGORITHM_RUNNERS: dict[str, Callable[..., tuple[dict[str, Any], dict[str, Any], Any]]] = {
    "astar": _run_astar,
    "bellman_ford": _run_bellman_ford,
    "widest_path": _run_widest_path,
}


def _build_algorithm_record(
    graph: TopologyGraph,
    config: BenchmarkConfig,
    algorithm_name: str,
    src_host: str,
    dst_host: str,
    repetition: int,
    benchmark_mode: str,
    run_id: str | None = None,
):
    src_switch, first_port = graph.host_attachments[src_host]
    dst_switch, final_port = graph.host_attachments[dst_host]

    started_at = time.perf_counter()
    try:
        runner = ALGORITHM_RUNNERS[algorithm_name]
        if algorithm_name == "widest_path":
            result, previous, extra = runner(
                graph,
                src_switch,
                dst_switch,
                config.default_bandwidth_mbps,
            )
        else:
            result, previous, extra = runner(graph, src_switch, dst_switch)
        runtime_ms = (time.perf_counter() - started_at) * 1000.0

        path_switches = _reconstruct_switch_path(previous, src_switch, dst_switch)
        base_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmark_mode": benchmark_mode,
            "run_id": run_id,
            "topology": graph.name,
            "topology_seed": config.jellyfish_seed if graph.name == "jellyfish" else None,
            "algorithm": algorithm_name,
            "repeat_index": repetition,
            "source_host": src_host,
            "destination_host": dst_host,
            "source_switch": src_switch,
            "destination_switch": dst_switch,
            "status": "success",
            "runtime_ms": round(runtime_ms, 6),
            "hop_count": None,
            "path_cost": None,
            "path_switches": [],
            "path_string": "",
            "bottleneck_mbps": None,
            "throughput_estimate_mbps": None,
            "throughput_mbps": None,
            "first_port": first_port,
            "final_port": final_port,
        }

        if not path_switches:
            base_record.update({"status": "unreachable", "note": "no switch path found"})
            return base_record

        hop_count = max(len(path_switches) - 1, 0)
        path_cost = result.get(dst_switch)
        bottleneck = _path_bottleneck(path_switches, graph.weights, config.default_bandwidth_mbps)
        throughput_estimate = _throughput_estimate(
            path_switches,
            graph.weights,
            config.default_bandwidth_mbps,
        )

        base_record.update(
            {
                "hop_count": hop_count,
                "path_cost": path_cost,
                "path_switches": path_switches,
                "path_string": " -> ".join(path_switches),
                "bottleneck_mbps": bottleneck,
                "throughput_estimate_mbps": throughput_estimate,
            }
        )

        if algorithm_name == "bellman_ford":
            base_record["negative_cycle"] = bool(extra)

        return base_record
    except Exception as exc:  # pragma: no cover - defensive runtime capture
        runtime_ms = (time.perf_counter() - started_at) * 1000.0
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmark_mode": benchmark_mode,
            "run_id": run_id,
            "topology": graph.name,
            "topology_seed": config.jellyfish_seed if graph.name == "jellyfish" else None,
            "algorithm": algorithm_name,
            "repeat_index": repetition,
            "source_host": src_host,
            "destination_host": dst_host,
            "source_switch": src_switch,
            "destination_switch": dst_switch,
            "status": "error",
            "runtime_ms": round(runtime_ms, 6),
            "hop_count": None,
            "path_cost": None,
            "path_switches": [],
            "path_string": "",
            "bottleneck_mbps": None,
            "throughput_estimate_mbps": None,
            "throughput_mbps": None,
            "first_port": first_port,
            "final_port": final_port,
            "error": str(exc),
        }


def _wait_for_controller(timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for port in LIVE_CONTROLLER_PORTS:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    return port
        time.sleep(0.2)
    raise TimeoutError("controller did not start on ports 6653 or 6633")


def _start_controller_process(algorithm_name: str, log_path: str | None = None):
    script_name = CONTROLLER_SCRIPTS[algorithm_name]
    controller_path = ROOT_DIR / script_name
    if log_path:
        log_stream = open(log_path, "w", encoding="utf-8")
    else:
        log_stream = subprocess.DEVNULL

    process = subprocess.Popen(
        [sys.executable, str(controller_path)],
        cwd=str(ROOT_DIR.parent),
        stdout=log_stream,
        stderr=subprocess.STDOUT,
    )

    try:
        controller_port = _wait_for_controller()
    except Exception:
        process.terminate()
        process.wait(timeout=5)
        if log_path:
            log_stream.close()
        raise

    return process, controller_port, log_stream


def _stop_controller_process(process, log_stream):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if log_stream not in (None, subprocess.DEVNULL):
        log_stream.close()


def _extract_iperf3_throughput(output: str):
    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("iperf3 did not return JSON output")
    payload = json.loads(output[start:end + 1])
    summary = payload.get("end", {}).get("sum_received") or payload.get("end", {}).get("sum_sent") or {}
    bits_per_second = summary.get("bits_per_second")
    if bits_per_second is None:
        raise ValueError("iperf3 JSON payload did not include bits_per_second")
    return bits_per_second / 1_000_000.0, payload


def _run_live_iperf3(src_host, dst_host, port: int, duration: int, parallel: int):
    dst_host.cmd(f"iperf3 -s -1 -D -p {port} >/dev/null 2>&1")
    time.sleep(0.5)
    output = src_host.cmd(
        f"iperf3 -c {dst_host.IP()} -p {port} -t {duration} -P {parallel} -J"
    )
    return _extract_iperf3_throughput(output)


def benchmark_records_live(
    config: BenchmarkConfig,
    max_pairs: int | None = None,
    iperf_duration: int = 5,
    iperf_parallel: int = 1,
    iperf_port: int = 5201,
    warmup_ping: bool = True,
    controller_log_path: str | None = None,
    run_id: str | None = None,
):
    """Yield records from a live Mininet run with measured iperf3 throughput."""

    if len(config.algorithms) != 1:
        raise ValueError("live Mininet mode currently supports one algorithm per run")

    algorithm_name = config.algorithms[0]
    if algorithm_name not in CONTROLLER_SCRIPTS:
        raise ValueError(f"live Mininet mode does not support algorithm: {algorithm_name}")

    if run_id is None:
        topo = config.topologies[0] if config.topologies else "unknown"
        algo = algorithm_name
        run_id = f"run_live_{topo}_{algo}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    controller_process = None
    controller_log_stream = None
    net = None

    try:
        controller_process, controller_port, controller_log_stream = _start_controller_process(
            algorithm_name,
            log_path=controller_log_path,
        )

        topo = load_topology(config.topologies[0], config)
        net = Mininet(
            topo=topo,
            controller=RemoteController,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            waitConnected=True,
        )

        for host in net.hosts:
            host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null 2>&1")
        for sw in net.switches:
            sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null 2>&1")

        net.start()

        graph = build_topology_graph(config.topologies[0], config)
        host_pairs = _limited_host_pairs(graph, max_pairs=max_pairs)

        for repetition in range(config.repetitions):
            for src_host, dst_host in host_pairs:
                record = _build_algorithm_record(
                    graph,
                    config,
                    algorithm_name,
                    src_host,
                    dst_host,
                    repetition,
                    benchmark_mode="live",
                    run_id=run_id,
                )

                if record.get("status") != "success":
                    yield record
                    continue

                try:
                    src_mininet = net.get(src_host)
                    dst_mininet = net.get(dst_host)
                    if warmup_ping:
                        src_mininet.cmd(f"ping -c 1 -W 1 {dst_mininet.IP()} >/dev/null 2>&1")
                        time.sleep(0.2)

                    measured_mbps, iperf_payload = _run_live_iperf3(
                        src_mininet,
                        dst_mininet,
                        port=iperf_port,
                        duration=iperf_duration,
                        parallel=iperf_parallel,
                    )
                    record["throughput_mbps"] = measured_mbps
                    record["traffic_tool"] = "iperf3"
                    record["traffic_protocol"] = "tcp"
                    record["iperf_duration_s"] = iperf_duration
                    record["iperf_parallel"] = iperf_parallel
                    record["controller_port"] = controller_port
                    record["controller_pid"] = controller_process.pid if controller_process else None
                    record["iperf_summary"] = iperf_payload.get("end", {})
                except Exception as exc:
                    record["status"] = "error"
                    record["error"] = str(exc)
                yield record
    finally:
        if net is not None:
            try:
                net.stop()
            except Exception:
                pass
        if controller_process is not None:
            _stop_controller_process(controller_process, controller_log_stream)


def benchmark_records(config: BenchmarkConfig, run_id: str | None = None):
    """Yield one JSON-serialisable record per benchmark run."""
    if run_id is None:
        run_id = f"run_graph_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    for topology_name in config.topologies:
        graph = build_topology_graph(topology_name, config)
        host_pairs = _limited_host_pairs(graph)

        for repetition in range(config.repetitions):
            for algorithm_name in config.algorithms:
                for src_host, dst_host in host_pairs:
                    yield _build_algorithm_record(
                        graph,
                        config,
                        algorithm_name,
                        src_host,
                        dst_host,
                        repetition,
                        benchmark_mode="graph",
                        run_id=run_id,
                    )


def jsonl_records_to_csv_rows(records: Iterable[dict[str, Any]]):
    """Flatten JSON-friendly records into CSV-ready dictionaries."""

    for record in records:
        flat = {}
        for key, value in record.items():
            if isinstance(value, (list, dict)):
                flat[key] = json.dumps(value, sort_keys=True)
            elif value is None:
                flat[key] = ""
            else:
                flat[key] = value
        yield flat


def write_jsonl(records: Iterable[dict[str, Any]], stream):
    for record in records:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def load_jsonl(stream):
    for line in stream:
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)
