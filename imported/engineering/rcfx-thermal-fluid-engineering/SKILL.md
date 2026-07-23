---
name: rcfx-thermal-fluid-engineering
description: Domain-rigor skill for multi-stage counter-flow fluidized bed heat exchange systems (RCFX), lunar ISRU regolith processing, He-3 extraction thermal recovery, multiphase flow under vacuum/extreme conditions, patent disclosure packets, calculation plans, uncertainty analysis, trade studies, and manuscript sections. Use for heat transfer, fluidization regimes, pressure drop, particle-gas interactions, radiative/conductive limits, scaling laws, CFD/experiment validation checks, invention support. Produces research briefs, design comparisons, methods/results drafts, provisional patent technical content, evidence packets. Triggers on RCFX, fluidized bed, lunar heat recovery, ISRU thermal, regolith processing, He-3, multiphase vacuum systems, or related patent/manuscript work.
---

# RCFX Thermal-Fluid Engineering

## Overview

Domain judgment layer for thermal-fluid systems in lunar and offworld ISRU contexts, centered on multi-stage counter-flow fluidized bed heat exchangers (RCFX family). Enforce physical defensibility: validity ranges of correlations, regime maps (packed → fluidized → bubbling → slugging → pneumatic), uncertainty propagation, scaling limits between DEM/CFD and full system, and explicit separation of measured vs. inferred performance under vacuum, low-g, abrasive/cohesive regolith, and extreme thermal gradients.

This skill layers mechanical-engineering research rigor onto ISRU-specific constraints. Prefer primary sources: NASA/DOE technical reports, peer-reviewed multiphase literature, manufacturer datasheets for high-temp materials, and prior patents. Treat marketing or uncited summaries as orientation only.

## Research Workflow

1. Clarify the engineering objective.
   - System: stages, bed geometry, gas (He, Ar, N2, process gas), solid (regolith simulant properties: size distribution, density, cohesion, thermal conductivity).
   - Operating regime: pressure (vacuum to mild overpressure), temperature bounds, gravity level, mass flow rates, target heat recovery efficiency, pressure-drop budget.
   - Performance metrics and hard constraints (attrition, electrostatics, radiative loss, power for fans/blowers in vacuum).
   - State assumptions explicitly when data missing; only query user for values that change the path.

2. Build source hierarchy.
   - Standards/handbooks, peer-reviewed multiphase/fluidization papers, NASA technical memoranda, primary patents, validated DEM/CFD studies with mesh/particle independence.
   - Extract equations, dimensionless groups (Re_p, Ar, Umf, Nu, Bi), material limits, empirical constants, and applicability envelopes (particle diameter, gas velocity, temperature, pressure).

3. Extract engineering substance and validity.
   - Record what was measured vs. simulated vs. assumed.
   - Flag correlation misuse (e.g., Wen-Yu or Ergun outside calibrated range for lunar-like particles).
   - Note multiphase regime transitions and heat-transfer mechanism shifts (conduction-dominated packed → particle convection in fluidized → radiation at high T).

4. Compare alternatives by mechanism.
   - Explain performance differences via dominant physics (pressure drop vs. HTC trade-off, stage count vs. complexity, gas recirculation energy cost).
   - Include manufacturability, instrumentation under vacuum, maintenance, safety (dust, electrostatic discharge), cost, and scaling.

5. Produce decision-ready output.
   - Lead with recommendation or state of evidence.
   - Include assumptions, key equations with units and limits, source quality, uncertainty bounds, next verification steps (simple analytical sanity, reduced-order model, targeted DEM, or lab simulant test).
   - Mark inference explicitly.

## Thermal-Fluid & Multiphase Checks (RCFX-specific)

Before finalizing any claim:

- Fluidization: minimum fluidization velocity Umf (Ergun/Wen-Yu or measured), excess velocity, regime map (Geldart group for lunar regolith analogs), bed expansion, bubble size/frequency, segregation risk.
- Heat transfer: particle-gas HTC, wall-to-bed, inter-stage recovery effectiveness; radiation contribution at >800 K; contact resistance and coating effects.
- Pressure drop: ΔP across stages, fan/blower power in rarefied gas, choking risk.
- Vacuum/low-g effects: mean free path vs. particle diameter (Knudsen), reduced buoyancy, altered bubble dynamics, electrostatic charging of dielectric regolith.
- Material limits: abrasion/attrition rates, sintering/cohesion at high T, thermal stress on walls, outgassing.
- Scaling: DEM particle count limits vs. continuum CFD validity; benchtop simulant → lunar fidelity gaps (atmosphere, gravity, composition).
- Uncertainty: property variation with T/P, measurement error on particle size distribution, model form uncertainty.

For CFD/DEM:
- Require turbulence/particle model, wall treatment, independence study, BC specification, validation data before treating as evidence.
- Prefer analytical or empirical bounds as first sanity check.

## Output Patterns

**Research brief**
- Question / Bottom Line / Assumptions / Evidence (cited) / Models & Correlations (eqs + limits) / Tradeoffs / Gaps / Next Steps

**Trade study / design comparison**
- Compact matrix scored on efficiency, ΔP, complexity, scalability, risk; dominant physics explanation per cell.

**Calculation plan**
- Step-by-step equations, input ranges, sensitivity variables, expected output format, verification method.

**Manuscript support**
- Methods: geometry, properties, regime justification, model assumptions.
- Results/Discussion: figure-led, mechanism interpretation, uncertainty, limitations specific to lunar conditions.

**Invention disclosure / patent-support packet**
- Technical description of multi-stage counter-flow architecture, novelty relative to prior art (single-stage, fixed-bed, different gas-solid contactors), key claims support (effectiveness, pressure minimization, vacuum operability), figure list, prior-art comparison table, experimental or simulation evidence summary. Defer legal claim scope and filing strategy to counsel.

**Proposal narrative (NASA/DOE style)**
- Objectives, technical approach with rigor gates, milestones, risks/mitigations, broader impact for cislunar ISRU.

## Rigor Gate

- Never present unvalidated high-fidelity simulation as definitive evidence.
- Explicitly flag leaps: e.g., terrestrial correlation applied to 1/6 g vacuum without correction factor discussion.
- Prefer reversible, auditable reasoning: every performance number traceable to equation + inputs + source.
- For patent work: prioritize enablement detail and clear distinction from prior art over speculative performance claims.

## Integration

- Pair with existing patent-specification, patent-evidence-package, and research-paper-writing skills for full pipeline.
- Use litreview / arxiv for prior-art and multiphase literature pulls.
- Cross-link to local offworld-fluid-dynamics knowledge and custom-gpu-dem results when available.

## Anti-Patterns

- Applying atmospheric fluidization correlations without Knudsen or gravity correction discussion.
- Ignoring radiation or electrostatics at lunar conditions.
- Over-claiming efficiency without uncertainty or regime justification.
- Treating marketing claims or unvalidated CFD as primary evidence.

Version: 1.0.0 (synthesized 2026-07-23 from mechanical-engineering-research patterns + RCFX/ISRU domain constraints)
