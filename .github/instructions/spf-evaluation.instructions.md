---
description: "Use when auditing, updating, or creating SPF experiment evaluation docs, run plans, run logs, and testing-mode guidance."
applyTo: "SPF/docs/**/*.md,SPF/experiment_plan.md,SPF/EXPERIMENT_INDEX.md,SPF/TESTING_MODES.md"
---
# SPF Evaluation Workflow

- Keep graph-mode, live-mode, and scenario-mode clearly separated.
- Prefer canonical docs over duplicated explanations. Link to existing docs instead of rewriting the same content.
- When editing evaluation docs, preserve the distinction between record-level fields and run-level metadata.
- Use the run log template in `SPF/docs/pipeline-planning/03-run-log-template.md` as the default operational log format.
- If a doc changes a workflow, update the relevant navigation or index page so the new entry point is discoverable.
- For claims about behavior or availability, rely on the actual codebase and sample outputs in `SPF/`.
- If a missing capability is identified, label it as a gap or recommendation rather than implying it already exists.
- Keep edits small, consistent, and aligned with the existing SPF documentation style.

## Suggested review checklist
- Are live-mode and scenario-mode distinctions explicit?
- Are run-level metadata and record-level metadata separated?
- Are links to canonical docs present and correct?
- Does the page mention what is verified in code versus what is still a recommendation?
- If a new artifact was added, is it linked from `SPF/EXPERIMENT_INDEX.md` and/or `SPF/docs/topik1-az-guide/INDEX.md`?
