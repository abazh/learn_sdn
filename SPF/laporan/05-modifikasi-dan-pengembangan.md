# 4.2 Modifikasi dan Pengembangan Tambahan

Bagian ini menjelaskan pengembangan tambahan yang relevan untuk Topik 1, sekaligus membedakan mana yang sudah ada di codebase dan mana yang masih berupa rekomendasi pengembangan.

## 4.2.1 Otomasi Konfigurasi Eksperimen Berbasis Parameter Python
Di codebase saat ini, matriks eksperimen sudah distandarisasi lewat parameter Python, bukan lewat file YAML eksternal.

Komponen yang sudah ada:
- `SPF/benchmark_algorithms.py`
- `SPF/benchmark_core.py`

Cara kerjanya:
- `SPF/benchmark_algorithms.py` menyediakan CLI untuk memilih topologi, algoritma, mode benchmark, dan parameter traffic.
- `SPF/benchmark_core.py` menyimpan struktur `BenchmarkConfig` yang dipakai sebagai konfigurasi utama saat benchmark dijalankan.
- Default yang terlihat di codebase memang memakai `ring5`, `jellyfish`, `astar`, `widest_path`, dan `bellman_ford`.

Kesimpulan:
- Standarisasi eksperimen sudah ada.
- Namun, `SPF/experiments/config.yaml` belum ada di repo.
- Jadi, pernyataan yang aman adalah: konfigurasi eksperimen diatur melalui parameter CLI dan `BenchmarkConfig` Python.

## 4.2.2 Modul Pengukur Waktu Konvergensi
Pada codebase yang diperiksa, helper bernama `SPF/testing-code/convergence_time.py` belum ada.

Artinya:
- klaim bahwa file itu sudah ditambahkan belum sesuai dengan codebase,
- jika dibutuhkan untuk laporan, posisinya harus ditulis sebagai usulan pengembangan tambahan.

Fungsi yang diinginkan untuk modul ini:
- mengukur selisih waktu antara terjadinya perubahan topologi dan terpenuhinya kondisi flow yang diharapkan,
- membantu mengukur metrik konvergensi secara lebih eksplisit,
- melengkapi benchmark yang sekarang lebih fokus pada runtime, ping, throughput, dan PCAP.

Rekomendasi implementasi bila ingin dibuat nanti:
- polling tabel flow menggunakan `ovs-ofctl dump-flows`,
- menghitung kapan jumlah flow mencapai target,
- menyimpan hasil konvergensi ke CSV atau JSONL agar selaras dengan pipeline benchmark yang sudah ada.

## 4.2.3 Visualisasi Data Otomatis
File notebook `SPF/analysis/plot_results.ipynb` belum ditemukan di codebase.

Yang sudah ada saat ini:
- hasil benchmark JSONL,
- konversi ke CSV melalui `SPF/benchmark_jsonl_to_csv.py`,
- data scenario dan hasil pcap yang dapat diproses lebih lanjut.

Kesimpulan:
- visualisasi otomatis belum hadir sebagai file notebook terpisah,
- tetapi pipeline data untuk analisis sudah tersedia,
- sehingga notebook visualisasi sebaiknya ditulis sebagai pengembangan lanjutan, bukan klaim implementasi yang sudah ada.

## 4.2.4 Dampak terhadap Reproducibility
Pendekatan yang sudah ada di codebase cukup baik untuk reproduksi karena:
- topologi dipilih melalui CLI,
- algoritma dipilih melalui CLI,
- benchmark menghasilkan JSONL dan CSV yang konsisten,
- scenario live dapat dijalankan ulang dengan parameter yang sama.

Yang masih kurang untuk reproduksibilitas yang lebih formal adalah:
- file konfigurasi eksperimen terpusat,
- helper konvergensi eksplisit,
- notebook analisis terstandarisasi.

## 4.2.5 Kesimpulan Subbab
Subbab 4.2 sebaiknya ditulis dengan pemisahan jelas antara:
1. apa yang sudah ada di codebase,
2. apa yang masih berupa usulan pengembangan,
3. apa yang memang belum ditemukan sebagai file terpisah.

Untuk kondisi repositori saat ini, yang valid adalah menyebut bahwa pengembangan tambahan masih bisa dilakukan pada area konfigurasi eksperimen terpusat, pengukuran konvergensi, dan visualisasi otomatis.