# SPF Run Log Template — Live / Scenario Evaluation

**Purpose**: Template operasional untuk mencatat satu eksekusi eksperimen live-mode atau scenario-mode secara seragam, audit-friendly, dan mudah dibandingkan antar run.

**Use Case**:
- Live-mode benchmark run
- Scenario-mode failure / recovery run
- Batch eksperimen yang perlu reproducibility dan review cepat

**Recommended Storage**:
- `SPF/csv/run-logs/`
- File name pattern: `runlog_<mode>_<topology>_<algorithm>_<scenario>_<YYYYMMDD-HHMMSS>.md`

---

## 1. Run Summary

- **Run ID**: [unique-id]
- **Mode**: [live | scenario]
- **Topology**: [ring5 | jellyfish]
- **Algorithm**: [astar | bellman_ford | widest_path]
- **Scenario**: [baseline_no_failure | link_down_before_traffic | link_down_during_traffic | link_flap | switch_down | bandwidth_throttle | random_link_down_jellyfish | n/a]
- **Repetition Index**: [0-based index]
- **Total Repetitions**: [number]
- **Scenario Index**: [0-based index or n/a]
- **Scenario Seed**: [number or n/a]
- **Topology Seed**: [number or n/a]
- **Start Time**: [ISO 8601 UTC]
- **End Time**: [ISO 8601 UTC]
- **Duration**: [seconds]
- **Status**: [success | partial | failed]
- **Operator**: [name/initials]

---

## 2. Environment Metadata

### System Context
- **Host OS**: [Windows / Linux / macOS]
- **Shell**: [PowerShell / bash / zsh]
- **Python Version**: [python --version]
- **Mininet Version**: [mn --version or n/a]
- **OSKen Version**: [version or n/a]
- **Scapy Installed**: [yes/no]
- **tcpdump Available**: [yes/no]
- **Disk Space Available**: [estimated free space]

### Git Context
- **Branch**: [git branch]
- **Commit**: [git commit hash]
- **Working Tree Clean**: [yes/no]
- **Command Line**: [exact command used]
- **Run Directory**: [absolute or workspace-relative path]
- **Output Directory**: [where JSONL/CSV written]
- **Controller Log Path**: [if used]
- **PCAP Directory**: [if used]

---

## 3. Execution Parameters

### Common Parameters
- **Warmup Ping**: [true/false]
- **Max Host Pairs**: [number or n/a]
- **Repetitions**: [number]
- **iperf Duration**: [seconds]
- **iperf Parallel**: [streams]
- **iperf Port**: [port]
- **Default Bandwidth Mbps**: [number]

### Live-Mode Parameters
- **Topology Name**: [ring5/jellyfish]
- **Algorithm Name**: [astar/bellman_ford/widest_path]
- **Controller Script**: [path]
- **Controller PID**: [pid]
- **Controller Port**: [port]
- **Output JSONL**: [path]
- **CSV Output**: [path]

### Scenario-Mode Parameters
- **Scenario List**: [comma-separated list]
- **Link Down Delay**: [seconds]
- **Link Up Delay**: [seconds]
- **Throttle Bandwidth**: [Mbps]
- **Throttle Delay**: [ms]
- **tcpdump Enabled**: [true/false]
- **tcpdump Snaplen**: [bytes]
- **PCAP Prefix**: [path]
- **Scenario Manifest**: [path or n/a]

---

## 4. Run-Level Metadata

Metadata berikut dicatat sekali per run, bukan diulang di setiap record JSONL.

- **Command Line**: [exact command]
- **Git Branch**: [branch]
- **Git Commit**: [hash]
- **Python Version**: [version]
- **Mininet Version**: [version]
- **OSKen Version**: [version or n/a]
- **Run Manifest Path**: [optional manifest file]
- **Controller Log Path**: [path]
- **Output Directory**: [path]
- **PCAP Directory**: [path or n/a]
- **Start Time**: [ISO 8601 UTC]
- **End Time**: [ISO 8601 UTC]
- **Duration**: [seconds]

### Run-Level Notes
- Gunakan section ini untuk audit dan reproducibility.
- Jika pipeline sudah matang, metadata ini idealnya dipindah ke file manifest terpisah.
- Jika masih disimpan di JSONL, cukup tempelkan pada record pertama agar tidak menduplikasi seluruh record.

---

## 5. Record-Level Summary

Isi tabel ini untuk ringkasan hasil utama dari JSONL yang dihasilkan.

| Record | Source Host | Destination Host | Source Switch | Destination Switch | Hop Count | Path Cost | Runtime ms | Throughput Mbps | Status | Notes |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 1 | [h1] | [h2] | [s1] | [s2] | [0] | [0] | [0.00] | [0.00] | [success] | [note] |
| 2 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Record-Level Fields To Review
- `benchmark_mode`
- `topology`
- `algorithm`
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
- `iperf_summary`
- `scenario_name` (scenario-mode only)
- `scenario_phase` (scenario-mode only)
- `link_action` (scenario-mode only)
- `link_target` (scenario-mode only)
- `switch_target` (scenario-mode only)
- `link_timing_s` (scenario-mode only)
- `pingall_loss_pct` (scenario-mode only)
- `tcpdump_pcap_paths` (scenario-mode only)
- `tcpdump_csv_paths` (scenario-mode only)
- `event_timestamps` (scenario-mode only)

---

## 6. Live-Mode Notes

### Live Run Focus
- **Goal**: validasi throughput nyata, RTT, dan execution overhead.
- **Primary Outputs**: JSONL + CSV.
- **Expected Evidence**: iperf summary, throughput stabil, controller log lengkap.

### Live Run Observations
- **Startup Time**: [seconds]
- **Warmup Ping Result**: [pass/fail]
- **Throughput Mean**: [Mbps]
- **Throughput Min/Max**: [Mbps]
- **RTT Summary**: [mean/min/max if available]
- **Retransmits**: [count]
- **Anomalies**: [none / description]

### Live Run Quality Check
- [ ] Output JSONL valid.
- [ ] CSV conversion sukses.
- [ ] Run-level metadata tercatat.
- [ ] Tidak ada process yang tertinggal.
- [ ] Hasil dapat diulang dengan command yang sama.

---

## 7. Scenario-Mode Notes

### Scenario Run Focus
- **Goal**: validasi resilience, recovery, packet loss, dan packet-level evidence.
- **Primary Outputs**: JSONL + CSV + PCAP.
- **Expected Evidence**: event timestamps, loss percentage, PCAP, recovery timing.

### Scenario Run Observations
- **Scenario Name**: [name]
- **Scenario Phase**: [pre | during | baseline]
- **Link / Switch Target**: [target]
- **Failure Trigger Time**: [seconds after traffic start]
- **Recovery Trigger Time**: [seconds after traffic start]
- **Packet Loss**: [%]
- **Recovery Time**: [seconds]
- **Throughput Under Failure**: [Mbps]
- **PCAP Count**: [number]
- **CSV Count**: [number]
- **Anomalies**: [none / description]

### Scenario Run Quality Check
- [ ] Scenario registry sesuai dengan yang direncanakan.
- [ ] Failure timing tercatat.
- [ ] PCAP tersimpan untuk host yang relevan.
- [ ] CSV parsing sukses.
- [ ] Recovery analysis bisa dilakukan tanpa rekonstruksi manual.

---

## 8. Output Bundle Checklist

### Live-Mode Bundle
- [ ] JSONL tersedia.
- [ ] CSV tersedia.
- [ ] Controller log tersedia.
- [ ] Run log ini terisi.

### Scenario-Mode Bundle
- [ ] JSONL tersedia.
- [ ] CSV tersedia.
- [ ] PCAP tersedia.
- [ ] Parsed PCAP CSV tersedia.
- [ ] Run log ini terisi.

---

## 9. Issues and Resolutions

### Issue Log
| Issue | Impact | Resolution | Status |
|---|---|---|---|
| [describe issue] | [high/medium/low] | [how fixed] | [open/resolved] |
| [describe issue] | [high/medium/low] | [how fixed] | [open/resolved] |

### Notes
- [ ] Environment issue
- [ ] Topology issue
- [ ] Controller issue
- [ ] Traffic issue
- [ ] Packet capture issue
- [ ] Parsing issue

---

## 10. Final Summary

### Run Verdict
- **Verdict**: [success | partial | failed]
- **Main Finding**: [short summary]
- **Best / Worst Observation**: [short summary]
- **Follow-up Needed**: [yes/no]

### Next Action
- [ ] Re-run with same parameters
- [ ] Compare with another algorithm
- [ ] Compare with another topology
- [ ] Inspect controller logs
- [ ] Inspect PCAP / CSV outputs

---

## 11. Copy-Paste Notes for Report

### Short Summary
> [Insert a concise summary of the run, including topology, algorithm, mode, and the main result.]

### Important Evidence
> [Insert the strongest evidence from JSONL/CSV/PCAP that supports the conclusion.]

### Recommendation
> [Insert the follow-up recommendation based on this run.]

---

## 12. File Links

- [Live-Mode Planning](01-live-mode-planning.md)
- [Scenario-Mode Planning](02-scenario-mode-planning.md)
- [Experiment Index](../../EXPERIMENT_INDEX.md)
- [Testing Modes](../../TESTING_MODES.md)
