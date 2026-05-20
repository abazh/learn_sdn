# 4.1 Arsitektur Testing

Dokumen ini menjelaskan arsitektur testing yang sesuai dengan codebase.

## 4.1.1 Level Testing yang Ada
### A. Unit Test
Unit test berada di `SPF/tests/` dan fokus pada algoritma murni serta helper terkait.

Contoh file:
- `SPF/tests/test_astar.py`
- `SPF/tests/test_bellman_ford.py`
- `SPF/tests/test_widest_path.py`
- `SPF/tests/test_benchmark_core.py`

### B. Benchmark Graph Mode
Graph mode dijalankan lewat `SPF/benchmark_algorithms.py` dengan backend helper di `SPF/benchmark_core.py`.

Tujuan:
- mengukur runtime algoritma,
- menghitung hop count,
- menghasilkan record JSONL yang mudah dikonversi ke CSV.

### C. Benchmark Live Mode
Live mode dijalankan lewat `SPF/testing-code/run_live_scenarios.py`.

Tujuan:
- menjalankan Mininet,
- mengaktifkan controller OSKen,
- mengirim traffic `ping` dan `iperf3`,
- menangkap PCAP,
- menguji failure scenario.

### D. Konversi Data
- `SPF/benchmark_jsonl_to_csv.py` mengubah hasil benchmark menjadi CSV.
- `SPF/testing-code/pcap_to_csv.py` mengubah hasil capture menjadi CSV.

## 4.1.2 Arsitektur Testing per Lapisan
### Lapisan 1: Validasi algoritma
Memastikan path yang dihitung oleh algoritma benar.

### Lapisan 2: Validasi benchmark core
Memastikan graph building, record generation, dan throughput estimate bekerja.

### Lapisan 3: Validasi scenario live
Memastikan Mininet, controller, ping, iperf3, dan failure injection bisa berjalan.

### Lapisan 4: Validasi hasil
Memastikan JSONL, CSV, dan PCAP dapat diproses untuk analisis.

## 4.1.3 Saran Struktur Testing untuk Topik 1
Untuk eksperimen Topik 1, urutan testing yang paling aman adalah:
1. Jalankan unit test algoritma.
2. Jalankan test benchmark core.
3. Jalankan graph-mode benchmark untuk `ring5` dan `jellyfish`.
4. Jalankan live scenario runner.
5. Konversi hasil ke CSV.
6. Bandingkan metrik final.

## 4.1.4 Batasan Testing Saat Ini
- Belum ada helper khusus untuk mengukur waktu konvergensi secara eksplisit.
- Belum ada test end-to-end tunggal yang mengunci matriks `ring5` + `jellyfish` + 3 algoritma secara penuh.
- `SPF/experiments/config.yaml` belum ada, sehingga konfigurasi eksperimen masih berbentuk CLI argument.

## 4.1.5 Kesimpulan Testing
Arsitektur testing di codebase sudah memadai untuk eksperimen dasar dan benchmark terukur, tetapi untuk kebutuhan penelitian yang lebih formal masih ada ruang untuk menambah helper konvergensi dan konfigurasi eksperimen terpusat.
