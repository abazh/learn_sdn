# Scenario-Mode Planning — SPF Pipeline Standardization

**Purpose**: Rencana implementasi dan standardisasi untuk Scenario-Mode agar pengujian failure, recovery, logging, dan evaluasi menjadi lebih robust, profesional, dan otomatis.

**Scope**: `SPF/testing-code/run_live_scenarios.py` dan seluruh alur yang terkait dengan tcpdump, failure injection, parsing PCAP, dan konversi hasil.

**Status**: Planning document

---

## 1. Goal Statement

Scenario-Mode harus menjadi mode evaluasi ketahanan yang terdokumentasi rapi, sehingga failure injection, recovery measurement, packet capture, dan pasca-analisis dapat dijalankan ulang dengan cara yang konsisten. Mode ini harus menjawab seberapa cepat, seberapa stabil, dan seberapa mudah dipulihkan jaringan ketika ada gangguan.

### Target Outcome
- Scenario matrix yang eksplisit dan bisa diulang.
- Logging event yang terstruktur untuk failure, recovery, dan traffic window.
- PCAP capture per host yang terorganisir.
- Evaluasi packet loss, recovery time, throughput under failure, dan packet-level evidence yang bisa diaudit.
- Metadata cukup lengkap untuk reproduksi dan audit ulang.

---

## 2. Current State in Codebase

### Existing Components
- Scenario runner: [SPF/testing-code/run_live_scenarios.py](../../testing-code/run_live_scenarios.py)
- PCAP parser: [SPF/testing-code/pcap_to_csv.py](../../testing-code/pcap_to_csv.py)
- Shared benchmark helpers: [SPF/benchmark_core.py](../../benchmark_core.py)
- Live benchmark CLI: [SPF/benchmark_algorithms.py](../../benchmark_algorithms.py)
- Sample scenario output target: [SPF/csv/live-scenarios.jsonl](../../csv/live-scenarios.jsonl)

### Practical Constraints
- Scenario-Mode membutuhkan Mininet, OSKen, dan hak akses yang cukup untuk tcpdump.
- Output akan lebih besar daripada live-mode biasa karena ada PCAP per host.
- Timing failure injection sensitif terhadap environment, sehingga metadata harus lebih lengkap.
- Beberapa scenario butuh parameter timing eksplisit seperti link down delay dan link up delay.

---

## 3. Standard Operating Model

### Recommended Execution Pattern
1. Define scenario set yang akan dijalankan.
2. Lock topology, algorithm, repetition, dan seed.
3. Jalankan scenario runner.
4. Simpan JSONL utama dan folder PCAP terstruktur.
5. Parse PCAP ke CSV untuk analisis.
6. Simpan ringkasan evaluasi, observasi, dan potensi anomali.

### Preflight Checks
Sebelum menjalankan scenario mode, verifikasi:
- Mininet dan OSKen tersedia.
- `tcpdump` dapat dijalankan di environment target.
- Output directory dan pcap directory bisa ditulis.
- Topology dan controller yang dipakai sudah final.
- Seed untuk scenario selection sudah dibakukan.
- Tidak ada proses Mininet atau controller lama yang masih hidup.

### Recommended Commands
```bash
sudo python3 SPF/testing-code/run_live_scenarios.py \
  --topologies ring5 jellyfish \
  --algorithms astar bellman_ford widest_path \
  --scenarios baseline_no_failure link_down_before_traffic link_flap bandwidth_throttle \
  --repetitions 1 \
  --scenario-seed 1 \
  --output SPF/csv/live-scenarios.jsonl \
  --pcap-dir SPF/csv/pcap

python3 SPF/testing-code/pcap_to_csv.py \
  --pcap-dir SPF/csv/pcap \
  --output-dir SPF/csv/pcap-csv
```

### Recommended Run Shape
- Gunakan satu batch scenario dengan topology, algorithm, dan scenario yang jelas.
- Gunakan seed yang sama saat ingin membandingkan run.
- Gunakan `--repetitions` untuk mengukur variansi hasil.
- Gunakan `--tcpdump` aktif saat butuh bukti packet-level.
- Gunakan `--pcap-snaplen` cukup kecil untuk menjaga ukuran file, tetapi jangan terlalu kecil jika packet analysis penting.

---

## 4. Automation Targets

### Phase A: Scenario Registry
Sediakan daftar scenario resmi yang dipakai oleh tim, termasuk:
- baseline_no_failure
- link_down_before_traffic
- link_down_during_traffic
- link_flap
- switch_down
- bandwidth_throttle
- random_link_down_jellyfish

### Phase B: Standard Failure Timing
Setiap scenario harus memiliki definisi:
- action
- phase
- timing relatif terhadap traffic
- object yang terkena failure
- parameter recovery atau throttle jika relevan
- aturan apakah scenario dijalankan sebelum traffic atau saat traffic berjalan

### Phase C: Automatic Capture and Parsing
- tcpdump start/stop harus otomatis.
- PCAP harus disimpan per host, per scenario, per repetition.
- parsing ke CSV harus bisa dijalankan tanpa manual renaming.
- hasil parsing harus tetap bisa ditelusuri kembali ke file PCAP asal.

### Phase D: Evaluation Bundle
Setiap run scenario idealnya menghasilkan:
- JSONL utama,
- folder PCAP,
- folder CSV hasil parsing,
- catatan ringkas recovery dan packet loss,
- ringkasan status apakah run berhasil penuh atau sebagian.

### Phase E: Cleanup and Recovery
Scenario-mode harus menutup resource dengan bersih:
- hentikan tcpdump setelah run selesai,
- stop Mininet sebelum mulai run berikutnya,
- hentikan controller process setelah batch selesai,
- bersihkan file log sementara yang tidak diperlukan,
- tandai run sebagai failed jika cleanup tidak selesai normal.

---

## 5. Logging Contract

### Required Fields in Scenario JSONL
- `benchmark_mode`
- `run_id`
- `scenario_name`
- `scenario_phase`
- `scenario_index`
- `scenario_seed`
- `repetition_index`
- `repetitions`
- `topology`
- `topology_seed`
- `algorithm`
- `link_action`
- `link_target`
- `switch_target`
- `link_timing_s`
- `pingall_loss_pct`
- `tcpdump_pcap_paths`
- `tcpdump_csv_paths`
- `pcap_snaplen`
- `tcpdump_enabled`
- `throughput_mbps`
- `controller_pid`
- `controller_port`
- `controller_log_path`
- `warmup_ping`
- `event_timestamps`
- `start_time`
- `end_time`
- `duration_s`
- `status`
- `error`
- `note`

### Run-Level Metadata
Metadata berikut tetap wajib dicatat, tetapi cukup sekali per run dan tidak perlu diulang pada setiap record scenario:
- `command_line`
- `git_commit`
- `git_branch`
- `python_version`
- `mininet_version`
- `output_dir`
- `pcap_dir`
- `scenario_seed`
- `topology_seed`

Prinsip pemisahan:
- field record-level dipakai untuk analisis tiap event atau tiap host pair,
- field run-level dipakai untuk audit, reproducibility, dan tracing,
- bila ingin disimpan dalam JSONL, run-level metadata sebaiknya ditempelkan pada record pertama atau ditulis ke run manifest terpisah,
- jika pipeline nanti dibuat lebih matang, run-level metadata idealnya dipindah ke file manifest agar tidak menduplikasi data di seluruh record.

### Logging Rules
- Satu scenario run harus bisa ditelusuri dari JSONL ke PCAP ke CSV.
- Nama folder harus mencerminkan topology, algorithm, scenario, dan repetition bila relevan.
- Failure events perlu timestamp yang cukup untuk analisis recovery.
- Jangan gabungkan data run berbeda ke satu file tanpa indeks yang jelas.
- Jika scenario mengalami failure sebagian, log tetap harus valid JSONL.
- Jika ada retry, setiap percobaan harus punya `run_id` yang berbeda.

---

## 6. Evaluation Model

### Primary Metrics
- Packet loss (`pingall_loss_pct`)
- Recovery time
- Throughput saat failure dan setelah recovery
- Jumlah packet yang terekam di PCAP
- Konsistensi path setelah failure
- Perubahan latency selama event berlangsung

### Secondary Metrics
- Variansi antar scenario repetition
- Waktu startup dan shutdown process
- Dampak throttle terhadap throughput
- Stabilitas hasil pada topologi Jellyfish dibanding Ring-5
- Konsistensi hasil antar seed
- Banyaknya event yang benar-benar tercatat di `event_timestamps`

### Evaluation Questions
- Algoritma mana yang paling cepat recover?
- Apakah link flap membuat throughput turun drastis?
- Bagaimana packet loss berubah sebelum dan sesudah recovery?
- Apakah Jellyfish lebih resilien terhadap random failure?
- Apakah timing failure yang berbeda mengubah hasil secara material?
- Apakah PCAP yang dihasilkan cukup untuk membuktikan urutan kejadian?

---

## 7. Standardization Checklist

- [ ] Semua scenario yang dipakai tercantum dalam registry resmi.
- [ ] Parameter failure timing terdokumentasi.
- [ ] JSONL, PCAP, dan CSV terhubung oleh naming convention yang konsisten.
- [ ] Recovery dan packet loss bisa diaudit.
- [ ] Evaluasi bisa diulang dengan seed yang sama.
- [ ] Tidak ada output scenario yang tidak punya metadata lengkap.
- [ ] `run_id`, branch, commit, dan command line tercatat otomatis.
- [ ] `event_timestamps` terisi untuk event penting.
- [ ] `tcpdump` dan `Mininet` selalu berhenti bersih setelah run.
- [ ] Ringkasan hasil per run tersedia untuk audit cepat.
- [ ] Run-level metadata dipisahkan dari record-level metadata.
- [ ] Run manifest tersedia untuk audit reproducibility.

### Failure Handling and Retry Policy
- Retry hanya untuk kegagalan environment, bukan untuk hasil algoritma yang buruk.
- Batas retry harus kecil dan eksplisit, misalnya 1 atau 2 percobaan ulang.
- Jika retry masih gagal, batch ditandai failed dan dilaporkan apa adanya.

#### When to Abort a Run
Hentikan run jika:
- controller tidak ready dalam batas waktu yang ditentukan,
- Mininet gagal start,
- tcpdump tidak dapat dimulai,
- parsing output tidak valid,
- disk space atau permission tidak memadai.

#### When to Keep a Run
Lanjutkan run jika:
- satu host pair gagal tetapi batch masih bisa menghasilkan record lain,
- warning non-fatal muncul tetapi output JSONL tetap valid,
- controller log mencatat event yang bisa dianalisis ulang.

---

## 8. Recommended Folder Layout

```text
SPF/
├── csv/
│   ├── live-scenarios.jsonl
│   ├── pcap/
│   │   └── <topology>/<algorithm>/<scenario>/<host>.pcap
│   └── pcap-csv/
│       └── <topology>/<algorithm>/<scenario>/<host>.csv
├── testing-code/
│   ├── run_live_scenarios.py
│   └── pcap_to_csv.py
└── docs/
    └── pipeline-planning/
        ├── 01-live-mode-planning.md
        └── 02-scenario-mode-planning.md
```

---

## 9. Exit Criteria

Scenario-Mode dianggap matang jika:
- Semua scenario punya definisi yang baku.
- Failure injection, capture, dan parsing berjalan otomatis.
- Recovery analysis bisa dilakukan dari artifact yang tersedia tanpa rekonstruksi manual.
- Hasil cukup lengkap untuk masuk ke laporan evaluasi akhir.
- Run dapat diulang dari command line yang terdokumentasi.
- PCAP dan CSV punya jejak asal yang jelas ke JSONL utama.

---

## 10. Next Implementation Suggestions

1. Tambahkan scenario manifest atau registry yang lebih formal.
2. Tambahkan structured event log untuk failure dan recovery.
3. Tambahkan ringkasan evaluasi otomatis setelah parsing PCAP.
4. Tambahkan template laporan hasil scenario agar run antar minggu konsisten.
5. Tambahkan metadata environment capture untuk mempercepat audit hasil.
6. Tambahkan retry policy eksplisit untuk kegagalan non-algoritmik.
