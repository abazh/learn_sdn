# 4.1 Gambaran Implementasi

Bagian ini menjelaskan implementasi pada codebase secara ringkas, akurat, dan sesuai dengan struktur repositori.

## 4.1.1 Framework dan Fondasi
Implementasi SPF pada repositori ini menggunakan OSKen sebagai framework controller OpenFlow. OSKen berperan sebagai lapisan control plane yang menerima event dari switch dan mengirim keputusan routing kembali ke data plane.

Fondasi proyek berasal dari repositori `learn_sdn`, dengan pemisahan yang jelas antara:
- data plane: topologi Mininet,
- control plane: controller OSKen,
- algoritma routing: modul Python murni di `SPF/algorithms/`.

## 4.1.2 Alur Dasar Controller
Alur kerja controller di codebase adalah sebagai berikut:
1. Switch mengirim `PacketIn` ketika belum ada flow yang cocok.
2. `SPF/base_controller.py` menerima event tersebut.
3. Controller memeriksa MAC source, MAC destination, dan lokasi host.
4. Jika jalur belum tersedia, controller menghitung path menggunakan algoritma yang dipilih.
5. Controller memasang flow entry ke switch dengan `OFPFlowMod`.
6. Paket awal diteruskan kembali menggunakan `OFPPacketOut`.

Alur ini terlihat langsung di `SPF/base_controller.py`, terutama pada handler `EventOFPPacketIn`.

## 4.1.3 Implementasi Algoritma Routing
Tiga algoritma utama yang dipakai pada Topik 1 sudah tersedia sebagai berikut:
- A* pada `SPF/astar_osken_controller.py` dan `SPF/algorithms/astar.py`
- Bellman-Ford pada `SPF/bellman_ford_osken_controller.py` dan `SPF/algorithms/bellman_ford.py`
- Widest-Path pada `SPF/widest_path_osken_controller.py` dan `SPF/algorithms/widest_path.py`

Modul algoritma berada di `SPF/algorithms/` agar dapat diuji secara terpisah dari Mininet dan OpenFlow.

## 4.1.4 Topologi yang Dipakai
Untuk fokus Topik 1, topologi yang paling relevan adalah:
- `SPF/topo-ring5_lab.py` untuk skenario ring-5,
- `SPF/jellyfish_topo.py` untuk skenario jellyfish.

Keduanya adalah skrip Mininet yang membangun jaringan data plane secara eksplisit. Controller tidak membuat topologi fisik dari nol, melainkan bekerja di atas topologi yang sudah didefinisikan oleh skrip tersebut.

## 4.1.5 Data Bandwidth dan Bobot Jalur
Informasi bandwidth untuk routing tidak berasal dari LLDP. Dalam codebase ini:
- `ring5` menanam bandwidth langsung pada link Mininet, misalnya `bw=100` pada link antar-switch di `SPF/topo-ring5_lab.py`,
- jalur pada `jellyfish` dan benchmark graph-mode diproses melalui graph helper di `SPF/benchmark_core.py`, dengan fallback `default_bandwidth_mbps` bila metadata bandwidth tidak tersedia.

Karena itu, penjelasan yang tepat adalah: bobot jalur disediakan oleh metadata link/topologi dan dipakai oleh algoritma sebagai input graf.

## 4.1.6 Integrasi Pengujian dan Benchmark
Untuk menguji perilaku sistem, codebase menyediakan:
- `SPF/benchmark_algorithms.py` untuk benchmark graph-mode dan live-mode,
- `SPF/testing-code/run_live_scenarios.py` untuk skenario Mininet live dengan failure injection,
- `SPF/benchmark_jsonl_to_csv.py` untuk konversi JSONL ke CSV,
- `SPF/testing-code/pcap_to_csv.py` untuk konversi PCAP ke CSV.

Jadi, implementasi tidak berhenti pada controller, tetapi juga mencakup pipeline pengumpulan data hasil eksperimen.

## 4.1.7 Kesimpulan Implementasi
Secara arsitektural, implementasi pada repositori ini sudah sesuai untuk eksperimen perbandingan routing SPF karena:
- controller dan algoritma dipisah dengan baik,
- topologi dapat dijalankan secara independen,
- hasil eksperimen bisa diekspor ke JSONL dan CSV,
- unit test tersedia untuk algoritma murni.
