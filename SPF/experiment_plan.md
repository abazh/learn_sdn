# Rencana Eksperimen — Topik 1: Analisis Perbandingan Algoritma Perutean SPF

## Ringkasan Topik
Topik: Analisis perbandingan Algoritma SPF — fokus pada `A*`, `Bellman-Ford`, dan `Widest-Path` pada lingkungan SDN (Mininet + OSKen).

## Arsitektur Eksperimen (komponen)
- Emulator: Mininet — topologi dijalankan dari skrip di `SPF/topo-*.py`.
  - Ring-5 (utama): `SPF/topo-ring5_lab.py`
  - Jellyfish (utama): `SPF/jellyfish_topo.py`
  - Topologi lain tersedia: `SPF/topo-spf_lab.py`, `SPF/topo-mesh_lab.py`, `SPF/topo-weighted_lab.py`
- Controller: OSKen-based controllers yang diwariskan dari `SPF/base_controller.py`.
  - Implementasi algoritme:
    - `A*`: `SPF/astar_osken_controller.py` (dan multipath: `SPF/astar_multipath_osken_controller.py`)
    - `Bellman-Ford`: `SPF/bellman_ford_osken_controller.py`
    - `Widest-Path`: `SPF/widest_path_osken_controller.py`
  - Lainnya tersedia (Dijkstra, Suurballe, k-shortest, dll.)
- Algoritma (pure Python): `SPF/algorithms/` — `astar.py`, `bellman_ford.py`, `widest_path.py`, dll.
- Benchmark & orchestration:
  - Graph-mode benchmarks: `SPF/benchmark_algorithms.py`
  - Live Mininet scenarios: `SPF/testing-code/run_live_scenarios.py`
  - Utilities: `SPF/benchmark_jsonl_to_csv.py`, `SPF/testing-code/pcap_to_csv.py`
- Telemetri & keluaran:
  - JSONL / CSV pipeline: menghasilkan CSV di `SPF/benchmark-csv` dan `SPF/benchmark-live-csv`.
  - PCAP output: `SPF/csv/pcap/...` dihasilkan oleh scenario runner.

## Fokus Eksperimen (dari rancangan Anda)
- Topologi: Jellyfish dan Ring-5 (keduanya sudah tersedia di repo).
- Metrik: Latensi (ping), Throughput (iperf3), Waktu Konvergensi / Jumlah Hop.
- Deliverable: skrip topologi, diagram, tabel perbandingan metrik, analisis dan rekomendasi.

## Checklist: apakah sudah ada di codebase
- [x] Topologi Ring-5 (`SPF/topo-ring5_lab.py`) — ADA
- [x] Topologi Jellyfish (`SPF/jellyfish_topo.py`) — ADA
- [x] Implementasi `A*` — ADA (`SPF/astar_osken_controller.py`, `SPF/algorithms/astar.py`)
- [x] Implementasi `Bellman-Ford` — ADA (`SPF/bellman_ford_osken_controller.py`, `SPF/algorithms/bellman_ford.py`)
- [x] Implementasi `Widest-Path` — ADA (`SPF/widest_path_osken_controller.py`, `SPF/algorithms/widest_path.py`)
- [x] Pytests untuk algoritma murni — ADA (`SPF/tests/test_astar.py`, `SPF/tests/test_bellman_ford.py`, `SPF/tests/test_widest_path.py`)
- [x] Unit test untuk benchmark core — ADA (`SPF/tests/test_benchmark_core.py`)
- [x] Benchmark graph-mode (JSONL) — ADA (`SPF/benchmark_algorithms.py`)
- [x] Scenario runner (live Mininet + pcap) — ADA (`SPF/testing-code/run_live_scenarios.py`)
- [x] JSONL->CSV converter — ADA (`SPF/benchmark_jsonl_to_csv.py`)
- [x] PCAP->CSV helper — ADA (`SPF/testing-code/pcap_to_csv.py`)
- [x] Contoh output data untuk Ring-5 dan Jellyfish — ADA (`SPF/benchmark-csv/topology-ring5_algorithm-*.csv`, `SPF/benchmark-csv/topology-jellyfish_algorithm-*.csv`)

## Checklist test & validasi untuk Topik 1
- [x] Correctness algoritma A* (unit tests) — tersedia di `SPF/tests/test_astar.py`
- [x] Correctness algoritma Bellman-Ford (unit tests) — tersedia di `SPF/tests/test_bellman_ford.py`
- [x] Correctness algoritma Widest-Path (unit tests) — tersedia di `SPF/tests/test_widest_path.py`
- [x] Validasi utilitas benchmark core — tersedia di `SPF/tests/test_benchmark_core.py`
- [ ] Uji integrasi live Mininet khusus matriks `ring5` + `jellyfish` untuk 3 algoritma (perlu dijalankan saat eksperimen final)
- [ ] Uji konvergensi eksplisit berbasis timestamp/log parsing (belum ada helper khusus)

## Kekurangan / gap fungsional yang direkomendasikan (catatan)
1. Pengukuran eksplisit untuk "Waktu Konvergensi":
   - Repo menyediakan scenario runner yang mengumpulkan ping/pcap/throughput, tetapi tidak tampak ada helper tunggal yang mengukur waktu konvergensi controller (waktu hingga semua flow terpasang atau hingga rute stabil). Rekomendasi: tambahkan modul kecil `SPF/testing-code/convergence_time.py` yang:
     - menjalankan testcase (ambil timestamp sebelum dan setelah peristiwa recovery/flow install), atau
     - parsing dpctl/flow dumps atau controller log untuk mendeteksi ketika semua flow yang diharapkan ada.
2. Standarisasi eksperimen & konfigurasi:
   - Tambahkan file konfigurasi eksperimen (mis. `SPF/experiments/config.yaml`) untuk menentukan kombinasi (topology, algorithm, traffic profile, run-count) agar eksperimen bisa direproduksi.
3. Otomasi traffic load (iperf3 orchestration):
   - `run_live_scenarios.py` sudah melakukan live measurements, tetapi pastikan ada parameter untuk `--max-pairs`, `--iperf-duration`, dan output naming yang konsisten (README menyebutkannya—periksa dan gunakan).
4. Visualisasi / agregasi hasil:
   - Ada converter ke CSV; mungkin perlu notebook atau skrip `SPF/analysis/plot_results.ipynb` untuk langsung menghasilkan tabel & figure dari CSV.

## Perubahan alur di codebase yang dicatat (apa yang ada/ditambahkan)
- Ada pipeline lengkap: generate JSONL (graph or live) → convert CSV → per-topology CSV. (Ada file contoh CSV di `SPF/benchmark-csv` dan `SPF/benchmark-live-csv`.)
- Ada runner untuk skenario live yang sudah meng-capture PCAP per-host.
- Alur benchmark memakai komponen reusable di `SPF/benchmark_core.py` (sudah ada test `SPF/tests/test_benchmark_core.py`).
- README sudah mendokumentasikan command skenario untuk `--topologies ring5 jellyfish` pada `SPF/testing-code/run_live_scenarios.py`.
- Tambahan yang saya sarankan (lihat "Kekurangan") akan menambah file baru di `SPF/testing-code/` dan `SPF/experiments/`.

## Rekomendasi langkah implementasi (prioritas)
1. Tambah `SPF/experiments/config.yaml` + small CLI wrapper `SPF/testing-code/run_experiment.py` untuk menjalankan matrix (topology × algorithm × repeat).
2. Tambah `SPF/testing-code/convergence_time.py` untuk mengukur konvergensi (opsional: integrasi dengan controller logging).
3. Buat `SPF/analysis/plot_results.ipynb` untuk agregasi dan visualisasi hasil otomatis.
4. Pastikan dokumentasi singkat di `SPF/README.md` atau `SPF/docs/` yang menjelaskan langkah reproducible experiment.

## Next steps yang bisa saya kerjakan sekarang
- Buatkan file `SPF/experiments/config.yaml` contoh dan `SPF/testing-code/convergence_time.py` skeleton.
- Atau: jalankan satu eksperimen percobaan (graph-mode) untuk menghasilkan sample CSV.

---
*File ini dibuat otomatis oleh asisten. Sesuaikan parameter dan dokumentasi sesuai kebutuhan penelitian.*
