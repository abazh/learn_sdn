# 4.1 Checklist Kesesuaian Codebase

Gunakan checklist ini untuk memastikan narasi laporan tetap sesuai dengan kode yang benar-benar ada.

## A. Yang Sudah Sesuai
- [x] OSKen dipakai sebagai framework controller OpenFlow.
- [x] `PacketIn` ditangani di `SPF/base_controller.py`.
- [x] `FlowMod` dipasang dari controller.
- [x] `PacketOut` dipakai untuk meneruskan paket awal.
- [x] Topologi `ring5` tersedia di `SPF/topo-ring5_lab.py`.
- [x] Topologi `jellyfish` tersedia di `SPF/jellyfish_topo.py`.
- [x] Controller A* tersedia.
- [x] Controller Bellman-Ford tersedia.
- [x] Controller Widest-Path tersedia.
- [x] Modul algoritma murni tersedia di `SPF/algorithms/`.
- [x] Benchmark graph-mode tersedia.
- [x] Benchmark live-mode tersedia.
- [x] JSONL ke CSV tersedia.
- [x] PCAP ke CSV tersedia.
- [x] Unit tests untuk algoritma inti tersedia.

## B. Yang Perlu Ditulis Hati-hati
- [!] LLDP dipakai untuk discovery topologi OSKen, tetapi topologi fisik tetap dibangun oleh skrip Mininet.
- [!] Bandwidth tidak diambil dari LLDP, melainkan dari metadata link/topologi atau fallback default di benchmark core.
- [!] `SPF/experiments/config.yaml` belum ada di codebase.
- [!] Topik 1 di codebase ini paling sesuai dengan `ring5` dan `jellyfish`, bukan mesh sebagai fokus utama saat ini.

## C. Koreksi Istilah dan Nama File
- [x] Gunakan `SPF/widest_path_osken_controller.py`, bukan penulisan terpotong atau salah spasi.
- [x] Gunakan `SPF/jellyfish_topo.py`, bukan `jellyfish _topo.py`.
- [x] Gunakan `benchmark_jsonl_to_csv.py`, bukan `benchmark_ jsonl_to_csv.py`.
- [x] Gunakan `pcap_to_csv.py` pada folder `SPF/testing-code/`.

## D. Kalimat Aman untuk Laporan
Jika ingin menulis pernyataan yang aman terhadap codebase, gunakan formulasi seperti:
- "Implementasi SPF pada repositori ini menggunakan OSKen sebagai controller OpenFlow dan Mininet sebagai emulator topologi."
- "Algoritma routing diimplementasikan sebagai modul Python murni di `SPF/algorithms/` dan dipanggil oleh controller turunan."
- "Eksperimen Topik 1 difokuskan pada topologi `ring5` dan `jellyfish` yang telah tersedia di repositori."
- "Hasil benchmark dapat diekspor melalui pipeline JSONL ke CSV dan PCAP ke CSV untuk analisis lanjutan."

## E. Kesimpulan Checklist
Narasi implementasi dinyatakan sesuai codebase bila seluruh item bagian A terpenuhi dan item bagian B ditulis dengan hati-hati.
