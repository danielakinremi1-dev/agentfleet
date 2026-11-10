# Design direction

The reference mockup is saved next to this file as `mockup.jpg`. It is a reference for palette and
layout only. Rebuild all content from real data and use AgentFleet branding.

## Visual identity (restrained sci-fi command center)
- Dark navy/charcoal base, teal/cyan for active states, amber for warnings, red for failures.
- Clean typography, restrained glow and animation, highly readable technical data.
- Should look like professional developer tooling, not a game menu.

## From the mockup
**Keep:** dark navy palette, card-based panels, left icon rail, header status strip (system, region, UTC time),
agent cards with live load sparklines, telemetry tiles, system-health panel with progress indicators.

**Change:** drop the ornate border and serif title treatment, use real data instead of placeholder metrics,
replace the Gantt-style timeline with a workflow graph (workflows are DAGs; React Flow), and use AgentFleet branding.

**Add (core to the product, absent from the mockup):** approvals queue, execution inspector
(inputs, outputs, tool calls, retries, token cost), live workflow graph, evaluation results view.

## Pages (roadmap Phase 6)
Runs list, run detail (live workflow graph, timeline and execution inspector) and approvals.
The workflow builder and analytics pages are P2 ([ADR-0007](../decisions/0007-roadmap-restructure.md)).
