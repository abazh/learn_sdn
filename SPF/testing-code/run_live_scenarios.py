#!/usr/bin/env python3
"""Scenario-driven Mininet benchmark runner.

Runs live Mininet experiments for SPF algorithms with failure injection and
optional tcpdump capture. Results are emitted as JSON Lines for piping into
CSV conversion.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import permutations
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
SPF_DIR = THIS_DIR.parent
if str(SPF_DIR) not in sys.path:
    sys.path.insert(0, str(SPF_DIR))

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController

from benchmark_core import (
    BenchmarkConfig,
    CONTROLLER_SCRIPTS,
    build_topology_graph,
    load_topology,
    _build_algorithm_record,
    _run_live_iperf3,
    _start_controller_process,
    _stop_controller_process,
)


RING5_LINKS = [
    ("s1", "s2"),
    ("s2", "s3"),
    ("s3", "s4"),
    ("s4", "s5"),
    ("s5", "s1"),
]
RING5_SWITCHES = ["s1", "s2", "s3", "s4", "s5"]


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    phase: str
    action: str
    pre_action: bool
    during_traffic: bool
    requires_link: bool = False
    requires_switch: bool = False
    requires_throttle: bool = False
    random_link: bool = False


SCENARIOS: dict[str, ScenarioDefinition] = {
    "baseline_no_failure": ScenarioDefinition(
        name="baseline_no_failure",
        phase="baseline",
        action="none",
        pre_action=False,
        during_traffic=False,
    ),
    "link_down_before_traffic": ScenarioDefinition(
        name="link_down_before_traffic",
        phase="pre",
        action="link_down",
        pre_action=True,
        during_traffic=False,
        requires_link=True,
    ),
    "link_down_during_traffic": ScenarioDefinition(
        name="link_down_during_traffic",
        phase="during",
        action="link_down",
        pre_action=False,
        during_traffic=True,
        requires_link=True,
    ),
    "link_flap": ScenarioDefinition(
        name="link_flap",
        phase="during",
        action="link_flap",
        pre_action=False,
        during_traffic=True,
        requires_link=True,
    ),
    "switch_down": ScenarioDefinition(
        name="switch_down",
        phase="pre",
        action="switch_down",
        pre_action=True,
        during_traffic=False,
        requires_switch=True,
    ),
    "bandwidth_throttle": ScenarioDefinition(
        name="bandwidth_throttle",
        phase="pre",
        action="throttle",
        pre_action=True,
        during_traffic=False,
        requires_link=True,
        requires_throttle=True,
    ),
    "random_link_down_jellyfish": ScenarioDefinition(
        name="random_link_down_jellyfish",
        phase="pre",
        action="link_down",
        pre_action=True,
        during_traffic=False,
        requires_link=True,
        random_link=True,
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser():
    parser = argparse.ArgumentParser(description="Run live Mininet scenarios with failures")
    parser.add_argument(
        "--topologies",
        nargs="+",
        default=["ring5", "jellyfish"],
        choices=["ring5", "jellyfish"],
        help="Topologies to test",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=["astar", "bellman_ford", "widest_path"],
        choices=["astar", "bellman_ford", "widest_path"],
        help="Algorithms to test",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=list(SCENARIOS.keys()),
        choices=list(SCENARIOS.keys()),
        help="Scenario names to run",
    )
    parser.add_argument("--repetitions", type=int, default=1, help="Repetitions per host pair")
    parser.add_argument("--max-pairs", type=int, help="Limit number of host pairs")
    parser.add_argument("--iperf-duration", type=int, default=5, help="iperf3 duration in seconds")
    parser.add_argument("--iperf-parallel", type=int, default=1, help="iperf3 parallel streams")
    parser.add_argument("--iperf-port", type=int, default=5201, help="iperf3 TCP port")
    parser.add_argument(
        "--warmup-ping",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Send a ping before iperf3",
    )
    parser.add_argument(
        "--link-down-delay",
        type=float,
        default=1.0,
        help="Seconds after iperf start to bring link down",
    )
    parser.add_argument(
        "--link-up-delay",
        type=float,
        default=3.0,
        help="Seconds after iperf start to bring link up (for flap)",
    )
    parser.add_argument(
        "--throttle-bw-mbps",
        type=float,
        default=10.0,
        help="Bandwidth to apply for throttle scenario",
    )
    parser.add_argument(
        "--throttle-delay-ms",
        type=int,
        default=10,
        help="Delay to apply for throttle scenario",
    )
    parser.add_argument(
        "--scenario-seed",
        type=int,
        default=42,
        help="Seed for random link selection",
    )
    parser.add_argument(
        "--pcap-dir",
        default="SPF/csv/pcap",
        help="Base directory for tcpdump pcap files",
    )
    parser.add_argument(
        "--pcap-snaplen",
        type=int,
        default=96,
        help="tcpdump snaplen",
    )
    parser.add_argument(
        "--tcpdump",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable tcpdump capture on hosts",
    )
    parser.add_argument("--controller-log", help="Path for controller stdout/stderr")
    parser.add_argument("--output", help="Output JSONL file (defaults to stdout)")

    parser.add_argument("--jellyfish-seed", type=int, default=42)
    parser.add_argument("--jellyfish-switches", type=int, default=10)
    parser.add_argument("--jellyfish-ports", type=int, default=4)
    parser.add_argument("--jellyfish-sw-ports", type=int, default=3)
    parser.add_argument("--default-bandwidth-mbps", type=float, default=100.0)
    return parser


def _get_switch_links(net: Mininet):
    switch_names = {sw.name for sw in net.switches}
    links = []
    for link in net.links:
        left = link.intf1.node.name
        right = link.intf2.node.name
        if left in switch_names and right in switch_names:
            links.append((left, right, link))
    return links


def _find_link(net: Mininet, left: str, right: str):
    for n1, n2, link in _get_switch_links(net):
        if {n1, n2} == {left, right}:
            return link
    return None


def _link_key(left: str, right: str) -> str:
    return "-".join(sorted([left, right]))


def _select_link_pair(
    topology: str,
    scenario: ScenarioDefinition,
    scenario_index: int,
    switch_links: list[tuple[str, str, Any]],
    seed: int,
):
    if scenario.random_link or topology == "jellyfish":
        rng = random.Random(seed + scenario_index)
        if not switch_links:
            raise ValueError("no switch links available")
        left, right, _ = rng.choice(switch_links)
        return left, right

    if topology == "ring5":
        left, right = RING5_LINKS[scenario_index % len(RING5_LINKS)]
        return left, right

    if not switch_links:
        raise ValueError("no switch links available")
    left, right, _ = switch_links[scenario_index % len(switch_links)]
    return left, right


def _select_switch_target(topology: str, scenario_index: int, seed: int, switch_names: list[str]):
    if topology == "ring5":
        return RING5_SWITCHES[scenario_index % len(RING5_SWITCHES)]
    rng = random.Random(seed + scenario_index)
    return rng.choice(switch_names)


def _set_link_status(net: Mininet, left: str, right: str, status: str):
    net.configLinkStatus(left, right, status)


def _set_switch_links(net: Mininet, switch_name: str, status: str):
    for left, right, _ in _get_switch_links(net):
        if left == switch_name or right == switch_name:
            _set_link_status(net, left, right, status)


def _throttle_link(link, bw_mbps: float, delay_ms: int):
    left_params = dict(link.intf1.params)
    right_params = dict(link.intf2.params)
    delay = f"{delay_ms}ms"
    link.intf1.config(bw=bw_mbps, delay=delay)
    link.intf2.config(bw=bw_mbps, delay=delay)
    return left_params, right_params


def _restore_link_params(link, left_params: dict, right_params: dict):
    link.intf1.config(**left_params)
    link.intf2.config(**right_params)


def _start_tcpdump(net: Mininet, base_dir: Path, topology: str, algorithm: str, scenario: str, snaplen: int):
    pcap_paths: dict[str, str] = {}
    pids: dict[str, str] = {}
    scenario_dir = base_dir / topology / algorithm / scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)

    for host in net.hosts:
        intf = host.defaultIntf()
        if intf is None:
            continue
        pcap_path = scenario_dir / f"{host.name}.pcap"
        cmd = (
            f"tcpdump -i {intf.name} -w {pcap_path} -U -s {snaplen} -n "
            ">/dev/null 2>&1 & echo $!"
        )
        pid_output = host.cmd(cmd).strip()
        pid = pid_output.splitlines()[-1].strip() if pid_output else ""
        if pid:
            pids[host.name] = pid
            pcap_paths[host.name] = str(pcap_path)
    return pcap_paths, pids


def _stop_tcpdump(net: Mininet, pids: dict[str, str]):
    for host in net.hosts:
        pid = pids.get(host.name)
        if pid:
            host.cmd(f"kill -2 {pid} >/dev/null 2>&1")
    time.sleep(0.3)


def _schedule_event(delay_s: float, action_name: str, func, event_log: list[dict[str, str]]):
    def _wrapper():
        func()
        event_log.append({"event": action_name, "timestamp": _utc_now()})

    timer = threading.Timer(delay_s, _wrapper)
    timer.start()
    return timer


def _write_record(stream, record: dict[str, Any]):
    stream.write(json.dumps(record, sort_keys=True) + "\n")
    stream.flush()


def _host_pairs(graph, max_pairs: int | None):
    pairs = []
    for src, dst in permutations(graph.host_names, 2):
        if graph.host_attachments[src][0] == graph.host_attachments[dst][0]:
            continue
        pairs.append((src, dst))
    if max_pairs is None:
        return pairs
    return pairs[:max_pairs]


def run_scenarios(args):
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

    output_stream = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    try:
        for topology_name in config.topologies:
            for algorithm_name in config.algorithms:
                if algorithm_name not in CONTROLLER_SCRIPTS:
                    raise ValueError(f"unsupported algorithm for live mode: {algorithm_name}")

                for scenario_index, scenario_name in enumerate(args.scenarios):
                    if topology_name != "jellyfish" and scenario_name == "random_link_down_jellyfish":
                        continue
                    scenario = SCENARIOS[scenario_name]
                    controller_process = None
                    controller_log_stream = None
                    net = None
                    tcpdump_paths: dict[str, str] = {}
                    tcpdump_pids: dict[str, str] = {}
                    link_pair = None
                    link_target = ""
                    switch_target = ""
                    throttle_restore = None
                    scenario_events: list[dict[str, str]] = []

                    try:
                        controller_process, controller_port, controller_log_stream = _start_controller_process(
                            algorithm_name,
                            log_path=args.controller_log,
                        )

                        topo = load_topology(topology_name, config)
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

                        switch_links = _get_switch_links(net)
                        switch_names = [sw.name for sw in net.switches]

                        if scenario.requires_link:
                            left, right = _select_link_pair(
                                topology_name,
                                scenario,
                                scenario_index,
                                switch_links,
                                args.scenario_seed,
                            )
                            link_pair = (left, right)
                            link_target = _link_key(left, right)

                        if scenario.requires_switch:
                            switch_target = _select_switch_target(
                                topology_name,
                                scenario_index,
                                args.scenario_seed,
                                switch_names,
                            )

                        if scenario.pre_action:
                            if scenario.action == "link_down" and link_pair:
                                _set_link_status(net, link_pair[0], link_pair[1], "down")
                                scenario_events.append({"event": "link_down", "timestamp": _utc_now()})
                            elif scenario.action == "switch_down" and switch_target:
                                _set_switch_links(net, switch_target, "down")
                                scenario_events.append(
                                    {"event": "switch_down", "timestamp": _utc_now(), "target": switch_target}
                                )
                            elif scenario.action == "throttle" and link_pair:
                                link = _find_link(net, link_pair[0], link_pair[1])
                                if link is None:
                                    raise ValueError(f"unable to locate link {link_target}")
                                throttle_restore = _throttle_link(
                                    link, args.throttle_bw_mbps, args.throttle_delay_ms
                                )
                                scenario_events.append(
                                    {
                                        "event": "throttle",
                                        "timestamp": _utc_now(),
                                        "bw_mbps": args.throttle_bw_mbps,
                                        "delay_ms": args.throttle_delay_ms,
                                    }
                                )

                        if args.tcpdump:
                            tcpdump_paths, tcpdump_pids = _start_tcpdump(
                                net,
                                Path(args.pcap_dir),
                                topology_name,
                                algorithm_name,
                                scenario.name,
                                args.pcap_snaplen,
                            )

                        pingall_loss = net.pingAll() if net.hosts else None

                        graph = build_topology_graph(topology_name, config)
                        pairs = _host_pairs(graph, args.max_pairs)

                        for repetition in range(config.repetitions):
                            for src_host, dst_host in pairs:
                                record = _build_algorithm_record(
                                    graph,
                                    config,
                                    algorithm_name,
                                    src_host,
                                    dst_host,
                                    repetition,
                                    benchmark_mode="live",
                                )

                                link_timing = {}
                                if scenario.action in ("link_down", "link_flap"):
                                    link_timing = {
                                        "down_at": args.link_down_delay if scenario.during_traffic else 0.0,
                                        "up_at": args.link_up_delay if scenario.action == "link_flap" else None,
                                    }

                                record.update(
                                    {
                                        "scenario_name": scenario.name,
                                        "scenario_phase": scenario.phase,
                                        "scenario_index": scenario_index,
                                        "scenario_seed": args.scenario_seed
                                        if scenario.random_link or topology_name == "jellyfish"
                                        else None,
                                        "link_action": scenario.action,
                                        "link_target": link_target,
                                        "switch_target": switch_target,
                                        "link_timing_s": link_timing,
                                        "pingall_loss_pct": pingall_loss,
                                        "tcpdump_pcap_paths": tcpdump_paths,
                                        "tcpdump_csv_paths": {},
                                        "event_timestamps": list(scenario_events),
                                        "throttle_bw_mbps": args.throttle_bw_mbps
                                        if scenario.action == "throttle"
                                        else None,
                                        "throttle_delay_ms": args.throttle_delay_ms
                                        if scenario.action == "throttle"
                                        else None,
                                        "iperf_port": args.iperf_port,
                                    }
                                )

                                if record.get("status") != "success":
                                    _write_record(output_stream, record)
                                    continue

                                try:
                                    src_mininet = net.get(src_host)
                                    dst_mininet = net.get(dst_host)
                                    if args.warmup_ping:
                                        src_mininet.cmd(
                                            f"ping -c 1 -W 1 {dst_mininet.IP()} >/dev/null 2>&1"
                                        )
                                        time.sleep(0.2)

                                    event_log: list[dict[str, str]] = []
                                    timers: list[threading.Timer] = []

                                    if scenario.during_traffic and link_pair:
                                        if scenario.action in ("link_down", "link_flap"):
                                            timers.append(
                                                _schedule_event(
                                                    args.link_down_delay,
                                                    "link_down",
                                                    lambda: _set_link_status(
                                                        net, link_pair[0], link_pair[1], "down"
                                                    ),
                                                    event_log,
                                                )
                                            )
                                        if scenario.action == "link_flap":
                                            timers.append(
                                                _schedule_event(
                                                    args.link_up_delay,
                                                    "link_up",
                                                    lambda: _set_link_status(
                                                        net, link_pair[0], link_pair[1], "up"
                                                    ),
                                                    event_log,
                                                )
                                            )

                                    measured_mbps, iperf_payload = _run_live_iperf3(
                                        src_mininet,
                                        dst_mininet,
                                        port=args.iperf_port,
                                        duration=args.iperf_duration,
                                        parallel=args.iperf_parallel,
                                    )

                                    for timer in timers:
                                        if timer.is_alive():
                                            timer.cancel()

                                    if scenario.during_traffic and link_pair:
                                        _set_link_status(net, link_pair[0], link_pair[1], "up")

                                    record["throughput_mbps"] = measured_mbps
                                    record["traffic_tool"] = "iperf3"
                                    record["traffic_protocol"] = "tcp"
                                    record["iperf_duration_s"] = args.iperf_duration
                                    record["iperf_parallel"] = args.iperf_parallel
                                    record["controller_port"] = controller_port
                                    record["controller_pid"] = controller_process.pid if controller_process else None
                                    record["iperf_summary"] = iperf_payload.get("end", {})
                                    record["event_timestamps"] = record["event_timestamps"] + event_log
                                except Exception as exc:
                                    record["status"] = "error"
                                    record["error"] = str(exc)

                                _write_record(output_stream, record)
                    finally:
                        if args.tcpdump and tcpdump_pids and net is not None:
                            _stop_tcpdump(net, tcpdump_pids)

                        if scenario.pre_action and net is not None:
                            if scenario.action == "link_down" and link_pair:
                                _set_link_status(net, link_pair[0], link_pair[1], "up")
                            elif scenario.action == "switch_down" and switch_target:
                                _set_switch_links(net, switch_target, "up")
                            elif scenario.action == "throttle" and link_pair and throttle_restore:
                                link = _find_link(net, link_pair[0], link_pair[1])
                                if link is not None:
                                    left_params, right_params = throttle_restore
                                    _restore_link_params(link, left_params, right_params)

                        if net is not None:
                            try:
                                net.stop()
                            except Exception:
                                pass
                        if controller_process is not None:
                            _stop_controller_process(controller_process, controller_log_stream)
    finally:
        if output_stream is not sys.stdout:
            output_stream.close()


def main(argv=None):
    args = build_parser().parse_args(argv)
    run_scenarios(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
