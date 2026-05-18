# SPF Lab — Shortest-Path Forwarding with SDN

This lab implements multiple routing algorithm controllers using
[OSKen](https://github.com/openstack/os-ken) (an OpenFlow controller framework)
and [Mininet](https://mininet.org/) as the virtual network emulator.

Each controller demonstrates a different path-computation algorithm running as a
centralised SDN application.  All controllers share the same network infrastructure
code (`base_controller.py`) and differ only in their routing algorithm.

---

## Contents

```
SPF/
├── algorithms/                          Pure-Python algorithm implementations
│   ├── __init__.py
│   ├── bfs.py                           Breadth-First Search  O(V+E)
│   ├── dijkstra.py                      Dijkstra + multi-parent variant
│   ├── astar.py                         A* with reverse-BFS heuristic
│   ├── bellman_ford.py                  Bellman-Ford with negative-cycle detection
│   ├── floyd_warshall.py                Floyd-Warshall all-pairs O(V^3)
│   ├── widest_path.py                   Maximum-bottleneck bandwidth path
│   ├── yen_k_shortest.py                Yen's K-shortest simple paths
│   └── suurballe.py                     Suurballe edge-disjoint paths
│
├── base_controller.py                   Shared SDN infrastructure (all controllers inherit)
│
├── bfs_osken_controller.py              BFS controller
├── dijkstra_osken_controller.py         Dijkstra controller
├── dijkstra_multipath_osken_controller.py  Dijkstra + ECMP multipath
├── astar_osken_controller.py            A* controller
├── astar_multipath_osken_controller.py  A* + ECMP multipath
├── bellman_ford_osken_controller.py     Bellman-Ford controller
├── floyd_warshall_osken_controller.py   Floyd-Warshall controller
├── widest_path_osken_controller.py      Widest-path (QoS) controller
├── kshortest_osken_controller.py        Yen's K-shortest paths + ECMP
├── suurballe_fast_failover_osken_controller.py  Suurballe + FAST_FAILOVER
├── suurballe_balanced_failover_osken_controller.py  Suurballe balanced failover
│
├── topo-spf_lab.py                      3-switch ring topology (basic lab)
├── topo-ecmp_lab.py                     ECMP topology
├── topo-weighted_lab.py                 6-switch topology with variable bandwidths
├── topo-mesh_lab.py                     6-switch mesh for multipath demos
│
├── link_weights.json                    Per-link bandwidth for weighted controllers
│
├── tests/                               pytest test suite
│   ├── conftest.py                      Shared graph fixtures
│   ├── test_bfs.py
│   ├── test_dijkstra.py
│   ├── test_astar.py
│   ├── test_bellman_ford.py
│   ├── test_floyd_warshall.py
│   ├── test_widest_path.py
│   ├── test_yen_k_shortest.py
│   └── test_suurballe.py
│
└── docs/                                Teaching guides
    ├── 00-overview.md                   Start here — lab structure and comparison table
    ├── 01-sdn-concepts.md               SDN architecture background
    ├── 03-bfs.md                        BFS walkthrough
    ├── 04-dijkstra.md                   Dijkstra walkthrough
    ├── 07-floyd-warshall.md             Floyd-Warshall and SDN global-view advantage
    ├── 08-widest-path.md                QoS bandwidth routing
    ├── 09-ecmp.md                       ECMP and OpenFlow SELECT groups
    ├── 10-yen-k-shortest.md             Yen's K-shortest paths
    └── 11-suurballe.md                  Suurballe + FAST_FAILOVER
```

---

## Quick Start

All labs require **two terminals** inside the container.

### Terminal 1 — Start Mininet topology

```bash
# Basic 3-switch ring (works with all controllers):
python3 SPF/topo-spf_lab.py

# 6-switch weighted topology (for widest-path / Bellman-Ford):
python3 SPF/topo-weighted_lab.py

# Mesh topology (for ECMP / multipath controllers):
python3 SPF/topo-mesh_lab.py
```

### Terminal 2 — Start a controller

```bash
# Single-path controllers (any topology):
python3 SPF/bfs_osken_controller.py
python3 SPF/dijkstra_osken_controller.py
python3 SPF/astar_osken_controller.py
python3 SPF/bellman_ford_osken_controller.py
python3 SPF/floyd_warshall_osken_controller.py

# Weighted metric (requires link_weights.json):
python3 SPF/widest_path_osken_controller.py

# Fast failover (edge-disjoint paths):
python3 SPF/suurballe_fast_failover_osken_controller.py

# Balanced failover (load balance + fast failover):
python3 SPF/suurballe_balanced_failover_osken_controller.py

# ECMP / multipath controllers:
python3 SPF/dijkstra_multipath_osken_controller.py
python3 SPF/astar_multipath_osken_controller.py
python3 SPF/kshortest_osken_controller.py
```

### Verify connectivity in Mininet CLI

```
mininet> pingall
mininet> h1 ping h6
mininet> dpctl dump-flows -O OpenFlow13
mininet> dpctl dump-groups -O OpenFlow13    # for ECMP controllers
```

### Verify balanced failover (optional)

```bash
# In Mininet CLI
h4 iperf3 -s -D
h1 iperf3 -c 10.2.0.4 -P 4 -t 8
dpctl dump-groups -O OpenFlow13
dpctl dump-group-stats -O OpenFlow13

# Fail the primary link
link s1 s2 down
h1 iperf3 -c 10.2.0.4 -P 4 -t 8
dpctl dump-group-stats -O OpenFlow13
```

---

## Algorithm Comparison

| Controller                  | Algorithm       | O(…)              | Weights | ECMP |
|-----------------------------|----------------|-------------------|---------|------|
| bfs                         | BFS            | O(V+E)            | No      | No   |
| dijkstra                    | Dijkstra       | O((V+E) log V)    | Yes     | No   |
| dijkstra_multipath          | Dijkstra MP    | O((V+E) log V)    | No      | Yes  |
| astar                       | A*             | O((V+E) log V)    | Yes     | No   |
| astar_multipath             | A* MP          | O((V+E) log V)    | No      | Yes  |
| bellman_ford                | Bellman-Ford   | O(V*E)            | Yes     | No   |
| floyd_warshall              | Floyd-Warshall | O(V^3) pre-compute| Yes     | No   |
| widest_path                 | Widest Path    | O((V+E) log V)    | Yes*    | No   |
| kshortest                   | Yen's K-SP    | O(KV(E+V log V))  | No      | Yes  |
| suurballe_fast_failover      | Suurballe      | O((V+E) log V)    | No      | No   |
| suurballe_balanced_failover  | Suurballe      | O((V+E) log V)    | No      | Yes  |

*widest_path requires `link_weights.json`; falls back to hop-count without it.

---

## Running Tests

```bash
cd SPF
python3 -m pytest tests/ -v
```

All tests cover the pure-Python algorithm implementations.

## Benchmark Pipeline

The benchmark scripts added in this repo emit JSON Lines first, then convert
that output to CSV for plotting or notebook work.

Generate graph-mode benchmark data:

```bash
python3 SPF/benchmark_algorithms.py \
  --topologies ring5 jellyfish \
  --algorithms astar widest_path bellman_ford \
  > benchmark-results.jsonl
```

Run live Mininet throughput measurement for one topology and one algorithm:

```bash
python3 SPF/benchmark_algorithms.py \
  --mode live \
  --topologies ring5 \
  --algorithms widest_path \
  --max-pairs 5 \
  --iperf-duration 5 \
  > benchmark-live.jsonl
```

Convert JSONL to several CSV files:

```bash
python3 SPF/benchmark_jsonl_to_csv.py \
  --input benchmark-results.jsonl \
  --output-dir benchmark-csv \
  --split-by topology,algorithm
```

That produces one CSV per topology/algorithm pair, for example:

- `topology-ring5_algorithm-astar.csv`
- `topology-ring5_algorithm-widest_path.csv`
- `topology-ring5_algorithm-bellman_ford.csv`
- `topology-jellyfish_algorithm-astar.csv`
- `topology-jellyfish_algorithm-widest_path.csv`
- `topology-jellyfish_algorithm-bellman_ford.csv`

Graph mode stores `throughput_estimate_mbps`, a path-quality proxy derived
from link capacity and hop count.  Live mode adds `throughput_mbps` from
`iperf3`, so the same JSONL/CSV pipeline works for both estimated and measured
results.

---

## Logging

All controllers use structured log tags for easy filtering:

| Tag            | Meaning                                      |
|----------------|----------------------------------------------|
| `[HOST-LEARN]` | Host MAC discovered or moved to new switch   |
| `[TOPO-CHANGE]`| Link up/down event                           |
| `[TOPO] refreshed` | Topology snapshot rebuilt               |
| `[PATH-QUERY]` | Path computation requested                   |
| `[SPF-DONE]`   | Algorithm result logged                      |
| `[FLOW-INSTALL]`| Flow rule installed on a switch             |
| `[PKT-FWD]`    | Packet forwarded                             |
| `[PKT-DROP]`   | Packet dropped (no path found)               |
| `[ECMP-GROUP]` | SELECT group installed (multipath)           |

Enable verbose logging with `--verbose` or `--default-log-level 10`.

---

## Simulating Link Failures

In the Mininet CLI:

```
mininet> link s1 s3 down    # disable link between s1 and s3
mininet> h1 ping h6          # observe rerouting
mininet> link s1 s3 up      # restore link
```

The controller detects the topology change via LLDP, flushes affected flows,
and reinstalls routes automatically.

---

## Class Structure (for Developers)

```
SPFBaseController (base_controller.py)
  |- Topology discovery (LLDP via OSKen)
  |- Host learning (MAC -> switch:port)
  |- Flow installation / deletion
  |- Broadcast tree flooding (BFS-based spanning tree)
  |- Proactive route reinstallation after topology changes
  |- Graceful shutdown

  Abstract:  compute_path(src, dst, first_port, final_port)
  Hook:      _on_topology_changed()   (optional — used by Floyd-Warshall)
  Override:  install_path()           (optional — used by multipath)
```

See `docs/00-overview.md` for full documentation.
