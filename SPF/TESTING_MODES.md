# SPF Testing Modes — Perbandingan & Capabilities

**Purpose**: Dokumentasi lengkap perbedaan graph-mode vs live-mode vs scenario testing, capabilities masing-masing, dan guidance untuk evaluasi.

**Last Updated**: 2026-05-28

---

## 📊 Quick Comparison Table

| Aspek | Graph-Mode | Live-Mode | Scenario-Mode |
|------|-----------|-----------|---------------|
| **Mininet Emulation** | ❌ Tidak | ✅ Ya (full topology) | ✅ Ya (full topology) |
| **OSKen Controller** | ❌ Tidak | ✅ Ya (running) | ✅ Ya (running) |
| **Actual Network I/O** | ❌ In-memory only | ✅ Ya (via Mininet emulation) | ✅ Ya (via Mininet emulation) |
| **Traffic Generation** | ❌ Tidak | ✅ iperf3 TCP streams | ✅ iperf3 TCP streams |
| **Real Throughput** | ❌ Null (estimated only) | ✅ Ya (95-100 Mbps typical) | ✅ Ya (varies with failures) |
| **Packet Capture (PCAP)** | ❌ Tidak | ❌ Tidak | ✅ Ya (tcpdump per-host) |
| **Failure Injection** | ❌ Tidak | ❌ Tidak | ✅ Ya (7 scenario types) |
| **Recovery Measurement** | ❌ Tidak | ❌ Tidak | ✅ Ya (convergence time, loss) |
| **Required Tools** | Python 3.8+ | Mininet, OSKen | Mininet, OSKen, sudo |
| **Typical Runtime** | ~1-5 sec | ~1-2 min per algo | ~5-10 min per scenario |
| **Output Size** | Small (100 KB) | Medium (500 KB - 2 MB) | Large (10-100 MB with PCAP) |
| **Reproducibility** | ✅ Perfect (pure Python) | ⚠️ Good (network timing varies) | ⚠️ Fair (failure timing vars) |

### Logging and Audit Model

| Aspect | Graph-Mode | Live-Mode | Scenario-Mode |
|------|-----------|-----------|---------------|
| **Record-Level Metadata** | topology, algorithm, path, runtime | topology, algorithm, path, throughput, RTT | scenario, failure, PCAP paths, packet loss |
| **Run-Level Metadata** | command line, git commit, git branch, output dir | command line, git commit, git branch, controller log path, output dir | command line, git commit, git branch, scenario seed, output dir, pcap dir |
| **Recommended Log File** | JSONL + CSV | JSONL + CSV + optional run log | JSONL + CSV + PCAP + optional run log |
| **Template to Use** | [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) | [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) | [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) |

---

## 🔍 Mode Descriptions & Capabilities

### Mode 1: Graph-Mode — Algorithm Correctness Testing

**What It Does:**
```
Load topology definition → Convert to graph → Run pure Python algorithm → Measure time & path
```

**Execution Flow (Code Reference)**:
```python
# SPF/benchmark_algorithms.py
records = benchmark_records(config)  # ← Pure Python, no Mininet

# SPF/benchmark_core.py
def benchmark_records(config: BenchmarkConfig):
    for topology_name in config.topologies:
        graph = build_topology_graph(topology_name, config)  # ← Abstract graph
        for algorithm_name in config.algorithms:
            for src_host, dst_host in _ordered_host_pairs(...):
                record = _build_algorithm_record(...)  # ← Call algo: astar(), bellman_ford(), widest_path()
                yield record
```

**What's NOT Included:**
- ❌ Mininet network emulation
- ❌ OSKen controller
- ❌ Actual packet switching
- ❌ Real traffic/throughput

**Metrics Captured**:
```json
{
  "benchmark_mode": "graph",
  "topology": "ring5",
  "algorithm": "astar",
  "source_switch": "s1",
  "destination_switch": "s5",
  "hop_count": 1,
  "path_cost": 1.0,
  "path_string": "s1 -> s5",
  "path_switches": ["s1", "s5"],
  "runtime_ms": 0.01924,
  "throughput_estimate_mbps": 100.0,
  "throughput_mbps": null,
  "status": "success"
}
```

**Use Cases**:
- ✅ Validate algorithm correctness (returns valid paths)
- ✅ Compare hop count per algorithm (algorithm quality)
- ✅ Benchmark algorithm speed (runtime_ms comparison)
- ✅ Detect algorithm bugs early (before Mininet)
- ✅ Quick regression testing
- ✅ Use [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) for run-level audit metadata

**Evaluation Questions Answered**:
1. "Does A* find shorter paths than Bellman-Ford?" → **YES** (compare hop_count)
2. "Which algorithm is fastest?" → **runtime_ms comparison**
3. "What's the path cost on Ring-5?" → **path_cost values**
4. "Does algorithm fail on any topology?" → **status field**

**Typical Output** (Ring-5 + 3 algorithms):
- Records: ~45 (5 source switches × 3 destination switches × 3 algorithms)
- File size: ~50-100 KB JSONL
- Runtime: ~1-5 seconds

**Limitations**:
- ❌ No network behavior validation
- ❌ No real throughput (can't measure switching/queueing delays)
- ❌ No controller overhead accounted
- ❌ No failure scenarios

---

### Mode 2: Live-Mode — End-to-End Real Network Testing

**What It Does:**
```
Spawn Mininet network → Start OSKen controller → Run iperf3 traffic → Measure real throughput
```

**Execution Flow (Code Reference)**:
```python
# SPF/benchmark_algorithms.py
records = benchmark_records_live(config, ...)  # ← Live network execution

# SPF/benchmark_core.py
def benchmark_records_live(config, ...):
    topo = load_topology(topology_name, config)  # ← Mininet Topo
    net = Mininet(topo=topo, controller=RemoteController(...))
    net.start()  # ← SPAWN actual emulated network
    
    process = _start_controller_process(algorithm_name)  # ← Start OSKen
    _wait_for_controller()  # ← Wait until ready
    
    for src_host, dst_host in _limited_host_pairs(...):
        throughput = _run_live_iperf3(src_host, dst_host, ...)  # ← Actual traffic
        record = _build_algorithm_record(..., throughput=throughput)
        yield record
    
    net.stop()
    _stop_controller_process(process)
```

**What's Included**:
- ✅ Full Mininet network (actual switches, hosts, links)
- ✅ OSKen controller (running in background)
- ✅ PacketIn/FlowMod/PacketOut exchanges
- ✅ Real iperf3 TCP traffic (5 seconds per pair by default)
- ✅ Real throughput measurement

**Metrics Captured** (additionally):
```json
{
  "benchmark_mode": "live",
  "throughput_mbps": 95.51563965461116,
  "controller_pid": 9435,
  "controller_port": 6653,
  "iperf_duration_s": 5,
  "iperf_parallel": 1,
  "iperf_summary": {
    "sum_sent": {
      "bits_per_second": 99821240.92029054,
      "bytes": 62390272,
      "retransmits": 0
    },
    "sum_received": {
      "bits_per_second": 95515639.65461117,
      "bytes": 62389992
    },
    "cpu_utilization_percent": {
      "host_total": 0.7546277128168928,
      "host_user": 0.07261966178337576,
      "host_system": 0.682027946831266,
      "remote_total": 1.7150760083979821,
      "remote_user": 0.28012410581028835,
      "remote_system": 1.43497103936224
    },
    "receiver_tcp_congestion": "cubic",
    "sender_tcp_congestion": "cubic"
  },
  "traffic_tool": "iperf3",
  "traffic_protocol": "tcp"
}
```

**Use Cases**:
- ✅ Measure real throughput per algorithm on actual (emulated) network
- ✅ Compare algorithm performance end-to-end (graph-mode + network overhead)
- ✅ Validate controller can install flows correctly
- ✅ Benchmark Mininet + OSKen coordination
- ✅ Measure latency (RTT from iperf3, visible in iperf_summary)
- ✅ Detect network congestion/retransmits
- ✅ Record run-level metadata separately using [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md)

**Evaluation Questions Answered**:
1. "What real throughput does each algorithm achieve?" → **throughput_mbps comparison** (95-100 Mbps typical)
2. "Does TCP congestion control work?" → **iperf_summary.sum_sent.retransmits** (should be 0 on clean link)
3. "Where's the controller bottleneck?" → **cpu_utilization_percent** (should be <5% for clean scenario)
4. "Which algorithm has lower latency?" → **iperf_summary RTT fields** (mean_rtt, min_rtt, max_rtt)
5. "Does controller properly handle parallel streams?" → Set `--iperf-parallel` > 1, compare throughput

**Typical Output** (Ring-5 + widest_path, 5 host pairs):
- Records: 5 (one per host pair)
- File size: ~100-200 KB JSONL (iperf_summary is complex)
- Runtime: ~1-2 minutes (includes controller startup + 5 sec per pair × 5 pairs)

**Limitations**:
- ❌ Controller startup overhead each run (can be 10-30 sec)
- ❌ No failure scenarios (link/switch failures)
- ❌ Mininet timing not exactly same as real network (but close for qualitative comparison)
- ❌ Single algorithm per run (use shell loop for matrix)

---

### Mode 3: Scenario-Mode — Robustness & Failure Testing

**What It Does:**
```
Spawn Mininet + controller → Inject failures (link down, switch down, throttle, flaps) → Capture PCAP → Measure recovery
```

**Execution Flow (Code Reference)**:
```python
# SPF/testing-code/run_live_scenarios.py
def run_scenarios(args):
    net = Mininet(...)
    net.start()  # ← SPAWN network
    process = _start_controller_process(algorithm_name)
    
    for scenario in scenarios:
        # Inject failure
        if scenario.action == "link_down":
            _set_link_status(net, "s1", "s2", "down")  # ← INJECT failure
        elif scenario.action == "throttle":
            _throttle_link(link, bw_mbps=20.0, delay_ms=50)
        
        # Capture PCAP & run traffic
        tcpdump_pids = _start_tcpdump(net, ...)
        _run_live_iperf3(src_host, dst_host, ...)
        _stop_tcpdump(net, tcpdump_pids)
        
        # Record metrics
        record = _build_algorithm_record(..., scenario_name=scenario.name, ...)
        yield record
```

**What's Included**:
- ✅ All from live-mode
- ✅ 7 failure scenario types (baseline, link_down_pre, link_down_during, link_flap, switch_down, bandwidth_throttle, random_link_down)
- ✅ tcpdump PCAP capture per-host
- ✅ Packet loss measurement (pingall_loss_pct)
- ✅ Failure timing and recovery logging

**Metrics Captured** (additionally):
```json
{
  "scenario_name": "link_down_before_traffic",
  "scenario_phase": "pre",
  "scenario_index": 0,
  "link_action": "link_down",
  "link_target": "s1-s2",
  "switch_target": null,
  "link_timing_s": 0.0,
  "pingall_loss_pct": 100,
  "tcpdump_pcap_paths": ["SPF/csv/pcap/ring5/widest_path/link_down_before_traffic/h1.pcap"],
  "tcpdump_csv_paths": ["SPF/csv/pcap-csv/ring5/widest_path/link_down_before_traffic/h1.csv"],
  "throttle_bw_mbps": null,
  "throttle_delay_ms": null
}
```

**7 Scenario Types** (available via `--scenarios`):

| Scenario | Phase | Action | Use Case |
|----------|-------|--------|----------|
| `baseline_no_failure` | baseline | None | Baseline throughput (no failure) |
| `link_down_before_traffic` | pre | link_down | Reroute before traffic starts |
| `link_down_during_traffic` | during | link_down | Reroute mid-traffic (recovery) |
| `link_flap` | during | link_flap | Link toggling (instability test) |
| `switch_down` | pre | switch_down | Full switch failure, all links down |
| `bandwidth_throttle` | pre | throttle | Bandwidth reduction (congestion sim) |
| `random_link_down_jellyfish` | pre | link_down (random) | Random link (Jellyfish-specific) |

**Use Cases**:
- ✅ Measure algorithm resilience to failures
- ✅ Compare recovery time across algorithms
- ✅ Measure packet loss during failure/recovery
- ✅ Capture packet traces for detailed analysis (PCAP → CSV)
- ✅ Benchmark controller convergence under stress
- ✅ Validate failover/rerouting behavior
- ✅ Keep scenario evidence, run-level metadata, and PCAP paths aligned via [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md)

**Evaluation Questions Answered**:
1. "Which algorithm recovers fastest after link failure?" → **Compare recovery metrics per algo**
2. "How many packets lost during failure?" → **pingall_loss_pct field**
3. "Does algorithm converge to new path before recovery?" → **Parse PCAP→CSV for timing**
4. "How stable is the throughput under link flaps?" → **Compare throughput variance across link_flap runs**
5. "Can Jellyfish handle random failures?" → **Run with random_link_down_jellyfish scenario**

**Typical Output** (Ring-5 + widest_path + 3 scenarios, 2 host pairs):
- Records: 6 (3 scenarios × 2 host pairs)
- PCAP files: ~30 (3 scenarios × 2 pairs × 5 hosts)
- File size: ~20-50 MB (includes PCAP)
- Runtime: ~5-10 minutes

**Limitations**:
- ⚠️ Requires sudo (for tcpdump)
- ⚠️ Slow (PCAP capture overhead)
- ⚠️ Large output (disk space needed)
- ⚠️ Timing of failures may vary (Mininet timing variability)

---

## 📈 Evaluation Workflow

### Logging First
Sebelum masuk ke fase evaluasi, siapkan [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) dan isi metadata run-level satu kali per eksekusi. Ini memastikan hasil graph-mode, live-mode, dan scenario-mode punya audit trail yang seragam.

### Step 1: Quick Algorithm Correctness (Graph-Mode)
```bash
python3 SPF/benchmark_algorithms.py --mode graph \
  --topologies ring5 \
  --algorithms astar bellman_ford widest_path \
  > phase1-graph.jsonl
```
**Questions to Answer:**
- ✅ Is hop_count reasonable for each algorithm?
- ✅ Does each algorithm complete (status=success)?
- ✅ Which is fastest (runtime_ms)?
- ✅ Was the run logged with the standard run log template?

### Step 2: Real Network Behavior (Live-Mode)
```bash
for algo in astar bellman_ford widest_path; do
  python3 SPF/benchmark_algorithms.py --mode live \
    --topologies ring5 \
    --algorithms $algo \
    --max-pairs 5 \
    > phase2-live-$algo.jsonl
done
```
**Questions to Answer:**
- ✅ What's real throughput per algorithm?
- ✅ Is throughput consistent or variable?
- ✅ Any retransmits (sign of congestion)?
- ✅ Latency comparison (RTT)?
- ✅ Is the run-level metadata captured once and not duplicated per record?

### Step 3: Failure Resilience (Scenario-Mode)
```bash
sudo python3 SPF/testing-code/run_live_scenarios.py \
  --topologies ring5 \
  --algorithms widest_path \
  --scenarios baseline_no_failure link_down_before_traffic link_flap \
  --output phase3-scenarios.jsonl \
  --pcap-dir phase3-pcap
```
**Questions to Answer:**
- ✅ Which algorithm recovers fastest?
- ✅ How much packet loss per scenario?
- ✅ Convergence time (from PCAP analysis)?
- ✅ Stability (throughput variance)?
- ✅ Do the JSONL, PCAP, CSV, and run log point to the same `run_id`?

---

## 📋 Metrics Summary by Mode

### Graph-Mode Metrics (Algorithm Quality)
| Metric | Field | Unit | Interpretation |
|--------|-------|------|-----------------|
| Path Length | `hop_count` | hops | Shorter = better |
| Path Cost | `path_cost` | cost units | Lower = better (widest-path uses capacity) |
| Computation Time | `runtime_ms` | milliseconds | Faster = better (for real-time routing) |
| Estimate Capacity | `throughput_estimate_mbps` | Mbps | Link bottleneck capacity |
| Status | `status` | success/error | Should be all success |

### Live-Mode Metrics (Network Performance)
| Metric | Field | Unit | Interpretation |
|--------|-------|------|-----------------|
| Real Throughput | `throughput_mbps` | Mbps | Actual TCP throughput (95-100 typical on emulated 100 Mbps link) |
| Retransmits | `iperf_summary.sum_sent.retransmits` | count | Lower = better (0 ideal) |
| RTT (min/mean/max) | `iperf_summary.min_rtt`, etc. | microseconds | Lower = better latency |
| CPU Utilization | `iperf_summary.cpu_utilization_percent` | % | Controller + host CPU (should be <5% clean) |
| Congestion Algorithm | `iperf_summary.receiver/sender_tcp_congestion` | cubic/reno/etc | TCP flavor in use |

### Logging Checklist (Applies to Live and Scenario)
- Record run-level metadata once per run, not per record.
- Store command line, git branch, and git commit in the run log or manifest.
- Keep JSONL focused on record-level measurements.
- Ensure `run_id` is present in JSONL and in the run log.
- Use the run log template as the audit entry point.

### Scenario-Mode Metrics (Robustness)
| Metric | Field | Unit | Interpretation |
|--------|-------|------|-----------------|
| Packet Loss | `pingall_loss_pct` | % | Lower = better (0 after recovery) |
| Recovery Time | (from PCAP) | seconds | Faster = better |
| Loss Duration | (timestamp diff) | seconds | Shorter = better |
| Throughput Under Failure | `throughput_mbps` (during scenario) | Mbps | Compare vs baseline |
| PCAP Analysis | tcpdump captures | packets | Detailed timing of recovery |
| Audit Trail | run log + `run_id` | traceability | Required for reproducibility and follow-up |

---

## 🎯 Typical Evaluation Matrix

For comprehensive algorithm comparison:

```
┌─────────────────────────────────────────────────────────────┐
│ Evaluation: SPF Algorithm Comparison (Topik 1)              │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: Graph-Mode (Algorithm Quality)                     │
│  → A* vs Bellman-Ford vs Widest-Path: hop_count, runtime    │
│  → Topology: Ring-5, Jellyfish                              │
│  → Output: hop_count_comparison, runtime_comparison tables  │
│                                                             │
│ Phase 2: Live-Mode (Network Performance)                    │
│  → A* vs Bellman-Ford vs Widest-Path: throughput, latency   │
│  → Topology: Ring-5, Jellyfish                              │
│  → Output: throughput_table, latency_table, stability_plot  │
│                                                             │
│ Phase 3: Scenario-Mode (Robustness)                         │
│  → Widest-Path (best from Phase 2): recovery time, loss     │
│  → Scenarios: baseline, link_down, link_flap                │
│  → Output: recovery_time_table, packet_loss_analysis        │
│                                                             │
│ Final: Synthesis Report                                     │
│  → Best algorithm for Ring-5                                │
│  → Best algorithm for Jellyfish                             │
│  → Trade-offs (speed vs throughput vs robustness)           │
│  → Run log template attached for reproducibility            │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Output Structure by Mode

### Graph-Mode Output
```
benchmark-results.jsonl
└─ Records: topology, algorithm, runtime_ms, hop_count, path_cost

CSV conversion:
├─ topology-ring5_algorithm-astar.csv
├─ topology-ring5_algorithm-bellman_ford.csv
├─ topology-ring5_algorithm-widest_path.csv
├─ topology-jellyfish_algorithm-astar.csv
└─ ...
```

### Live-Mode Output
```
benchmark-live.jsonl
└─ Records: graph-mode fields + throughput_mbps, controller_pid, iperf_summary

CSV conversion:
├─ topology-ring5_algorithm-astar.csv (with throughput_mbps filled)
├─ topology-ring5_algorithm-bellman_ford.csv
└─ ...
```

### Scenario-Mode Output
```
scenario-results.jsonl
├─ Records: live-mode fields + scenario_name, link_action, pingall_loss_pct, tcpdump_pcap_paths
│
PCAP directory:
└─ pcap/
   ├─ ring5/
   │  ├─ widest_path/
   │  │  ├─ baseline_no_failure/
   │  │  │  ├─ h1.pcap
   │  │  │  ├─ h2.pcap
   │  │  │  └─ ...
   │  │  ├─ link_down_before_traffic/
   │  │  │  └─ ...
   │  │  └─ ...
   │  └─ ...
   └─ ...

PCAP CSV outputs:
└─ pcap-csv/
   └─ (same structure, .csv instead of .pcap)
```

---

## ⚠️ Key Considerations for Evaluation

### Reproducibility
- **Graph-mode**: Perfect reproducibility (pure Python, same input = same output)
- **Live-mode**: Good reproducibility (Mininet timing may vary ±5%), seed parameter helps
- **Scenario-mode**: Fair reproducibility (failure timing varies, use same seed for comparable runs)

### Scale
- **Graph-mode**: Can run 100+ topologies/algorithms (fast)
- **Live-mode**: Limited by Mininet (10-20 algorithms per session before memory issues)
- **Scenario-mode**: Very limited (few scenarios, long runtime)

### Accuracy vs Real Networks
- **Graph-mode**: 100% algorithmic accuracy, 0% network accuracy
- **Live-mode**: ~95% network accuracy (Mininet emulation is accurate), includes network overhead
- **Scenario-mode**: ~90% network accuracy, failure timing not perfect, but good for qualitative comparison

### Resource Requirements
- **Graph-mode**: Minimal (any computer)
- **Live-mode**: Moderate (Mininet needs 4GB+ RAM, OSKen needs Python + openflow lib)
- **Scenario-mode**: High (tcpdump, many processes, sudo required, large disk)

---

## 📝 Next Steps for Your Evaluation

1. **Run Phase 1 (Graph-Mode)** → Identify which algorithm computes shortest paths
2. **Run Phase 2 (Live-Mode)** → Validate real throughput per algorithm
3. **Run Phase 3 (Scenario-Mode - optional)** → Deep-dive robustness if time permits
4. **Aggregate CSV** → Create comparison tables
5. **Write findings** → Document in laporan/*.md

---

## References

- [Experiment Plan](SPF/experiment_plan.md) — detailed setup & commands
- [Experiment Index](SPF/EXPERIMENT_INDEX.md) — full inventory & checklist
- [README](SPF/README.md) — quick-start guide

---

*File ini adalah guide lengkap untuk memahami dan mengevaluasi setiap testing mode. Update setiap kali ada perubahan metodologi atau capability.*
