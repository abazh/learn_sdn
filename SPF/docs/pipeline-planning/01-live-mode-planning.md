# Live-Mode Planning — SPF Pipeline Standardization

**Purpose**: Rencana implementasi dan standardisasi untuk Live-Mode agar eksekusi, logging, evaluasi, dan pengulangan eksperimen menjadi lebih profesional, terukur, dan otomatis.

**Scope**: `SPF/benchmark_algorithms.py --mode live` dan seluruh alur yang bergantung pada `SPF/benchmark_core.py`.

**Status**: Planning document

---

## 1. Goal Statement

Live-Mode harus menjadi mode evaluasi end-to-end yang konsisten untuk mengukur performa algoritma pada topologi emulasi nyata, tanpa campur tangan manual berlebih. Mode ini bukan sekadar menjalankan benchmark, tetapi menghasilkan artefak yang siap dianalisis ulang, dibandingkan lintas run, dan dipakai untuk laporan formal.

### Target Outcome
- Eksekusi otomatis untuk kombinasi topologi dan algoritma yang terdefinisi.
- Logging yang stabil, terstruktur, dan mudah diparse.
- Hasil yang bisa direproduksi pada level konfigurasi, sejauh kondisi Mininet memungkinkan.
- Output yang dapat langsung dikonversi ke CSV untuk analisis statistik.
- Metadata cukup lengkap untuk audit ulang tanpa membaca raw log secara manual.

---

## 2. Current State in Codebase

### Existing Components
- CLI utama: [SPF/benchmark_algorithms.py](../../benchmark_algorithms.py)
- Shared core: [SPF/benchmark_core.py](../../benchmark_core.py)
- Live runner support: `benchmark_records_live()`
- Topology sources:
  - [SPF/topo-ring5_lab.py](../../topo-ring5_lab.py)
  - [SPF/jellyfish_topo.py](../../jellyfish_topo.py)
- Output converter: [SPF/benchmark_jsonl_to_csv.py](../../benchmark_jsonl_to_csv.py)
- Sample live output: [SPF/benchmark-live.jsonl](../../benchmark-live.jsonl)

### Practical Constraints
- Live-Mode hanya mendukung 1 topologi dan 1 algoritma per run.
- Throughput nyata berasal dari iperf3, bukan estimasi graph-mode.
- Durasi run dipengaruhi oleh startup Mininet, startup controller, warmup ping, dan `--iperf-duration`.
- Hasil bisa sedikit bervariasi antar repetition karena timing emulasi dan startup process.

---

## 3. Standard Operating Model

### Recommended Execution Pattern
1. Select topology and algorithm explicitly.
2. Start benchmark in live mode.
3. Capture JSONL output per run.
4. Convert JSONL to CSV immediately after completion.
5. Store run metadata in a run log.
6. Compare results across runs using the same schema.

### Preflight Checks
Before a live run, verify:
- Mininet is installed and available in PATH.
- OSKen controller scripts are reachable from `SPF/`.
- The selected topology file exists and matches the intended parameters.
- The chosen controller is the final version for the experiment.
- Output directories are writable and disk space is sufficient.
- No stale Mininet or controller processes remain from previous runs.

### Recommended Run Shape
- Use one algorithm per run and one topology per run, matching the current CLI contract.
- Use a small `--max-pairs` during smoke checks, then increase only after the pipeline is stable.
- Keep `--iperf-duration` fixed across a comparison batch so throughput is comparable.
- Keep `--jellyfish-seed` fixed for Jellyfish comparison batches to avoid topology drift.
- Store the exact command line in the run log.

### Recommended Commands
```bash
python3 SPF/benchmark_algorithms.py \
  --mode live \
  --topologies ring5 \
  --algorithms widest_path \
  --max-pairs 5 \
  --iperf-duration 5 \
  --iperf-parallel 1 \
  --output SPF/csv/live-ring5-widest_path.jsonl

python3 SPF/benchmark_jsonl_to_csv.py \
  --input SPF/csv/live-ring5-widest_path.jsonl \
  --output-dir SPF/csv/live-ring5 \
  --split-by topology,algorithm
```

---

## 4. Automation Targets

### Phase A: Repeatable Run Wrapper
Buat wrapper yang menerima parameter berikut:
- topology
- algorithm
- repetitions
- max_pairs
- iperf_duration
- iperf_parallel
- output directory
- controller log path

### Phase B: Matrix Runner and Baseline Strategy
Tambahkan lapisan eksekusi yang bisa menjalankan batch eksperimen secara terurut:
- baseline run untuk ring5 dan jellyfish.
- per-algorithm live run dengan parameter yang sama.
- optional comparison batch dengan repetition lebih dari satu.

Prinsipnya:
- jangan campur graph-mode dan live-mode di satu artefak output,
- simpan baseline sebelum variasi parameter,
- gunakan naming convention yang konsisten untuk setiap batch.

### Phase C: Deterministic Run Metadata
Setiap run wajib menyimpan:
- `run_id` yang unik,
- branch,
- commit hash,
- start/end timestamp,
- duration_s,
- OS / environment notes,
- topology dan algorithm yang dipakai,
- topology_seed bila relevan,
- iperf parameters,
- warmup_ping status,
- controller log path,
- output file path,
- exit code.

### Phase D: Automatic Conversion
Setelah JSONL selesai, langsung jalankan conversion ke CSV sehingga hasil tidak tersebar di beberapa format tanpa indeks yang jelas.

Tambahkan juga ringkasan hasil per run:
- total record yang sukses,
- total record yang gagal,
- throughput min/mean/max,
- runtime min/mean/max,
- catatan error bila ada.

### Phase E: Cleanup and Recovery
Setiap eksekusi live-mode harus menutup resource dengan bersih:
- hentikan controller process setelah run selesai,
- stop Mininet sebelum mulai run berikutnya,
- bersihkan file log sementara yang tidak diperlukan,
- tandai run sebagai failed jika cleanup tidak selesai normal.

---

## 5. Logging Contract

### Required Fields in Live JSONL
- `benchmark_mode`
- `run_id`
- `topology`
- `algorithm`
- `topology_seed`
- `source_host`
- `destination_host`
- `source_switch`
- `destination_switch`
- `runtime_ms`
- `hop_count`
- `path_cost`
- `path_string`
- `throughput_estimate_mbps`
- `throughput_mbps`
- `controller_pid`
- `controller_port`
- `iperf_duration_s`
- `iperf_parallel`
- `warmup_ping`
- `record_index`
- `total_records`
- `iperf_summary`
- `summary_stats`
- `status`
- `error`
- `note`

### Run-Level Metadata
Metadata berikut tetap wajib dicatat, tetapi cukup sekali per run dan tidak perlu diulang pada setiap record live JSONL:
- `command_line`
- `git_commit`
- `git_branch`
- `python_version`
- `mininet_version`
- `output_dir`
- `controller_log_path`
- `start_time`
- `end_time`
- `duration_s`

Prinsip pemisahan:
- field record-level dipakai untuk analisis tiap host pair,
- field run-level dipakai untuk audit, reproducibility, dan tracing,
- bila ingin disimpan dalam JSONL, run-level metadata sebaiknya ditempelkan pada record pertama atau ditulis ke run manifest terpisah,
- jika pipeline nanti dibuat lebih matang, run-level metadata idealnya dipindah ke file manifest agar tidak menduplikasi data di seluruh record.

### Logging Rules
- Satu run menghasilkan satu file JSONL utama.
- Nama file harus mencerminkan topology, algorithm, dan tanggal run.
- Output CSV mengikuti nama file JSONL atau grouping yang ditentukan oleh split fields.
- Controller log dipisahkan dari hasil benchmark utama.
- Jika satu record gagal, log tetap harus valid JSONL dan mencatat error tanpa menghentikan seluruh run kecuali ada kegagalan fatal.
- Jika run diulang, setiap repetition harus punya `run_id` yang berbeda.
- Jangan menyimpan hasil sementara sebagai final output sebelum conversion sukses.

---

## 6. Evaluation Model

### Primary Metrics
- Real throughput (`throughput_mbps`)
- Runtime algoritma (`runtime_ms`)
- Hop count (`hop_count`)
- Path cost (`path_cost`)
- Iperf retransmit rate
- RTT summary dari `iperf_summary`
- Record success rate
- Cleanup success rate
- Per-run duration

### Secondary Metrics
- CPU utilization
- Stability antar repetition
- Variansi throughput
- Kesesuaian path yang dipilih dengan ekspektasi topology
- Controller startup time
- Warmup ping success rate

### Evaluation Questions
- Algoritma mana yang memberi throughput paling stabil?
- Apakah hasil live konsisten antar repetition?
- Apakah ada penurunan throughput signifikan pada topology tertentu?
- Apakah controller startup mempengaruhi hasil secara material?
- Apakah satu topology memerlukan warmup atau retry yang berbeda?
- Apakah failure pada satu record mengganggu keseluruhan batch?

---

## 7. Standardization Checklist

- [ ] Semua parameter live-mode terdokumentasi di satu tempat.
- [ ] Naming output konsisten.
- [ ] JSONL selalu dikonversi ke CSV setelah run.
- [ ] Metadata run disimpan terpisah.
- [ ] Hasil bisa dibandingkan lintas commit dan lintas topology.
- [ ] Tidak ada evaluasi manual tanpa log yang bisa direproduksi.
- [ ] Run ID, commit hash, branch, dan command line tercatat otomatis.
- [ ] Run-level metadata dipisahkan dari record-level metadata.
- [ ] Run manifest tersedia untuk audit reproducibility.
- [ ] Controller dan Mininet selalu berhenti bersih setelah run.
- [ ] Retry policy ditetapkan untuk run yang gagal karena kondisi environment.
- [ ] Summary statistik otomatis dibuat setelah CSV conversion.
- [ ] Dataset final disimpan dengan naming convention yang konsisten.

### Failure Handling and Retry Policy
- Retry hanya untuk kegagalan environment, bukan untuk hasil algoritma yang buruk.
- Batas retry harus kecil dan eksplisit, misalnya 1 atau 2 percobaan ulang.
- Jika retry masih gagal, batch ditandai gagal dan dilaporkan apa adanya.

#### When to Abort a Run
Hentikan run jika:
- controller tidak ready dalam batas waktu yang ditentukan,
- Mininet gagal start,
- iperf3 tidak menghasilkan output yang bisa diparse,
- cleanup sebelumnya belum selesai,
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
│   ├── live-*.jsonl
│   ├── live-*/
│   └── run-logs/
├── benchmark_algorithms.py
├── benchmark_core.py
├── benchmark_jsonl_to_csv.py
└── docs/
    └── pipeline-planning/
        ├── 01-live-mode-planning.md
        └── 02-scenario-mode-planning.md
```

---

## 9. Exit Criteria

Live-Mode dianggap siap pakai secara matang jika:
- Run bisa dijalankan dengan parameter yang sama dan menghasilkan schema output yang sama.
- CSV hasil konversi konsisten antar run.
- Metadata cukup untuk audit ulang.
- Evaluasi bisa dilakukan tanpa membaca raw controller log secara manual.
- Batch live-mode bisa dijalankan ulang dari run log yang sama.
- Failure environment kecil tidak merusak seluruh dataset.
- Semua output dapat dihubungkan ke commit dan branch tertentu.

---

## 10. Next Implementation Suggestions

1. Tambahkan wrapper eksekusi untuk matrix topology x algorithm.
2. Tambahkan run log format baku.
3. Tambahkan post-run conversion otomatis ke CSV.
4. Tambahkan ringkasan evaluasi per run agar hasil mudah dibandingkan.
5. Tambahkan metadata environment capture untuk mempercepat audit hasil.
6. Tambahkan retry policy yang eksplisit untuk kegagalan non-algoritmik.
