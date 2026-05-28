# Arsitektur Eksperimen

Dokumen ini menjelaskan arsitektur eksperimen Topik 1 dari input penelitian sampai output analisis, dengan pemisahan yang jelas antara graph-mode, live-mode, dan scenario-mode.

## 1. Lapisan Tujuan Penelitian
Topik 1 bertujuan membandingkan tiga algoritma perutean SPF pada dua topologi yang sudah tersedia di repo.

- Algoritma: `A*`, `Bellman-Ford`, `Widest-Path`
- Topologi: `ring5`, `jellyfish`
- Mode evaluasi: graph-mode, live-mode, scenario-mode
- Metrik: hop count, path cost, runtime, throughput, packet loss, recovery time

## 2. Lapisan Topologi
Topologi dijalankan dari skrip Mininet yang sudah ada dan dipakai sesuai kebutuhan eksperimen.

### Ring-5
- File: `SPF/topo-ring5_lab.py`
- Fungsi: baseline ring topology dengan 5 switch dan host attachment yang sederhana.
- Kegunaan: validasi jalur dasar, perbandingan path yang mudah dibaca, dan skenario gangguan yang ringan.

### Jellyfish
- File: `SPF/jellyfish_topo.py`
- Fungsi: topologi acak terstruktur yang bisa dikontrol lewat parameter CLI.
- Parameter penting: `--jellyfish-switches`, `--jellyfish-ports`, `--jellyfish-sw-ports`, `--jellyfish-seed`.
- Kegunaan: evaluasi routing yang lebih variatif, terutama saat ingin melihat karakter multipath dan resiliency.

## 3. Lapisan Controller
Controller berbasis OSKen menjadi jembatan antara event jaringan dan algoritma path-finding.

### Base controller
- File: `SPF/base_controller.py`
- Fungsi: packet-in handling, host learning, flow installation, dan plumbing OpenFlow umum.

### Controller algoritmik
- `SPF/astar_osken_controller.py`
- `SPF/bellman_ford_osken_controller.py`
- `SPF/widest_path_osken_controller.py`

Setiap controller melakukan hal yang sama secara konseptual:
- menerima event jaringan,
- memanggil algoritma yang sesuai,
- membangun path switch,
- memasang flow,
- mencatat hasil eksekusi.

## 4. Lapisan Algoritma
Algoritma inti berada di `SPF/algorithms/` dan tetap murni Python.

- `astar.py`: A* dengan heuristic reverse-hop.
- `bellman_ford.py`: shortest path dengan dukungan deteksi negative cycle.
- `widest_path.py`: path dengan bottleneck bandwidth terbesar.

Karena murni Python, lapisan ini bisa diuji tanpa Mininet dan cocok untuk graph-mode.

## 5. Lapisan Eksekusi Benchmark
Ada tiga jalur eksekusi yang harus dipahami secara terpisah.

### Graph-mode
- File: `SPF/benchmark_algorithms.py`
- Core: `SPF/benchmark_core.py`
- Karakter: pure algorithm execution tanpa Mininet dan tanpa controller.
- Output: JSONL berisi runtime, hop count, path cost, dan throughput estimate.

### Live-mode
- File: `SPF/benchmark_algorithms.py`
- Core: `SPF/benchmark_core.py`
- Karakter: Mininet + controller + iperf3.
- Output: JSONL dengan throughput aktual, controller metadata, dan iperf summary.

### Scenario-mode
- File: `SPF/testing-code/run_live_scenarios.py`
- Karakter: live-mode + failure injection + tcpdump capture.
- Output: JSONL + PCAP per host + CSV hasil parsing.

## 6. Lapisan Konversi Data
Output eksperimen tidak dianalisis langsung dari stdout, tetapi dikonversi lebih dulu.

- `SPF/benchmark_jsonl_to_csv.py`: JSONL → CSV.
- `SPF/testing-code/pcap_to_csv.py`: PCAP → CSV.

## 7. Lapisan Analisis
Data yang sudah terkumpul dipakai untuk:

- membandingkan runtime algoritma,
- membandingkan hop count dan path cost,
- membandingkan throughput aktual,
- membandingkan packet loss dan recovery,
- menyusun tabel final dan narasi evaluasi.

## 8. Lapisan Dokumen Pendukung
Dokumen planning dan index yang sekarang menjadi referensi utama:

- [Experiment Plan](../../experiment_plan.md)
- [Experiment Index](../../EXPERIMENT_INDEX.md)
- [Testing Modes](../../TESTING_MODES.md)
- [Live-Mode Planning](../pipeline-planning/01-live-mode-planning.md)
- [Scenario-Mode Planning](../pipeline-planning/02-scenario-mode-planning.md)

## 9. Ringkasan Alur
1. Pilih topologi.
2. Pilih algoritma.
3. Tentukan mode evaluasi.
4. Jalankan benchmark.
5. Simpan JSONL, CSV, dan PCAP bila relevan.
6. Bandingkan metrik.
7. Tarik kesimpulan berdasarkan mode yang tepat.
