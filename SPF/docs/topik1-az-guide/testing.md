# Arsitektur Testing

Dokumen ini menjelaskan bagaimana testing disusun di codebase SPF dan bagaimana testing tersebut dipetakan ke kebutuhan penelitian Topik 1.

## 1. Level Testing yang Sudah Ada

### Unit Test
Unit test fokus pada logika algoritma murni tanpa Mininet.

Ada di:
- `SPF/tests/test_astar.py`
- `SPF/tests/test_bellman_ford.py`
- `SPF/tests/test_widest_path.py`
- `SPF/tests/test_dijkstra.py`
- `SPF/tests/test_bfs.py`
- `SPF/tests/test_floyd_warshall.py`
- `SPF/tests/test_suurballe.py`
- `SPF/tests/test_yen_k_shortest.py`
- `SPF/tests/test_group_ids.py`

### Benchmark Core Test
- `SPF/tests/test_benchmark_core.py`
- Memvalidasi helper benchmark, pembentukan graph, perhitungan path, dan struktur record.

### Live Scenario Runner
- `SPF/testing-code/run_live_scenarios.py`
- Ini bukan unit test, tetapi harness eksperimen live untuk Mininet + controller + failure injection + traffic + PCAP.

### Data Conversion Validation
- `SPF/benchmark_jsonl_to_csv.py`
- `SPF/testing-code/pcap_to_csv.py`

Fungsinya adalah menjaga konsistensi format data eksperimen, bukan melakukan assertion test seperti unit test.

## 2. Pemisahan Kualitas yang Ingin Diukur

### A. Algorithm Correctness
Tujuan: memastikan path yang dihitung memang benar.

Cakupan:
- shortest path benar,
- widest path benar,
- negative cycle terdeteksi,
- group ID konsisten untuk multipath.

### B. Topology Integrity
Tujuan: memastikan topologi yang dipakai benar-benar terbentuk sesuai desain.

Cakupan:
- node dan link terbentuk,
- host attachment benar,
- jalur alternatif tersedia,
- metadata bandwidth ada bila dibutuhkan.

### C. Benchmark Pipeline Integrity
Tujuan: memastikan pipeline data berjalan dari eksekusi ke analisis.

Cakupan:
- JSONL terbentuk,
- CSV bisa dihasilkan,
- field tetap konsisten,
- graph-mode dan live-mode bisa diproses.

### D. Live Experiment Integrity
Tujuan: memastikan eksperimen lapangan bisa dijalankan dan diulang.

Cakupan:
- controller start,
- Mininet start,
- ping dan `iperf3` berjalan,
- pcap tersimpan,
- failure injection berhasil,
- recovery behavior bisa diamati.

## 3. Mode Testing vs Mode Evaluasi

- Graph-mode: pengujian algoritma dan struktur graph.
- Live-mode: pengujian end-to-end tanpa failure injection.
- Scenario-mode: pengujian resiliency dengan failure injection dan packet capture.

Pemisahan ini penting agar hasil evaluasi tidak tercampur antara correctness, performance, dan robustness.

## 4. Arsitektur Testing yang Disarankan untuk Topik 1

Urutan ideal:
1. Jalankan unit test algoritma.
2. Jalankan test benchmark core.
3. Jalankan graph-mode untuk `ring5` dan `jellyfish`.
4. Jalankan live-mode untuk masing-masing algoritma.
5. Jalankan scenario-mode bila ingin mengukur robustness.
6. Konversi JSONL ke CSV.
7. Validasi CSV dan ringkaskan hasil.
8. Dokumentasikan hasil final.

## 5. Gap Testing yang Masih Tersisa
- Belum ada helper eksplisit untuk mengukur waktu konvergensi.
- Belum ada suite end-to-end yang mengunci matriks `ring5` + `jellyfish` + 3 algoritma sekaligus.
- Belum ada notebook atau skrip visualisasi yang menjadi bagian baku dari pipeline testing.

## 6. Kesimpulan Testing
Testing di repo ini sudah kuat untuk:
- memverifikasi algoritma inti,
- memverifikasi benchmarking core,
- menjalankan eksperimen live dan scenario.

Untuk kebutuhan penelitian, yang paling penting ditambah adalah:
- guardrail end-to-end yang lebih formal,
- helper konvergensi,
- dokumentasi hasil otomatis yang konsisten.
