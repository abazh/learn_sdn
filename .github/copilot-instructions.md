# Project Guidelines

## Code Style
- Prefer small, localized edits that preserve existing behavior.
- Keep Python modules directly runnable; avoid introducing extra build steps.
- Match the naming and structure already used in SPF controllers and LB scripts.
- Favor existing patterns in the nearest implementation instead of inventing new abstractions.

## Architecture
- The repository has two main areas: SPF for shortest-path forwarding labs and LB for load-balancing labs.
- SPF controllers share the SDN plumbing in [SPF/base_controller.py](../SPF/base_controller.py) and route logic in [SPF/algorithms/](../SPF/algorithms/).
- SPF algorithm modules are pure Python and should stay testable in isolation from OpenFlow.
- Use the existing docs when you need deeper context instead of duplicating explanations. Start with [README.md](../README.md) and [SPF/README.md](../SPF/README.md).

## Build and Test
- There is no compile step; run the Python scripts directly.
- Start topology and controller in separate terminals.
- SPF quick start examples: `python3 SPF/topo-spf_lab.py`, `python3 SPF/topo-weighted_lab.py`, `python3 SPF/topo-ecmp_lab.py`, `python3 SPF/topo-mesh_lab.py`.
- SPF controller examples: `python3 SPF/bfs_osken_controller.py`, `python3 SPF/dijkstra_osken_controller.py`, `python3 SPF/astar_osken_controller.py`, `python3 SPF/bellman_ford_osken_controller.py`, `python3 SPF/floyd_warshall_osken_controller.py`.
- LB quick start examples: `python3 LB/topo_lb.py` and `python3 LB/rr_lb.py`.
- Run SPF tests with `cd SPF && python3 -m pytest tests/ -v`.
- Use `scripts/clean-pycache.sh` if you need to clear Python cache files.

## Conventions
- SPF controllers follow the `_osken_controller.py` suffix and typically inherit from [SPF/base_controller.py](../SPF/base_controller.py).
- Pure routing algorithms live in [SPF/algorithms/](../SPF/algorithms/) and should remain independent of Mininet and OSKen wiring.
- Multipath and failover controllers should reuse the existing ECMP or FAST_FAILOVER patterns already documented in [SPF/README.md](../SPF/README.md) and the SPF docs.
- Prefer linking to [SPF/docs/00-overview.md](../SPF/docs/00-overview.md), [SPF/docs/09-ecmp.md](../SPF/docs/09-ecmp.md), and [SPF/docs/11-suurballe.md](../SPF/docs/11-suurballe.md) when the detail already exists there.

## SPF Evaluation Docs
- Use [SPF/EXPERIMENT_INDEX.md](../SPF/EXPERIMENT_INDEX.md) as the master catalog for pipeline inventory, sample data, and evaluation tracking.
- Use [SPF/TESTING_MODES.md](../SPF/TESTING_MODES.md) for the authoritative comparison of graph-mode, live-mode, and scenario-mode.
- Use [SPF/docs/topik1-az-guide/README.md](../SPF/docs/topik1-az-guide/README.md) as the main A-Z entry point for Topik 1.
- Use [SPF/docs/pipeline-planning/01-live-mode-planning.md](../SPF/docs/pipeline-planning/01-live-mode-planning.md) and [SPF/docs/pipeline-planning/02-scenario-mode-planning.md](../SPF/docs/pipeline-planning/02-scenario-mode-planning.md) for the structured planning docs.
- Prefer linking to these canonical docs instead of repeating the same pipeline details in new files.

## SPF Customizations
- Use [spf-evaluation.instructions.md](instructions/spf-evaluation.instructions.md) when auditing or editing SPF evaluation docs.
- Use [spf-run-log.prompt.md](prompts/spf-run-log.prompt.md) when generating or filling an operational run log.
- Use [spf-topik1-doc-audit.agent.md](agents/spf-topik1-doc-audit.agent.md) when you want a focused documentation audit for Topik 1.

## Agent Bootstrap

When bootstrapping an AI assistant for this workspace, follow a lightweight, link-first workflow:

- **Discover**: search for instruction files and docs using these patterns: `**/.github/copilot-instructions.md`, `**/AGENTS.md`, `**/AGENT.md`, `**/README.md`, and any `*.md` under `SPF/docs/`.
- **Explore**: collect run/build/test commands and high-level architecture from: `README.md`, `SPF/README.md`, `SPF/docs/*`, and `SPF/tests/`.
- **Merge, don't duplicate**: prefer adding short guidance that links to existing docs rather than embedding long content. Keep the file small and actionable.
- **Suggested minimal contents**: quick start commands, test commands, important file locations, and examples of common tasks (run a topology, start a controller, run tests).
- **Example prompts** agents can use:
	- "List the commands to run the SPF lab topologies and controllers." 
	- "Where are the algorithm implementations and their tests?"
	- "Summarize the README and SPF/README quick-start steps."

If you update this file, make a small focused change, link to the canonical docs, and run `git commit` + `git push` so maintainers can review.
