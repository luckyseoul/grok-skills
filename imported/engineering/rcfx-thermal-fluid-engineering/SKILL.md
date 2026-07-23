---
name: rcfx-thermal-fluid-engineering
description: >
  Domain-rigor judgment layer for multi-stage counter-current fluidized bed heat recovery systems under lunar ISRU constraints (low pressure ~0.14 bar, cohesive regolith Geldart C, iron shot dual thermal-mass/agitator function). Incorporates correlation validity ranges (Re, Ar, Umf, Nu), multiphase regime maps, pressure-drop/heat-transfer tradeoffs, uncertainty propagation, DEM mechanistic evidence anchors, trade studies, and invention-disclosure/patent-support packets. Triggers on RCFX, lunar fluidized bed, He-3 extraction thermal, regolith heat recovery, multiphase bed design, provisional patent thermal claims, calculation plans for bed hydrodynamics. Fuse of mechanical-engineering-research patterns with existing RCFX DEM/patent evidence.
---

# RCFX Thermal-Fluid Engineering

Domain judgment layer that enforces physical validity for multi-stage counter-flow fluidized bed systems designed for lunar regolith processing and heat recovery.

## Core Mechanisms

Particle-scale: contact mechanics, gas-solid drag (consistent formulation across DEM rungs), agitation by larger iron shot particles producing bed mobilization (observed 7.32× height increase at target conditions).

Bed-scale: minimum fluidization velocity Umf, bubbling-to-slugging transitions, voidage, particle-gas and wall heat transfer coefficients, pressure drop ΔP, radiative contributions under vacuum.

System-scale: 5-stage counter-current effectiveness (target 75.6% at ~68 W blower), material transfer between stages, low-envelope-pressure operation (0.14 bar), overall energy balance.

## Workflow

1. Clarify objective: geometry, particle size distribution (iron vs regolith), gas velocity, pressure, target metrics (effectiveness, power, mobilization factor).
2. Source hierarchy: validated DEM runs and lumped models > peer-reviewed multiphase correlations with stated limits > NASA/DOE ISRU reports > patents > textbooks. Flag any leap beyond validity ranges.
3. Extract governing relations with explicit applicability bounds (Re_p, Archimedes, Geldart group, Umf correlations such as Wen-Yu or Ergun-derived).
4. Map regimes and detect phase transitions (fixed → fluidized → bubbling → slug → transport).
5. Perform trade studies: particle diameter vs velocity vs ΔP vs heat transfer vs attrition risk; iron fill fraction sensitivity.
6. Propagate uncertainty: sensor, property variation, model form, Monte-Carlo on key parameters if data allow.
7. Output decision-ready package with assumptions, evidence anchors, gaps, next experimental or simulation steps.

## Thermal-Fluid Validity Gates

- Confirm correlation used only inside stated Re, Pr, geometry, roughness, phase-change limits.
- For CFD or DEM: mesh/resolution independence, wall treatment, convergence, consistent drag/contact models, validation against analytical or experimental anchors.
- Experimental or simulated plans must include calibration, heat-loss correction, flow-development length, repeatability, uncertainty budget.
- Low-pressure specific: mean free path effects, continuum breakdown, electrostatics, radiative dominance relative to conduction/convection.
- Cohesive fines: account for agglomeration, channeling; quantify iron agitation leverage on mobilization.

## Output Patterns

- Research brief: Question | Bottom line | Assumptions | Evidence (DEM rung, correlation, model) | Tradeoffs | Gaps | Next steps.
- Calculation plan: equations, dimensionless groups, property tables, sensitivity estimates, required validation data.
- Invention disclosure / patent support packet: technical description of mechanism, performance numbers with sources, alternative embodiments within claim scope, enablement notes.
- Manuscript methods/results: regime maps, effectiveness curves, pressure-power trade, uncertainty bars.
- Trade-study matrix: rows = design variables (iron size, velocity, stages, pressure); columns = metrics (effectiveness, power, mobilization, risk); cells = quantitative or directional effect with causal chain.

## Integration

- Pull numbers and DEM results exclusively from current RCFX evidence package or validated runs.
- Cross-reference patent-specification and patent-evidence-package skills for claim support and formal drawings.
- For cosmology or unrelated physics, defer to other skills.

## Strict Rules

Stay inside existing claim parameters and validated operating points. Never introduce unvalidated new matter. Mark all model extrapolations. Prefer first-principles or anchored correlations over pure black-box ML surrogates unless the surrogate has explicit validation against the DEM or analytical anchors.

Flag every assumption and evidence gap explicitly.
