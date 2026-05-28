# Checklist Kesiapan Topik 1

Gunakan checklist ini sebelum menjalankan eksperimen final atau sebelum menulis laporan evaluasi akhir.

## A. Topologi
- [x] `ring5` tersedia di codebase
- [x] `jellyfish` tersedia di codebase
- [ ] Parameter eksplisit untuk masing-masing run sudah dibakukan
- [ ] Diagram topologi final sudah tersimpan dan dirujuk dalam laporan

## B. Algoritma dan Controller
- [x] `A*` tersedia
- [x] `Bellman-Ford` tersedia
- [x] `Widest-Path` tersedia
- [ ] Controller final yang dipakai untuk eksperimen sudah dipilih dan dicatat
- [ ] Nama controller per eksperimen sudah dibakukan dalam log

## C. Mode Evaluasi
- [x] Graph-mode tersedia
- [x] Live-mode tersedia
- [x] Scenario-mode tersedia
- [ ] Kriteria kapan memakai graph-mode, live-mode, dan scenario-mode sudah dipakai secara konsisten

## D. Testing
- [x] Unit test A* tersedia
- [x] Unit test Bellman-Ford tersedia
- [x] Unit test Widest-Path tersedia
- [x] Test benchmark core tersedia
- [ ] Test end-to-end khusus ring5 + jellyfish + 3 algoritma dibuat sebagai guardrail
- [ ] Test konvergensi eksplisit dibuat

## E. Benchmark dan Data
- [x] JSONL output untuk graph-mode tersedia
- [x] JSONL output untuk live-mode tersedia
- [x] JSONL output untuk scenario-mode tersedia
- [x] Konversi JSONL ke CSV tersedia
- [x] Konversi PCAP ke CSV tersedia
- [x] Contoh output untuk ring5 dan jellyfish sudah ada
- [ ] Naming convention final untuk dataset hasil eksperimen sudah dibakukan
- [ ] Folder hasil final untuk analisis sudah disepakati

## F. Logging dan Evaluasi
- [ ] Run log template sudah dipakai untuk setiap eksekusi
- [ ] Metadata branch dan commit dicatat di setiap run
- [ ] Parameter iperf3 dicatat di setiap live-mode run
- [ ] Scenario failure event dicatat dengan timestamp yang jelas
- [ ] Tabel metrik final disusun
- [ ] Kesimpulan algoritma terbaik per topologi ditulis

## G. Dokumentasi yang Wajib Dibaca
- [x] `SPF/README.md`
- [x] `SPF/experiment_plan.md`
- [x] `SPF/EXPERIMENT_INDEX.md`
- [x] `SPF/TESTING_MODES.md`
- [x] `SPF/docs/topik1-az-guide/README.md`
- [x] `SPF/docs/topik1-az-guide/arsitektur.md`
- [x] `SPF/docs/topik1-az-guide/alur.md`
- [x] `SPF/docs/topik1-az-guide/testing.md`
- [x] `SPF/docs/topik1-az-guide/peta-file.md`
- [x] `SPF/docs/pipeline-planning/01-live-mode-planning.md`
- [x] `SPF/docs/pipeline-planning/02-scenario-mode-planning.md`

## H. Kriteria Siap Eksekusi
Proyek dianggap siap jika:
1. Semua topologi yang dipilih bisa start dengan parameter yang sama antar run.
2. Semua controller target bisa start dan terhubung ke Mininet.
3. Unit test inti lulus.
4. Graph-mode menghasilkan JSONL dan CSV yang konsisten.
5. Live-mode menghasilkan throughput, RTT, dan metadata controller yang lengkap.
6. Scenario-mode menghasilkan JSONL, CSV, dan PCAP yang bisa dipetakan ulang.
7. Dataset final bisa dibandingkan tanpa rekonstruksi manual.
