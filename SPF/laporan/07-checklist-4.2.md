# 4.2 Checklist Kesesuaian

Gunakan checklist ini untuk memastikan narasi subbab 4.2 tidak melebih-lebihkan isi codebase.

## A. Yang Terbukti Ada
- [x] CLI benchmark berbasis parameter Python tersedia.
- [x] `BenchmarkConfig` tersedia di `SPF/benchmark_core.py`.
- [x] Topologi `ring5` tersedia.
- [x] Topologi `jellyfish` tersedia.
- [x] Controller A*, Bellman-Ford, dan Widest-Path tersedia.
- [x] Benchmark graph-mode tersedia.
- [x] Benchmark live-mode tersedia.
- [x] JSONL ke CSV tersedia.
- [x] PCAP ke CSV tersedia.

## B. Yang Belum Ditemukan Sebagai File Terpisah
- [ ] `SPF/experiments/config.yaml`
- [ ] `SPF/testing-code/convergence_time.py`
- [ ] `SPF/analysis/plot_results.ipynb`

## C. Kalimat Aman untuk Laporan
Pernyataan berikut aman dipakai karena sesuai codebase:
- "Konfigurasi eksperimen distandarisasi melalui parameter CLI dan struktur `BenchmarkConfig`."
- "Eksperimen Topik 1 saat ini difokuskan pada topologi `ring5` dan `jellyfish`."
- "Pipeline hasil eksperimen tersedia dalam bentuk JSONL, CSV, dan PCAP untuk keperluan analisis lanjutan."

## D. Kalimat yang Harus Diubah Jika Dipakai
Kalimat berikut jangan dipakai sebagai fakta implementasi:
- "File `SPF/experiments/config.yaml` sudah dibuat."
- "Modul `SPF/testing-code/convergence_time.py` sudah diimplementasikan."
- "Notebook `SPF/analysis/plot_results.ipynb` sudah tersedia di codebase."

## E. Kesimpulan Checklist
Subbab 4.2 dinyatakan sesuai codebase bila narasi membedakan secara jelas antara implementasi yang sudah ada dan usulan pengembangan tambahan.