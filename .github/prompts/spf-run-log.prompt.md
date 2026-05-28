---
description: "Fill an SPF run log from live-mode or scenario-mode execution notes and outputs."
---
# SPF Run Log Builder

You are given notes, commands, and outputs from an SPF benchmark run. Produce a completed run log using `SPF/docs/pipeline-planning/03-run-log-template.md`.

## Requirements
- Do not invent values. If something is unknown, use `[unknown]`.
- Keep run-level metadata separate from record-level metrics.
- Preserve the distinction between live-mode and scenario-mode fields.
- Prefer concise, audit-friendly wording.
- Include only evidence that is supported by the provided notes or artifacts.
- If the run was partial or failed, say so explicitly and note the likely cause.

## Inputs to extract
- Mode: live or scenario
- Topology and algorithm
- Scenario name, if any
- Run ID, repetition index, and seed values
- Command line
- Git branch and commit
- Python, Mininet, and OSKen versions if known
- Start and end time, or best available timestamps
- Output paths for JSONL, CSV, PCAP, or controller logs
- Main throughput, hop count, runtime, packet loss, and recovery observations
- Issues encountered and how they were handled
- Final verdict and next action

## Output
Return a single markdown run log that is ready to save under `SPF/csv/run-logs/`.

## Suggested structure
1. Run Summary
2. Environment Metadata
3. Execution Parameters
4. Run-Level Metadata
5. Record-Level Summary
6. Mode-Specific Notes
7. Output Bundle Checklist
8. Issues and Resolutions
9. Final Summary
10. Copy-Paste Notes for Report
