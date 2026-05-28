# Rencana Eksperimen — Topik 1: Analisis Perbandingan Algoritma Perutean SPF

## Ringkasan Topik
Topik: Analisis perbandingan Algoritma SPF — fokus pada `A*`, `Bellman-Ford`, dan `Widest-Path` pada lingkungan SDN (Mininet + OSKen).

## Arsitektur Eksperimen (komponen)

### Topologi (Emulator: Mininet)
- **Ring-5** (fokus utama): `SPF/topo-ring5_lab.py`
  - 5 switch, setiap switch ada 2 host.
  - Link bandwidth: 100 Mbps (default).
- **Jellyfish** (fokus utama): `SPF/jellyfish_topo.py`
  - Random-regular topology; dikonfigurasi via CLI (`--jellyfish-switches`, `--jellyfish-ports`, `--jellyfish-sw-ports`, `--jellyfish-seed`).
  - Default: 10 switches, 4 ports per switch, 3 switch-switch ports, seed=42.
- Topologi lain tersedia di repo (spf_lab, mesh_lab, weighted_lab) tetapi **tidak** termasuk dalam benchmark CLI default.

### Controller (OSKen-based)
- Base: `SPF/base_controller.py` — PacketIn handler, LLDP, flow installation via FlowMod/PacketOut.
- **Algoritma dalam fokus (3 pilihan di CLI)**:
  - `A*`: `SPF/astar_osken_controller.py` + `SPF/algorithms/astar.py`
  - `Bellman-Ford`: `SPF/bellman_ford_osken_controller.py` + `SPF/algorithms/bellman_ford.py`
  - `Widest-Path`: `SPF/widest_path_osken_controller.py` + `SPF/algorithms/widest_path.py`
- Algoritma lain tersedia di repo (Dijkstra, Suurballe, k-shortest, dll.) tetapi **tidak** dalam benchmark CLI default.

### Benchmark & Orchestration
- **Graph-mode**: `SPF/benchmark_algorithms.py --mode graph`
  - Jalankan algoritma pure Python tanpa Mininet/OpenFlow.
  - Output: JSONL dengan fields `runtime_ms`, `path_switches`, `hop_count`, `path_cost`, `throughput_estimate_mbps` (derived dari link capacity).
  - Default: `topology-ring5`, algoritma: `astar widest_path bellman_ford`, 1 repetisi.
  
- **Live-mode**: `SPF/benchmark_algorithms.py --mode live`
  - Spesial: hanya 1 topologi dan 1 algoritma per run (multi-topology/algorithm harus pakai loop shell).
  - Jalankan Mininet + controller, orchestrate iperf3 traffic antar host pairs.
  - Output: JSONL dengan `throughput_mbps` (diukur dari iperf3), `controller_pid`, `controller_port`.
  - Default: topologi ring5, algoritma astar, max_pairs unlimited, iperf_duration 5s, iperf_parallel 1 stream.

- **Scenario runner**: `SPF/testing-code/run_live_scenarios.py`
  - Run live Mininet + inject failures (link down, switch down, bandwidth throttle, flaps, dll).
  - 7 scenario types: baseline_no_failure, link_down_before_traffic, link_down_during_traffic, link_flap, switch_down, bandwidth_throttle, random_link_down_jellyfish.
  - Capture tcpdump per-host (PCAP → `SPF/csv/pcap/<topology>/<algorithm>/<scenario>/<host>.pcap`).
  - Output: JSONL ke stdout atau file (flag `--output`).
  - Default: topologies `ring5 jellyfish`, algorithms `astar bellman_ford widest_path`, semua scenarios, seed=1, max_pairs unlimited.

- **Utilities**:
  - `SPF/benchmark_jsonl_to_csv.py`: convert JSONL → CSV, split by fields (e.g., `--split-by topology,algorithm`).
  - `SPF/testing-code/pcap_to_csv.py`: parse PCAP (scapy) → CSV rows dengan src_ip, dst_ip, proto, ports, dll.

### Output & Telemetri
- **JSONL pipeline**: 
  - Graph-mode fields: `timestamp`, `topology`, `algorithm`, `repeat_index`, `source_host`, `destination_host`, `source_switch`, `destination_switch`, `status`, `runtime_ms`, `hop_count`, `path_cost`, `path_string`, `path_switches`, `bottleneck_mbps`, `throughput_estimate_mbps`, `throughput_mbps` (null di graph-mode).
  - Live-mode fields: + `controller_pid`, `controller_port`, `iperf_duration_s`, `iperf_parallel`, `iperf_summary` (JSON kompleks), `traffic_tool`, `traffic_protocol`.
  - Scenario-mode fields: + `scenario_name`, `scenario_phase`, `scenario_index`, `link_action`, `link_target`, `switch_target`, `link_timing_s`, `pingall_loss_pct`, `tcpdump_pcap_paths`, `tcpdump_csv_paths`, dll.
  
- **CSV**: 
  - Default columns: 40+ field (timestamp, benchmark_mode, topology, algorithm, repeat_index, hop_count, path_cost, status, error, note, dll).
  - Per-topology/per-algorithm CSV: `topology-ring5_algorithm-astar.csv`, dll.
  
- **PCAP**:
  - Struktur dir: `<pcap-dir>/<topology>/<algorithm>/<scenario>/<host>.pcap`.
  - CSV output (dari pcap_to_csv.py): `<topology>/<algorithm>/<scenario>/<host>.csv`.
  - Fields: timestamp, topology, algorithm, scenario, host, src_mac, dst_mac, src_ip, dst_ip, proto, src_port, dst_port, length.

## Fokus Eksperimen (dari rancangan Anda)
- Topologi: **Jellyfish dan Ring-5** (keduanya tersedia dan default di benchmark CLI).
- Algoritma: **A*, Bellman-Ford, Widest-Path** (default choices di CLI).
- Metrik: Latensi (ping), Throughput (iperf3, via `throughput_mbps` di live-mode), Hop count, Path cost, Waktu runtime algoritma.
- Deliverable: skrip topologi, diagram, tabel perbandingan metrik, analisis rekomendasi, dan insight konvergensi.

## CLI Reference

### Graph-mode Benchmark
```bash
python3 SPF/benchmark_algorithms.py \
  --mode graph \
  --topologies ring5 jellyfish \
  --algorithms astar widest_path bellman_ford \
  --repetitions 1 \
  --output benchmark-results.jsonl
```

**Output fields**: `topology`, `algorithm`, `source_host`, `destination_host`, `source_switch`, `destination_switch`, `hop_count`, `path_cost`, `path_string`, `throughput_estimate_mbps`, `runtime_ms`, `status`.

### Live-mode Benchmark (per topologi/algoritma)
```bash
# Ring-5
python3 SPF/benchmark_algorithms.py \
  --mode live \
  --topologies ring5 \
  --algorithms widest_path \
  --max-pairs 5 \
  --iperf-duration 5 \
  --iperf-parallel 1 \
  --output benchmark-live-ring5.jsonl

# Jellyfish
python3 SPF/benchmark_algorithms.py \
  --mode live \
  --topologies jellyfish \
  --algorithms astar \
  --jellyfish-switches 10 \
  --jellyfish-ports 4 \
  --jellyfish-sw-ports 3 \
  --jellyfish-seed 42 \
  --max-pairs 5 \
  --iperf-duration 5 \
  --output benchmark-live-jellyfish.jsonl
```

**Output fields**: graph-mode fields + `controller_pid`, `controller_port`, `iperf_duration_s`, `iperf_parallel`, `throughput_mbps` (dari iperf3), `iperf_summary` (JSON kompleks).

### Scenario Runner (Live + Failures)
```bash
sudo python3 SPF/testing-code/run_live_scenarios.py \
  --topologies ring5 jellyfish \
  --algorithms astar bellman_ford widest_path \
  --scenarios baseline_no_failure link_down_before_traffic link_flap bandwidth_throttle \
  --seed 1 \
  --output SPF/csv/live-scenarios.jsonl \
  --pcap-dir SPF/csv/pcap
```

**Available scenarios**: 
- `baseline_no_failure` — no failure, just measure traffic
- `link_down_before_traffic` — disable link before starting iperf3
- `link_down_during_traffic` — disable link mid-traffic
- `link_flap` — toggle link on/off during traffic
- `switch_down` — disable all links of a switch
- `bandwidth_throttle` — limit link capacity
- `random_link_down_jellyfish` — random link failure (jellyfish-specific)

**Output fields**: live-mode fields + `scenario_name`, `scenario_phase`, `scenario_index`, `link_action`, `link_target`, `link_timing_s`, `pingall_loss_pct`, `tcpdump_pcap_paths` (list of PCAP files).

### JSONL → CSV Conversion
```bash
python3 SPF/benchmark_jsonl_to_csv.py \
  --input benchmark-results.jsonl \
  --output-dir benchmark-csv \
  --split-by topology,algorithm
```

Produces:
- `topology-ring5_algorithm-astar.csv`
- `topology-ring5_algorithm-bellman_ford.csv`
- `topology-ring5_algorithm-widest_path.csv`
- `topology-jellyfish_algorithm-astar.csv`
- ... (one per topology/algorithm pair)

### PCAP → CSV Parsing
```bash
python3 SPF/testing-code/pcap_to_csv.py \
  --pcap-dir SPF/csv/pcap \
  --output-dir SPF/csv/pcap-csv
```

Requires `scapy` — install via `pip install scapy`.

---

## Checklist: apakah sudah ada di codebase

### Topologi & Controllers
- [x] Topologi Ring-5 (`SPF/topo-ring5_lab.py`) — ADA, 5 switch, 2 host/switch, 100 Mbps links
- [x] Topologi Jellyfish (`SPF/jellyfish_topo.py`) — ADA, random-regular, param-driven
- [x] Implementasi `A*` — ADA (`SPF/astar_osken_controller.py`, `SPF/algorithms/astar.py`)
- [x] Implementasi `Bellman-Ford` — ADA (`SPF/bellman_ford_osken_controller.py`, `SPF/algorithms/bellman_ford.py`)
- [x] Implementasi `Widest-Path` — ADA (`SPF/widest_path_osken_controller.py`, `SPF/algorithms/widest_path.py`)
- [x] Base controller (`SPF/base_controller.py`) — ADA, includes PacketIn handler, LLDP, flow installation

### Benchmark & Testing
- [x] Pytests untuk algoritma murni — ADA (`SPF/tests/test_astar.py`, `SPF/tests/test_bellman_ford.py`, `SPF/tests/test_widest_path.py`)
- [x] Unit test untuk benchmark core — ADA (`SPF/tests/test_benchmark_core.py`), validates BenchmarkConfig, topology loading, record fields
- [x] Benchmark graph-mode (JSONL) — ADA (`SPF/benchmark_algorithms.py --mode graph`)
  - Produces JSONL dengan runtime_ms, path_switches, hop_count, path_cost, throughput_estimate_mbps
- [x] Benchmark live-mode (iperf3) — ADA (`SPF/benchmark_algorithms.py --mode live`)
  - Produces JSONL dengan throughput_mbps (dari iperf3), controller_pid, controller_port
- [x] Scenario runner (live Mininet + failures) — ADA (`SPF/testing-code/run_live_scenarios.py`)
  - 7 scenario types: baseline_no_failure, link_down_before_traffic, link_down_during_traffic, link_flap, switch_down, bandwidth_throttle, random_link_down_jellyfish
  - Capture tcpdump per-host, inject link/switch failures, measure iperf3 throughput
- [x] JSONL→CSV converter — ADA (`SPF/benchmark_jsonl_to_csv.py`), supports split-by field
- [x] PCAP→CSV helper — ADA (`SPF/testing-code/pcap_to_csv.py`), requires scapy

### Sample Data
- [x] Contoh CSV hasil benchmark graph-mode Ring-5 — ADA (`SPF/benchmark-csv/topology-ring5_algorithm-*.csv`)
- [x] Contoh JSONL hasil benchmark graph-mode — ADA (`SPF/benchmark-results.jsonl`, terdapat ring5+astar contoh)
- [x] Contoh JSONL hasil benchmark live-mode — ADA (`SPF/benchmark-live.jsonl`, terdapat ring5+widest_path contoh)

## Checklist test & validasi untuk Topik 1
- [x] Correctness algoritma A* (unit tests) — tersedia di `SPF/tests/test_astar.py`
- [x] Correctness algoritma Bellman-Ford (unit tests) — tersedia di `SPF/tests/test_bellman_ford.py`
- [x] Correctness algoritma Widest-Path (unit tests) — tersedia di `SPF/tests/test_widest_path.py`
- [x] Validasi utilitas benchmark core — tersedia di `SPF/tests/test_benchmark_core.py`
- [ ] Uji integrasi live Mininet khusus matriks `ring5` + `jellyfish` untuk 3 algoritma (perlu dijalankan saat eksperimen final)
- [ ] Uji konvergensi eksplisit berbasis timestamp/log parsing (belum ada helper khusus)

## Kekurangan / Gap Fungsional yang Direkomendasikan

Berdasarkan audit lampiran, berikut artifact yang **tidak ditemukan** di repo dan direkomendasikan untuk ditambahkan:

1. **Config orchestration** (`SPF/experiments/config.yaml` + `SPF/testing-code/run_experiment.py`):
   - **Status**: NOT FOUND.
   - **Alasan dibutuhkan**: CLI parameter-based (`benchmark_algorithms.py`) cocok untuk single run, tetapi eksperimen matrix (combinatorial topology × algorithm × repetition) lebih mudah jika ada YAML config + runner orchestration.
   - **Proposasi**: 
     - File YAML Define kombinasi (ring5, jellyfish) × (astar, bellman_ford, widest_path) × (repetitions, iperf_duration).
     - Runner wrapper yang baca YAML, loop eksekusi benchmark per kombinasi.
   - **Prioritas**: MEDIUM — bisa diamankan dengan shell loop sementara.

2. **Convergence time measurement** (`SPF/testing-code/convergence_time.py`):
   - **Status**: NOT FOUND.
   - **Alasan dibutuhkan**: Scenario runner (`run_live_scenarios.py`) sudah capture tcpdump per-host, tetapi helper khusus untuk mengukur "time-to-convergence" (waktu hingga semua flow stabil) belum ada.
   - **Proposasi**:
     - Polling-based: query controller state (via dpctl atau remote API) untuk mendeteksi ketika semua flow installed.
     - Log-based: parse controller log untuk mendeteksi event `path_installed` atau `flow_mod_sent`.
     - Output: JSONL dengan `convergence_timestamp`, `convergence_ms` per source/destination pair.
   - **Prioritas**: LOW-MEDIUM — optional jika laporan fokus pada throughput/hop-count saja.

3. **Plotting & aggregation notebook** (`SPF/analysis/plot_results.ipynb`):
   - **Status**: NOT FOUND.
   - **Alasan dibutuhkan**: CSV outputs sudah ada dan siap untuk visualisasi; notebook bisa mengagregasi & menampilkan barplot/lineplot perbandingan algoritma per metrik.
   - **Proposasi**:
     - Load CSV (`topology-ring5_algorithm-*.csv`, dll).
     - Group by topology/algorithm, compute mean/stddev hop_count, throughput_estimate_mbps, runtime_ms.
     - Plot: hop_count vs algorithm (per topology), throughput vs algorithm, runtime vs algorithm.
   - **Prioritas**: NICE-TO-HAVE — eksperimen bisa pakai manual plotting jika diperlukan.

### Catatan Audit
- **Benchmark core telah teruji**: `test_benchmark_core.py` memvalidasi BenchmarkConfig parsing, topology loading, dan output field JSON serialization.
- **Live orchestration sudah baik**: `run_live_scenarios.py` sudah dalam production dengan 7 scenario types, tcpdump capture, failure injection.
- **CLI sudah fleksibel**: `benchmark_algorithms.py` support graph & live modes, split output, custom iperf3 params.
- **Pipeline sudah end-to-end**: JSONL → CSV → per-topology CSV sudah jalan, siap untuk analysis.

## Perubahan alur di codebase yang dicatat (apa yang ada/ditambahkan)

Dari audit lampiran, berikut snapshot state eksperimen:

### Pipeline Lengkap (Verified)
- **Graph-mode**: CLI → algorithm execution → JSONL (runtime_ms, hop_count, path_cost, throughput_estimate) → CSV.
- **Live-mode**: CLI → Mininet spawed → Remote OSKen controller → iperf3 traffic → JSONL (+ throughput_mbps, controller_pid) → CSV.
- **Scenario-mode**: CLI → orchestrate topology + controller + iperf3 + tcpdump + failure injection → JSONL (+ scenario fields) → separate CSV per topology/algorithm/scenario, PCAP→CSV parsing.

### Output Locations
- **JSONL**: stdout atau `--output` file (e.g., `benchmark-results.jsonl`).
- **CSV**: `--output-dir` (e.g., `SPF/benchmark-csv/topology-ring5_algorithm-astar.csv`).
- **PCAP**: `--pcap-dir` structure: `SPF/csv/pcap/<topology>/<algorithm>/<scenario>/<host>.pcap`.

### Contoh Data (verified present in repo)
- `SPF/benchmark-results.jsonl` — graph-mode ring5+astar sample (10 host pairs, hop_count 1-2, runtime ~0.01ms each).
- `SPF/benchmark-live.jsonl` — live-mode ring5+widest_path sample (3 pairs, throughput_mbps ~95 Mbps, iperf3 summary included).
- `SPF/benchmark-csv/topology-ring5_algorithm-*.csv` — converted CSV from graph-mode.

### Testing Coverage (Verified)
- Unit tests: `test_astar.py`, `test_bellman_ford.py`, `test_widest_path.py`, `test_benchmark_core.py`.
- Test suite validates: algorithm correctness (path finding, cost calculation), BenchmarkConfig parsing, topology graph building, JSON serialization.

### Repository Structure
```
SPF/
├── benchmark_algorithms.py           # CLI entry: graph & live modes
├── benchmark_core.py                 # Shared: BenchmarkConfig, topology loader, record builder
├── benchmark_jsonl_to_csv.py         # JSONL → CSV converter
├── algorithms/
│   ├── astar.py
│   ├── bellman_ford.py
│   ├── widest_path.py
│   └── ...
├── astar_osken_controller.py         # Controller implementations
├── bellman_ford_osken_controller.py
├── widest_path_osken_controller.py
├── topo-ring5_lab.py                 # Topologies
├── jellyfish_topo.py
├── testing-code/
│   ├── run_live_scenarios.py         # Scenario runner with failure injection
│   └── pcap_to_csv.py                # PCAP → CSV parsing
├── tests/
│   └── test_*.py                     # Unit tests
└── csv/
    ├── benchmark-results.jsonl       # Sample graph-mode output
    ├── benchmark-live.jsonl          # Sample live-mode output
    └── benchmark-csv/                # CSV outputs (populated after ConvERSION)
```

---

## Rekomendasi Langkah Eksperimen (prioritas urut)

### Fasa 1: Validasi & Baseline (segera dapat dijalankan)
1. **Jalankan graph-mode benchmark (no Mininet needed)**:
   ```bash
   python3 SPF/benchmark_algorithms.py \
     --mode graph \
     --topologies ring5 \
     --algorithms astar bellman_ford widest_path \
     --repetitions 3 \
     > baseline-ring5-graph.jsonl
   ```
   Expected output: ~30 records (5 topology.hosts × 3 algo × 2 repetitions), runtime <5 sec.

2. **Konversi ke CSV**:
   ```bash
   python3 SPF/benchmark_jsonl_to_csv.py \
     --input baseline-ring5-graph.jsonl \
     --output SPF/benchmark-csv/baseline-ring5.csv
   ```
   Expected output: 1 CSV dengan columns hop_count, path_cost, runtime_ms, algorithm, dst, src.

3. **Ulang untuk Jellyfish**:
   ```bash
   python3 SPF/benchmark_algorithms.py \
     --mode graph \
     --topologies jellyfish \
     --algorithms astar bellman_ford widest_path \
     --jellyfish-switches 8 --jellyfish-ports 4 --jellyfish-seed 42 \
     > baseline-jellyfish-graph.jsonl
   ```

### Fasa 2: Live Measurements (requires Mininet + OSKen, no sudo)
1. **Ring-5 live measurement**:
   ```bash
   python3 SPF/benchmark_algorithms.py \
     --mode live \
     --topologies ring5 \
     --algorithms widest_path \
     --max-pairs 3 \
     --iperf-duration 5 \
     > live-ring5-widest_path.jsonl
   ```
   Expected output: 3 host pair measurements, each with throughput_mbps, controller_pid.

2. **Multi-algorithm matrix (shell loop)**:
   ```bash
   for algo in astar bellman_ford widest_path; do
     python3 SPF/benchmark_algorithms.py \
       --mode live \
       --topologies ring5 \
       --algorithms $algo \
       --max-pairs 3 \
       > live-ring5-$algo.jsonl
   done
   ```

### Fasa 3: Scenario Testing (requires sudo for tcpdump)
1. **Baseline scenario (no failure)**:
   ```bash
   sudo python3 SPF/testing-code/run_live_scenarios.py \
     --topologies ring5 \
     --algorithms widest_path \
     --scenarios baseline_no_failure \
     --max-pairs 2 \
     --output scenario-ring5-baseline.jsonl \
     --pcap-dir SPF/csv/pcap/ring5
   ```

2. **Link-down scenario**:
   ```bash
   sudo python3 SPF/testing-code/run_live_scenarios.py \
     --topologies ring5 \
     --algorithms widest_path \
     --scenarios link_down_before_traffic link_flap \
     --max-pairs 2 \
     --output scenario-ring5-failures.jsonl \
     --pcap-dir SPF/csv/pcap/ring5
   ```

### Fasa 4: Analysis (after phases 1-3 produce JSONL)
1. **Agregate CSV dan compute statistics**:
   ```bash
   python3 SPF/benchmark_jsonl_to_csv.py \
     --input baseline-ring5-graph.jsonl \
     --output-dir SPF/benchmark-csv \
     --split-by algorithm
   ```

2. **Parse PCAP (jika ada)**:
   ```bash
   python3 SPF/testing-code/pcap_to_csv.py \
     --pcap-dir SPF/csv/pcap/ring5 \
     --output-dir SPF/csv/pcap-csv/ring5
   ```

3. **Manual analysis** (atau dengan notebook):
   - Baca CSV, compute per-algorithm mean/stddev hop_count, throughput_estimate, runtime_ms.
   - Generate tabel komparasi untuk laporan.

---

## Quick Start Untuk Eksperimen Minimal

Untuk hasil quick-test tanpa perlu Mininet full setup:

```bash
# 1. Graph-mode untuk kedua topologi (15 detik total)
python3 SPF/benchmark_algorithms.py --mode graph --topologies ring5 jellyfish > all-graph.jsonl

# 2. Konversi ke CSV
python3 SPF/benchmark_jsonl_to_csv.py --input all-graph.jsonl --output-dir out-csv --split-by topology,algorithm

# 3. Lihat hasil
ls -la out-csv/
cat out-csv/topology-ring5_algorithm-astar.csv | head -20
```

Output: 6 CSV files (2 topologi × 3 algoritma), ready untuk manual analysis atau plotting.

---
