# 4.1 Integrasi dengan Codebase

Dokumen ini menjelaskan bagian codebase yang benar-benar ada dan fungsi masing-masing komponen.

## 4.1.1 Integrasi Controller
### File utama
- `SPF/base_controller.py`
- `SPF/astar_osken_controller.py`
- `SPF/bellman_ford_osken_controller.py`
- `SPF/widest_path_osken_controller.py`

### Fungsi
- `SPF/base_controller.py` menangani logika umum jaringan:
  - menerima `PacketIn`,
  - mengenali host source dan destination,
  - menghitung jalur,
  - memasang `FlowMod`,
  - mengirim `PacketOut`,
  - menangani event perubahan topologi berbasis LLDP/OSKen topology events.
- Controller turunan hanya bertugas menentukan algoritma path-finding yang dipakai.

### Catatan akurasi
Kode menunjukkan bahwa LLDP dipakai untuk discovery topologi oleh OSKen, tetapi topologi Mininet tetap dibangun oleh skrip topologi. Jadi controller bukan pembangun topologi fisik, melainkan pengelola control plane di atas topologi tersebut.

## 4.1.2 Integrasi Algoritma
### File utama
- `SPF/algorithms/astar.py`
- `SPF/algorithms/bellman_ford.py`
- `SPF/algorithms/widest_path.py`

### Fungsi
- `astar.py`: pencarian jalur dengan heuristic reverse-hop.
- `bellman_ford.py`: shortest path dengan dukungan negative cycle detection.
- `widest_path.py`: mencari jalur dengan bottleneck bandwidth terbesar.

### Pola integrasi
Modul algoritma dibuat murni Python supaya bisa dipanggil oleh controller maupun diuji secara unit.

## 4.1.3 Integrasi Topologi
### File utama
- `SPF/topo-ring5_lab.py`
- `SPF/jellyfish_topo.py`

### Fungsi
- `SPF/topo-ring5_lab.py` membangun ring-5 dengan link antar-switch berbobot bandwidth.
- `SPF/jellyfish_topo.py` membangun topologi jellyfish dengan parameter jumlah switch, jumlah port, dan seed.

### Catatan akurasi
Fokus Topik 1 di codebase saat ini paling konsisten dengan `ring5` dan `jellyfish`, bukan mesh sebagai topologi utama.

## 4.1.4 Integrasi Benchmark dan Data
### File utama
- `SPF/benchmark_core.py`
- `SPF/benchmark_algorithms.py`
- `SPF/benchmark_jsonl_to_csv.py`
- `SPF/testing-code/run_live_scenarios.py`
- `SPF/testing-code/pcap_to_csv.py`

### Fungsi
- `benchmark_core.py`: membangun graph, menghitung record benchmark, menjalankan live iperf3, dan mengelola helper umum.
- `benchmark_algorithms.py`: CLI untuk menjalankan benchmark graph-mode atau live-mode.
- `benchmark_jsonl_to_csv.py`: mengubah JSONL menjadi CSV.
- `run_live_scenarios.py`: menjalankan eksperimen live dengan ping, iperf3, failure injection, dan capture PCAP.
- `pcap_to_csv.py`: mengubah PCAP menjadi CSV untuk analisis.

## 4.1.5 Integrasi Testing
### File utama
- `SPF/tests/test_astar.py`
- `SPF/tests/test_bellman_ford.py`
- `SPF/tests/test_widest_path.py`
- `SPF/tests/test_benchmark_core.py`

### Fungsi
- Validasi correctness algoritma murni.
- Validasi helper benchmark.
- Menjaga agar perubahan pada algoritma atau pipeline tidak merusak perilaku yang sudah ada.

## 4.1.6 Kesimpulan Integrasi
Codebase sudah terintegrasi dengan baik untuk eksperimen Topik 1 karena memiliki:
- pemisahan controller, algoritma, topologi, dan benchmark,
- pipeline data yang dapat direproduksi,
- test unit untuk komponen inti.

Yang belum ada secara eksplisit adalah file konfigurasi YAML terpusat seperti `SPF/experiments/config.yaml`.
