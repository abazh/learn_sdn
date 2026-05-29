#!/usr/bin/env bash
set -eu

# Run from repo root regardless of where the script is invoked
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO_ROOT"

TS=$(date +%Y%m%d-%H%M%S)
mkdir -p SPF/csv/runs/$TS

python3 SPF/testing-code/run_live_scenarios.py \
  --topologies jellyfish \
  --output SPF/csv/runs/$TS/live-jellyfish-all.jsonl \
  --pcap-dir SPF/csv/runs/$TS/pcap \
  --controller-log SPF/csv/runs/$TS/controller.log
