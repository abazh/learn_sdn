# Laporan SPF - Subbab 4.1 dan 4.2

Folder ini berisi dokumen siap pakai untuk menjelaskan subbab 4.1 dan 4.2 sesuai codebase repositori `learn_sdn`.

## Isi Folder
### Subbab 4.1
- [01-gambaran-implementasi.md](01-gambaran-implementasi.md)
- [02-integrasi-codebase.md](02-integrasi-codebase.md)
- [03-arsitektur-testing.md](03-arsitektur-testing.md)
- [04-checklist-kesesuaian.md](04-checklist-kesesuaian.md)

### Subbab 4.2
- [05-modifikasi-dan-pengembangan.md](05-modifikasi-dan-pengembangan.md)
- [06-evaluasi-kesesuaian.md](06-evaluasi-kesesuaian.md)
- [07-checklist-4.2.md](07-checklist-4.2.md)

## Tujuan
Dokumen di folder ini disusun untuk menjawab empat hal:
- bagaimana implementasi SPF bekerja di codebase,
- bagaimana controller, topologi, dan algoritma saling terhubung,
- bagaimana pengujian disusun,
- bagian mana yang sudah terbukti ada dan mana yang harus ditulis hati-hati agar tidak melampaui codebase.

## Catatan Penting
- Topologi utama yang sesuai dengan fokus Topik 1 adalah `ring5` dan `jellyfish`.
- Implementasi controller utama berada di `SPF/base_controller.py` dan controller turunan algoritmik.
- Benchmark dan scenario runner sudah ada di codebase, tetapi `SPF/experiments/config.yaml` belum ada.
- Untuk subbab 4.2, beberapa item pada rancangan awal masih belum berupa file terpisah di repo dan harus ditulis sebagai rekomendasi, bukan fakta implementasi.
