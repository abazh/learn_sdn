# Peta File dan Fungsi

Dokumen ini adalah katalog file yang paling relevan untuk Topik 1, dengan fokus pada file yang dipakai dalam eksperimen, evaluasi, dan dokumentasi pipeline.

## 1. Dokumen Referensi
- `SPF/README.md`: dokumentasi utama SPF, termasuk quick start dan benchmark pipeline.
- `SPF/experiment_plan.md`: rencana eksperimen Topik 1 yang lebih operasional.
- `SPF/EXPERIMENT_INDEX.md`: indeks komponen, status testing, dan template evaluasi.
- `SPF/TESTING_MODES.md`: perbandingan capability graph-mode, live-mode, dan scenario-mode.
- `SPF/docs/00-overview.md`: ringkasan arsitektur SPF.
- `SPF/docs/09-ecmp.md`: referensi multipath/ECMP.
- `SPF/docs/11-suurballe.md`: referensi failover dan edge-disjoint paths.
- `SPF/docs/topik1-az-guide/README.md`: entry point panduan A-Z.
- `SPF/docs/topik1-az-guide/INDEX.md`: pintu masuk lokal yang lebih ringkas.
- `SPF/docs/topik1-az-guide/arsitektur.md`: gambaran arsitektur eksperimen.
- `SPF/docs/topik1-az-guide/alur.md`: alur kerja end-to-end.
- `SPF/docs/topik1-az-guide/testing.md`: arsitektur testing.
- `SPF/docs/topik1-az-guide/checklist.md`: checklist kesiapan.

## 2. File Topologi
- `SPF/topo-ring5_lab.py`: topologi baseline ring-5 untuk perbandingan utama.
- `SPF/jellyfish_topo.py`: topologi jellyfish yang dipakai sebagai pembanding utama.
- `SPF/topo-spf_lab.py`: baseline topology tambahan untuk demo atau eksplorasi.
- `SPF/topo-mesh_lab.py`: mesh topology untuk eksplorasi jalur alternatif.
- `SPF/topo-weighted_lab.py`: topology berbobot yang mendukung metadata bandwidth.

## 3. File Controller
- `SPF/base_controller.py`: plumbing controller umum.
- `SPF/astar_osken_controller.py`: controller A*.
- `SPF/bellman_ford_osken_controller.py`: controller Bellman-Ford.
- `SPF/widest_path_osken_controller.py`: controller Widest-Path.
- `SPF/astar_multipath_osken_controller.py`: controller A* multipath.
- `SPF/dijkstra_osken_controller.py`: controller Dijkstra.
- `SPF/dijkstra_multipath_osken_controller.py`: controller Dijkstra multipath.
- `SPF/kshortest_osken_controller.py`: controller Yen k-shortest.
- `SPF/suurballe_fast_failover_osken_controller.py`: controller failover Suurballe.
- `SPF/suurballe_balanced_failover_osken_controller.py`: controller failover Suurballe balanced.

## 4. File Algoritma
- `SPF/algorithms/astar.py`: implementasi A*.
- `SPF/algorithms/bellman_ford.py`: implementasi Bellman-Ford.
- `SPF/algorithms/widest_path.py`: implementasi Widest-Path.
- `SPF/algorithms/dijkstra.py`: implementasi Dijkstra.
- `SPF/algorithms/floyd_warshall.py`: implementasi Floyd-Warshall.
- `SPF/algorithms/suurballe.py`: implementasi Suurballe.
- `SPF/algorithms/yen_k_shortest.py`: implementasi Yen k-shortest.
- `SPF/algorithms/group_ids.py`: utilitas group ID untuk multipath.

## 5. File Benchmark dan Data
- `SPF/benchmark_core.py`: mesin inti benchmark, graph builder, live helpers, dan record builder.
- `SPF/benchmark_algorithms.py`: CLI benchmark graph-mode dan live-mode.
- `SPF/benchmark_jsonl_to_csv.py`: konversi JSONL ke CSV.
- `SPF/testing-code/run_live_scenarios.py`: runner scenario-mode dengan failure injection.
- `SPF/testing-code/pcap_to_csv.py`: parser PCAP ke CSV.
- `SPF/benchmark-csv/`: contoh output CSV hasil graph-mode.
- `SPF/benchmark-live-csv/`: contoh output CSV hasil live-mode.
- `SPF/csv/`: output scenario, pcap, dan hasil konversi.

## 6. File Test
- `SPF/tests/conftest.py`: fixture dan helper bersama.
- `SPF/tests/test_astar.py`: test A*.
- `SPF/tests/test_bellman_ford.py`: test Bellman-Ford.
- `SPF/tests/test_widest_path.py`: test Widest-Path.
- `SPF/tests/test_bfs.py`: test BFS.
- `SPF/tests/test_dijkstra.py`: test Dijkstra.
- `SPF/tests/test_floyd_warshall.py`: test Floyd-Warshall.
- `SPF/tests/test_suurballe.py`: test Suurballe.
- `SPF/tests/test_yen_k_shortest.py`: test Yen k-shortest.
- `SPF/tests/test_group_ids.py`: test utilitas group ID.
- `SPF/tests/test_benchmark_core.py`: test pipeline benchmark core.

## 7. File Planning Tambahan yang Relevan
- `SPF/docs/pipeline-planning/01-live-mode-planning.md`: planning untuk standarisasi live-mode.
- `SPF/docs/pipeline-planning/02-scenario-mode-planning.md`: planning untuk standarisasi scenario-mode.

## 8. Cara Pakai Peta Ini
Gunakan file ini saat:
- mencari lokasi fungsi atau test tertentu,
- menyusun laporan eksperimen,
- memeriksa apa yang sudah ada versus apa yang masih perlu dibangun,
- menautkan artefak data dengan bagian pipeline yang menghasilkan artefak tersebut.
