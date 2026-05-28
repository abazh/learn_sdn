# SPF Experiment Index — Katalog Pipeline & Tracking Evaluasi

**Purpose**: Dokumentasi referensi lengkap untuk semua komponen pipeline eksperimen Topik 1, memudahkan logging, verification, dan evaluation tracking.

**Last Updated**: 2026-05-28

---

## 📋 Quick Navigation

- [Komponen & Inventory](#komponen--inventory)
- [Testing Status](#testing-status)
- [Sample Data & Outputs](#sample-data--outputs)
- [Pipeline Execution Checklist](#pipeline-execution-checklist)
- [Evaluation Tracking Template](#evaluation-tracking-template)
- [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md)
- [Topik 1 Guide Index](SPF/docs/topik1-az-guide/INDEX.md)
- [Known Gaps & Recommendations](#known-gaps--recommendations)

---

## Komponen & Inventory

### 1. Topologi (Emulator: Mininet)

| Nama | File | Status | Switches | Hosts | Link BW | Default CLI | Notes |
|------|------|--------|----------|-------|---------|-------------|-------|
| Ring-5 | `SPF/topo-ring5_lab.py` | ✅ Active | 5 | 10 (2/switch) | 100 Mbps | `--topologies ring5` | Fokus utama |
| Jellyfish | `SPF/jellyfish_topo.py` | ✅ Active | param | param | 100 Mbps | `--topologies jellyfish` | Fokus utama; param-driven |
| SPF Lab | `SPF/topo-spf_lab.py` | ✅ Available | ? | ? | ? | - | Tidak di CLI default |
| Mesh | `SPF/topo-mesh_lab.py` | ✅ Available | ? | ? | ? | - | Tidak di CLI default |
| Weighted | `SPF/topo-weighted_lab.py` | ✅ Available | ? | ? | ? | - | Tidak di CLI default |

**Jellyfish CLI Parameters**:
- `--jellyfish-switches` (default: 10)
- `--jellyfish-ports` (default: 4)
- `--jellyfish-sw-ports` (default: 3)
- `--jellyfish-seed` (default: 42) → deterministic generation

### 2. Algoritma & Controllers

| Algoritma | Algorithm File | Controller File | Testing | CLI | Notes |
|-----------|----------------|-----------------|---------|-----|-------|
| A* | `SPF/algorithms/astar.py` | `SPF/astar_osken_controller.py` | ✅ `test_astar.py` | `--algorithms astar` | Heuristic-based |
| Bellman-Ford | `SPF/algorithms/bellman_ford.py` | `SPF/bellman_ford_osken_controller.py` | ✅ `test_bellman_ford.py` | `--algorithms bellman_ford` | Negative-cycle detect |
| Widest-Path | `SPF/algorithms/widest_path.py` | `SPF/widest_path_osken_controller.py` | ✅ `test_widest_path.py` | `--algorithms widest_path` | Link capacity-aware |
| A* Multipath | `SPF/algorithms/astar.py` | `SPF/astar_multipath_osken_controller.py` | - | - | Multipath variant |
| Dijkstra | `SPF/algorithms/dijkstra.py` | `SPF/dijkstra_osken_controller.py` | ✅ `test_dijkstra.py` | - | Tidak di CLI fokus |
| Suurballe | `SPF/algorithms/suurballe.py` | `SPF/suurballe_*.py` (2 variants) | ✅ `test_suurballe.py` | - | Tidak di CLI fokus |
| Yen K-Shortest | `SPF/algorithms/yen_k_shortest.py` | `SPF/kshortest_osken_controller.py` | ✅ `test_yen_k_shortest.py` | - | Tidak di CLI fokus |
| Floyd-Warshall | `SPF/algorithms/floyd_warshall.py` | `SPF/floyd_warshall_osken_controller.py` | ✅ `test_floyd_warshall.py` | - | Tidak di CLI fokus |
| Widest-Path | `SPF/algorithms/widest_path.py` | `SPF/widest_path_osken_controller.py` | ✅ `test_widest_path.py` | - | Tidak di CLI fokus |

**Base Controller**: `SPF/base_controller.py` — PacketIn handler, LLDP, FlowMod/PacketOut orchestration.

### 3. Benchmark & Orchestration

| Tool | File | Mode | Purpose | Input | Output | Status |
|------|------|------|---------|-------|--------|--------|
| Benchmark CLI | `SPF/benchmark_algorithms.py` | graph | Pure Python algorithm sweep | CLI args | JSONL | ✅ Active |
| Benchmark CLI | `SPF/benchmark_algorithms.py` | live | Mininet + iperf3 measurement | CLI args | JSONL | ✅ Active |
| Scenario Runner | `SPF/testing-code/run_live_scenarios.py` | scenario | Live + failure injection + tcpdump | CLI args | JSONL + PCAP | ✅ Active |
| JSONL→CSV | `SPF/benchmark_jsonl_to_csv.py` | converter | JSONL → split CSV per topology/algo | JSONL | CSV | ✅ Active |
| PCAP→CSV | `SPF/testing-code/pcap_to_csv.py` | parser | PCAP → CSV rows (scapy-based) | PCAP | CSV | ✅ Active |

**Benchmark Core** (shared library): `SPF/benchmark_core.py`
- `BenchmarkConfig` dataclass
- `TopologyGraph` representation
- Algorithm runners (`_run_astar`, `_run_bellman_ford`, `_run_widest_path`)
- Live orchestration helpers
- Utilities: `_wait_for_controller`, `_start_controller_process`, `_extract_iperf3_throughput`

### 4. Testing

| Test File | Purpose | Coverage | Status | Run Command |
|-----------|---------|----------|--------|-------------|
| `SPF/tests/test_astar.py` | A* algorithm correctness | pathfinding, heuristics | ✅ Pass | `pytest tests/test_astar.py -v` |
| `SPF/tests/test_bellman_ford.py` | Bellman-Ford correctness | relaxation, negative cycles | ✅ Pass | `pytest tests/test_bellman_ford.py -v` |
| `SPF/tests/test_widest_path.py` | Widest-Path correctness | bottleneck capacity | ✅ Pass | `pytest tests/test_widest_path.py -v` |
| `SPF/tests/test_dijkstra.py` | Dijkstra correctness | shortest path | ✅ Pass | `pytest tests/test_dijkstra.py -v` |
| `SPF/tests/test_floyd_warshall.py` | Floyd-Warshall correctness | all-pairs shortest paths | ✅ Pass | `pytest tests/test_floyd_warshall.py -v` |
| `SPF/tests/test_suurballe.py` | Suurballe correctness | edge-disjoint paths | ✅ Pass | `pytest tests/test_suurballe.py -v` |
| `SPF/tests/test_yen_k_shortest.py` | Yen K-Shortest correctness | k-shortest paths | ✅ Pass | `pytest tests/test_yen_k_shortest.py -v` |
| `SPF/tests/test_benchmark_core.py` | Benchmark core functionality | config parsing, topology loading, JSON serialization | ✅ Pass | `pytest tests/test_benchmark_core.py -v` |
| `SPF/tests/test_group_ids.py` | Group ID management | multipath group handling | ✅ Pass | `pytest tests/test_group_ids.py -v` |

**Run all tests**:
```bash
cd SPF && python3 -m pytest tests/ -v
```

---

## Testing Status

### Unit Tests (✅ All Passing)
- Algorithm correctness: 8/8 tests pass
- Benchmark core: 1/1 test pass (validates BenchmarkConfig, topology loading, JSON serialization)

### Integration Testing
- **Graph-mode**: `SPF/benchmark_algorithms.py --mode graph` produces valid JSONL (verified with sample data)
- **Live-mode**: `SPF/benchmark_algorithms.py --mode live --topologies ring5 --algorithms widest_path` produces JSONL with iperf3 throughput (verified with sample)
- **Scenario mode**: `run_live_scenarios.py` orchestrates Mininet + tcpdump + failures (code reviewed, needs runtime validation)
- **Run logging**: `SPF/docs/pipeline-planning/03-run-log-template.md` is the canonical template for live/scenario run logs

### Known Test Limitations
- No Mininet integration tests in pytest (requires live system setup)
- PCAP→CSV parser requires scapy (optional dependency, not tested in CI)
- Run-level manifest generation is documented but not yet automated in the codebase

---

## Sample Data & Outputs

### Graph-Mode Sample
- **File**: `SPF/benchmark-results.jsonl`
- **Topology**: ring5
- **Algorithm**: astar
- **Records**: 10 (all host pairs from h1)
- **Fields**: timestamp, topology, algorithm, repeat_index, source_host, destination_host, source_switch, destination_switch, hop_count, path_cost, path_string, throughput_estimate_mbps, runtime_ms, status
- **Sample Record**: 
  ```json
  {"algorithm": "astar", "benchmark_mode": "graph", "hop_count": 1, "path_cost": 1, "path_string": "s1 -> s5", "path_switches": ["s1", "s5"], "runtime_ms": 0.01924, "source_host": "h1", "source_switch": "s1", "status": "success", "throughput_estimate_mbps": 100.0, ...}
  ```

### Live-Mode Sample
- **File**: `SPF/benchmark-live.jsonl`
- **Topology**: ring5
- **Algorithm**: widest_path
- **Records**: 3 (host pairs)
- **Additional Fields**: controller_pid, controller_port, iperf_duration_s, iperf_parallel, iperf_summary (JSON complex), throughput_mbps (95-99 Mbps)
- **Sample Record**:
  ```json
  {"algorithm": "widest_path", "benchmark_mode": "live", "throughput_mbps": 95.51563965461116, "controller_pid": 9435, "controller_port": 6653, "iperf_summary": {...}, ...}
  ```

### CSV Outputs
- **Location**: `SPF/benchmark-csv/`
- **Format**: One CSV per topology-algorithm pair
- **Files Expected**:
  - `topology-ring5_algorithm-astar.csv`
  - `topology-ring5_algorithm-bellman_ford.csv`
  - `topology-ring5_algorithm-widest_path.csv`
  - `topology-jellyfish_algorithm-astar.csv`
  - `topology-jellyfish_algorithm-bellman_ford.csv`
  - `topology-jellyfish_algorithm-widest_path.csv`
- **Column Count**: 40+ columns (timestamp, topology, algorithm, repeat_index, hop_count, path_cost, source_host, destination_host, status, error, note, etc.)

### PCAP Outputs
- **Location**: `SPF/csv/pcap/<topology>/<algorithm>/<scenario>/<host>.pcap`
- **Example**: `SPF/csv/pcap/ring5/widest_path/baseline_no_failure/h1.pcap`
- **Parsed CSV**: `SPF/csv/pcap-csv/<topology>/<algorithm>/<scenario>/<host>.csv`
- **Fields**: timestamp, topology, algorithm, scenario, host, src_mac, dst_mac, src_ip, dst_ip, proto, src_port, dst_port, length

---

## Pipeline Execution Checklist

### Pre-Experiment Validation
- [ ] Python 3.8+: `python3 --version`
- [ ] Required packages: `pip list | grep -E 'mininet|osken|scapy'`
- [ ] Test suite passes: `cd SPF && python3 -m pytest tests/ -v`
- [ ] Benchmark CLI works: `python3 SPF/benchmark_algorithms.py --help`

### Graph-Mode Execution (Fasa 1)
- [ ] Run Ring-5 graph: `python3 SPF/benchmark_algorithms.py --mode graph --topologies ring5 --algorithms astar bellman_ford widest_path > ring5-graph.jsonl`
- [ ] Record output rows: _____ (expected: 45 rows = 3 algo × 5 src switch × 3 dst switch)
- [ ] Verify JSONL valid: `cat ring5-graph.jsonl | wc -l`
- [ ] Convert to CSV: `python3 SPF/benchmark_jsonl_to_csv.py --input ring5-graph.jsonl --output-dir csv-ring5`
- [ ] Verify CSV files: `ls csv-ring5/` (expect 3 files)
- [ ] Repeat for Jellyfish: `python3 SPF/benchmark_algorithms.py --mode graph --topologies jellyfish --algorithms astar bellman_ford widest_path > jellyfish-graph.jsonl`

### Live-Mode Execution (Fasa 2)
- [ ] Mininet available: `which mn`
- [ ] OSKen running or available: check installation
- [ ] Run live Ring-5: `python3 SPF/benchmark_algorithms.py --mode live --topologies ring5 --algorithms widest_path --max-pairs 3 > ring5-live.jsonl`
- [ ] Record throughput (Mbps): _____ (expected: ~90-100 Mbps)
- [ ] Repeat for other algorithms (loop or manual)
- [ ] Repeat for Jellyfish topology

### Scenario Execution (Fasa 3)
- [ ] Sudo permissions: `sudo -l 2>/dev/null | grep -q mininet && echo yes`
- [ ] Run baseline scenario: `sudo python3 SPF/testing-code/run_live_scenarios.py --topologies ring5 --algorithms widest_path --scenarios baseline_no_failure --output scenario-baseline.jsonl --pcap-dir pcap-baseline`
- [ ] Record PCAP count: _____ (expected: 10 PCAP files = 2 host pair × 5 hosts)
- [ ] Run failure scenario: `sudo python3 SPF/testing-code/run_live_scenarios.py --topologies ring5 --algorithms widest_path --scenarios link_down_before_traffic --output scenario-failure.jsonl --pcap-dir pcap-failure`
- [ ] Parse PCAP: `python3 SPF/testing-code/pcap_to_csv.py --pcap-dir pcap-baseline --output-dir pcap-csv`

### Analysis (Fasa 4)
- [ ] Aggregate CSV: compute mean/stddev hop_count, runtime_ms, throughput per algorithm
- [ ] Generate comparison table: algorithm vs hop_count vs throughput
- [ ] Generate plots: optional (barplot algorithms vs metric)
- [ ] Document findings: record in laporan/*.md

---

## Evaluation Tracking Template

Use this template untuk log setiap eksperimen run. Copy-paste ke file baru `SPF/csv/RUN_LOG_YYYYMMDD_HHMMSS.md`, atau gunakan [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) sebagai canonical run log.

```markdown
# Experiment Run — [Tanggal Waktu]

## Setup
- **Host**: [OS / hardware]
- **Python**: `python3 --version`
- **Mininet**: `mn --version` (if live mode)
- **OSKen**: [version if available]
- **Branch**: `git rev-parse --abbrev-ref HEAD`
- **Commit**: `git rev-parse --short HEAD`

## Experiment Phase
### Fasa 1: Graph-Mode
- **Command**:
  ```
  python3 SPF/benchmark_algorithms.py --mode graph --topologies ring5 jellyfish --algorithms astar bellman_ford widest_path > [output-file].jsonl
  ```
- **Output File**: [filename]
- **Total Records**: [count] (expected: ~90 if ring5 + jellyfish)
- **Duration**: [seconds]
- **Status**: ✅ Success / ❌ Failed
- **Notes**: [any issues or observations]

### Fasa 2: Live-Mode
- **Command Ring-5**:
  ```
  python3 SPF/benchmark_algorithms.py --mode live --topologies ring5 --algorithms widest_path --max-pairs 5 > [ring5-live].jsonl
  ```
- **Output File**: [filename]
- **Records**: [count]
- **Throughput (Mbps)**: mean=[X], min=[X], max=[X]
- **Duration**: [seconds]
- **Status**: ✅ Success / ❌ Failed

- **Command Jellyfish**:
  ```
  python3 SPF/benchmark_algorithms.py --mode live --topologies jellyfish --algorithms astar --max-pairs 5 > [jelly-live].jsonl
  ```
- **Output File**: [filename]
- **Records**: [count]
- **Throughput (Mbps)**: mean=[X], min=[X], max=[X]
- **Duration**: [seconds]
- **Status**: ✅ Success / ❌ Failed

### Fasa 3: Scenario
- **Command**:
  ```
  sudo python3 SPF/testing-code/run_live_scenarios.py --topologies ring5 --algorithms widest_path --scenarios baseline_no_failure link_flap --output [scenario].jsonl --pcap-dir [pcap-dir]
  ```
- **Output JSONL**: [filename]
- **PCAP Count**: [total files]
- **Duration**: [seconds]
- **Status**: ✅ Success / ❌ Failed

### Fasa 4: Analysis
- **CSV Conversion**:
  ```
  python3 SPF/benchmark_jsonl_to_csv.py --input [input].jsonl --output-dir [csv-dir] --split-by topology,algorithm
  ```
- **CSV Files Generated**: [count]
- **Sample Stats** (from CSV):
  - Ring5 + A*: hop_count mean=[X], runtime_ms mean=[X]ms
  - Ring5 + Bellman-Ford: hop_count mean=[X], runtime_ms mean=[X]ms
  - Ring5 + Widest-Path: hop_count mean=[X], runtime_ms mean=[X]ms
  - Jellyfish + A*: hop_count mean=[X], runtime_ms mean=[X]ms
  - [repeat for other combos]

## Issues & Resolutions
- **Issue 1**: [description]
  - **Resolution**: [what did you do]
  - **Status**: ✅ Resolved / ⏳ Pending

- **Issue 2**: [description]
  - **Resolution**: [what did you do]
  - **Status**: ✅ Resolved / ⏳ Pending

## Observations & Insights
- [Key finding 1]
- [Key finding 2]
- [Question for next iteration]

## Next Steps
- [ ] [Action item 1]
- [ ] [Action item 2]

---
*End of Run Log*
```

---

## Known Gaps & Recommendations

### Not Yet Implemented
| Gap | File | Priority | Impact | Recommendation |
|-----|------|----------|--------|-----------------|
| Config orchestration | `SPF/experiments/config.yaml` + runner | MEDIUM | Need YAML-based matrix for reproducibility | Create YAML schema + `SPF/testing-code/run_experiment.py` wrapper |
| Convergence measurement | `SPF/testing-code/convergence_time.py` | LOW-MEDIUM | Can't measure time-to-stable-state | Polling-based or log-parsing helper |
| Visualization notebook | `SPF/analysis/plot_results.ipynb` | NICE-TO-HAVE | Manual CSV analysis slower | Create Jupyter notebook for aggregation & plotting |

### Data Collection Limitations
- **Live-mode constraint**: 1 topology + 1 algorithm per run (use shell loop for matrix)
- **PCAP parsing**: Requires optional `scapy` install (`pip install scapy`)
- **No Mininet CI**: Integration tests require live system; unit tests only

### Reproducibility Notes
- Jellyfish topology uses seed for determinism; same seed → same topology
- Link bandwidth defaults to 100 Mbps if not in topology metadata
- iperf3 parallel streams & duration configurable via CLI
- PCAP capture limited by disk space; use `--max-pairs` to limit hosts

---

## Navigation & Links

### Main Documentation
- [Experiment Plan](SPF/experiment_plan.md) — detailed architecture & checklist
- [README](SPF/README.md) — quick-start & overview
- [Algorithm Docs](SPF/docs/) — per-algorithm deep dives
- [Live-Mode Planning](SPF/docs/pipeline-planning/01-live-mode-planning.md) — robust execution, logging, and evaluation standard
- [Scenario-Mode Planning](SPF/docs/pipeline-planning/02-scenario-mode-planning.md) — failure injection, PCAP, and recovery analysis standard
- [Run Log Template](SPF/docs/pipeline-planning/03-run-log-template.md) — operational template for live/scenario run logs

### Benchmark Utilities
- Main CLI: `SPF/benchmark_algorithms.py`
- Core library: `SPF/benchmark_core.py`
- Scenario runner: `SPF/testing-code/run_live_scenarios.py`
- Converters: `SPF/benchmark_jsonl_to_csv.py`, `SPF/testing-code/pcap_to_csv.py`

### Sample Data
- Graph-mode: `SPF/benchmark-results.jsonl` (ring5 sample)
- Live-mode: `SPF/benchmark-live.jsonl` (ring5 sample)
- CSV templates: `SPF/benchmark-csv/` (after conversion)

### Test Suite
- All tests: `SPF/tests/`
- Run: `cd SPF && python3 -m pytest tests/ -v`

---

## Metadata

| Key | Value |
|-----|-------|
| Created | 2026-05-28 |
| Last Updated | 2026-05-28 |
| Topik | Topik 1: SPF Algorithm Comparison (A*, Bellman-Ford, Widest-Path) |
| Fokus Topologi | Ring-5, Jellyfish |
| Fokus Algoritma | A*, Bellman-Ford, Widest-Path |
| Pipeline Status | ✅ Core complete, ⏳ Optional features pending |
| Test Coverage | ✅ Unit tests pass; ⏳ Integration tests need runtime validation |
| Run Log Template | ✅ Available at `SPF/docs/pipeline-planning/03-run-log-template.md` |
| Local Guide Index | ✅ Available at `SPF/docs/topik1-az-guide/INDEX.md` |

---

*File ini adalah referensi master untuk semua komponen & tracking eksperimen. Update setiap kali menambah features atau run eksperimen baru.*
