# Alur Kerja End-to-End

Dokumen ini menjelaskan urutan kerja eksperimen dari persiapan sampai analisis akhir, dengan pemisahan yang jelas antara graph-mode, live-mode, dan scenario-mode.

## Alur 1: Persiapan Penelitian
1. Tetapkan fokus eksperimen: `ring5` dan `jellyfish`.
2. Tetapkan algoritma: `A*`, `Bellman-Ford`, dan `Widest-Path`.
3. Tetapkan mode evaluasi yang akan dipakai:
   - graph-mode untuk validasi algoritma,
   - live-mode untuk pengukuran end-to-end,
   - scenario-mode untuk failure and recovery analysis.
4. Tetapkan metrik yang akan dilog:
   - hop count,
   - path cost,
   - runtime,
   - throughput,
   - packet loss,
   - recovery time.
5. Tentukan jumlah repetition, seed, dan batasan host pair.

## Alur 2: Validasi Artefak yang Sudah Ada
1. Pastikan skrip topologi tersedia.
2. Pastikan controller algoritmik tersedia.
3. Pastikan unit test inti tersedia.
4. Pastikan pipeline benchmark dan converter data tersedia.
5. Pastikan dokumen referensi tersedia:
   - [Experiment Plan](../../experiment_plan.md)
   - [Experiment Index](../../EXPERIMENT_INDEX.md)
   - [Testing Modes](../../TESTING_MODES.md)

## Alur 3: Graph-Mode
1. Jalankan benchmark graph-mode untuk kedua topologi.
2. Simpan hasil ke JSONL.
3. Konversi JSONL ke CSV.
4. Bandingkan hasil berdasarkan hop count, path cost, dan runtime.

Contoh:
```bash
python3 SPF/benchmark_algorithms.py --mode graph --topologies ring5 jellyfish --algorithms astar bellman_ford widest_path > benchmark-results.jsonl
python3 SPF/benchmark_jsonl_to_csv.py --input benchmark-results.jsonl --output-dir SPF/benchmark-csv --split-by topology,algorithm
```

## Alur 4: Live-Mode
1. Jalankan satu topologi dan satu algoritma per run.
2. Start Mininet dan controller OSKen.
3. Jalankan traffic `iperf3` antar host pair.
4. Log throughput aktual dan summary iperf3.
5. Simpan JSONL untuk tiap run.
6. Konversi ke CSV untuk analisis lanjut.

Contoh:
```bash
python3 SPF/benchmark_algorithms.py --mode live --topologies ring5 --algorithms widest_path --max-pairs 5 --iperf-duration 5 --output SPF/csv/live-ring5-widest_path.jsonl
python3 SPF/benchmark_jsonl_to_csv.py --input SPF/csv/live-ring5-widest_path.jsonl --output-dir SPF/csv/live-ring5 --split-by topology,algorithm
```

## Alur 5: Scenario-Mode
1. Jalankan scenario runner dengan topology, algorithm, dan scenario yang dipilih.
2. Inject failure sesuai scenario.
3. Start tcpdump pada host yang relevan.
4. Jalankan traffic dan capture paket.
5. Simpan JSONL, PCAP, dan CSV hasil parsing.
6. Analisis packet loss dan recovery.

Contoh:
```bash
sudo python3 SPF/testing-code/run_live_scenarios.py --topologies ring5 jellyfish --algorithms astar bellman_ford widest_path --scenarios baseline_no_failure link_down_before_traffic link_flap bandwidth_throttle --output SPF/csv/live-scenarios.jsonl --pcap-dir SPF/csv/pcap
python3 SPF/benchmark_jsonl_to_csv.py --input SPF/csv/live-scenarios.jsonl --output-dir SPF/csv/scenario-csv --split-by topology,algorithm,scenario_name
python3 SPF/testing-code/pcap_to_csv.py --pcap-dir SPF/csv/pcap --output-dir SPF/csv/pcap-csv
```

## Alur 6: Analisis Data
1. Bandingkan hasil graph-mode antar algoritma.
2. Bandingkan hasil live-mode antar algoritma dan topologi.
3. Bandingkan hasil scenario-mode untuk failure resilience.
4. Hitung ringkasan statistik per topology dan algorithm.
5. Dokumentasikan insight utama untuk laporan.

## Alur 7: Output Akhir
1. Tabel perbandingan metrik.
2. Narasi hasil per topology.
3. Kesimpulan algoritma terbaik untuk tiap mode evaluasi.
4. Catatan tentang trade-off antara quality, throughput, dan robustness.

## Alur 8: Perluasan Jika Dibutuhkan
Jika ingin menaikkan maturitas pipeline, tambahkan:
- konfigurasi eksperimen terpusat,
- helper konvergensi eksplisit,
- notebook visualisasi,
- run log terstandar per eksekusi.
