# Topik 1 A-Z Guide

Panduan ini menjelaskan pipeline eksperimen Topik 1 secara end-to-end untuk fokus perbandingan `A*`, `Bellman-Ford`, dan `Widest-Path` pada topologi `ring5` dan `jellyfish`.

## Tujuan
- Menjadi navigasi utama untuk memahami seluruh rangkaian eksperimen.
- Menyatukan dokumentasi arsitektur, alur, testing, dan checklist kesiapan.
- Menjelaskan mana artefak yang sudah ada di repo dan mana yang masih berupa rekomendasi pengembangan.
- Menjadi jembatan antara README utama SPF dan planning docs untuk live-mode serta scenario-mode.

## Fokus Topik
- Topologi utama: `ring5` dan `jellyfish`.
- Algoritma utama: `A*`, `Bellman-Ford`, `Widest-Path`.
- Mode evaluasi: graph-mode, live-mode, dan scenario-mode.
- Metrik utama: hop count, path cost, runtime, throughput, packet loss, dan recovery behavior.

## Dokumen Terkait
0. [INDEX](INDEX.md) — pintu masuk lokal yang ringkas.
1. [Arsitektur Eksperimen](arsitektur.md)
2. [Alur Kerja End-to-End](alur.md)
3. [Peta File dan Fungsi](peta-file.md)
4. [Arsitektur Testing](testing.md)
5. [Checklist Kesiapan](checklist.md)
6. [Experiment Plan](../../experiment_plan.md)
7. [Experiment Index](../../EXPERIMENT_INDEX.md)
8. [Testing Modes](../../TESTING_MODES.md)
9. [Live-Mode Planning](../pipeline-planning/01-live-mode-planning.md)
10. [Scenario-Mode Planning](../pipeline-planning/02-scenario-mode-planning.md)

## Cara Membaca
- Baca [arsitektur.md](arsitektur.md) untuk memahami komponen sistem dan mode benchmark.
- Lanjutkan ke [alur.md](alur.md) untuk melihat urutan kerja eksperimen.
- Gunakan [peta-file.md](peta-file.md) saat ingin mencari lokasi file tertentu.
- Buka [testing.md](testing.md) untuk memahami capaian test dan gap yang masih ada.
- Gunakan [checklist.md](checklist.md) sebelum menjalankan eksperimen final.
- Gunakan [INDEX.md](INDEX.md) jika ingin navigasi cepat tanpa membaca penjelasan panjang.

## Prinsip Operasional
- Graph-mode dipakai untuk validasi algoritma dan pengukuran cepat berbasis graph abstrak.
- Live-mode dipakai untuk pengukuran end-to-end pada Mininet + OSKen + iperf3.
- Scenario-mode dipakai untuk failure injection, packet capture, dan recovery analysis.
- Semua hasil sebaiknya disimpan sebagai JSONL terlebih dahulu, lalu dikonversi ke CSV.
- Logging run harus menyimpan metadata yang cukup untuk audit ulang.

## Status Codebase
- `ring5` tersedia dan digunakan sebagai baseline topology.
- `jellyfish` tersedia dan dikonfigurasi via parameter CLI.
- Controller untuk `A*`, `Bellman-Ford`, dan `Widest-Path` tersedia.
- `benchmark_algorithms.py` mendukung graph-mode dan live-mode.
- `run_live_scenarios.py` mendukung scenario-mode dengan failure injection dan PCAP capture.
- `benchmark_jsonl_to_csv.py` dan `pcap_to_csv.py` tersedia untuk pipeline analisis.
- Unit test untuk algoritma inti dan benchmark core tersedia.

## Output yang Diharapkan
- JSONL hasil graph-mode untuk perbandingan kualitas algoritma.
- JSONL hasil live-mode untuk throughput dan RTT.
- JSONL + PCAP + CSV hasil scenario-mode untuk recovery dan robustness analysis.
- Tabel komparasi yang konsisten antar topology dan algoritma.

## Catatan Penting
Dokumen ini sengaja dipisahkan dari [SPF/README.md](../../README.md) agar bisa dipakai sebagai panduan kerja penelitian yang lebih detail, terstruktur, dan langsung mengarah ke evaluasi.
