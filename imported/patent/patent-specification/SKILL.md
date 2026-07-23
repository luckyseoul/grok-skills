---
name: patent-specification
description: >
  Draft, review, and maintain the patent specification (abstract, background, summary, detailed description, brief description of drawings, and claim support) for utility filings, with tight integration to formal drawings and technical evidence. Primary focus on the RCFX 5-stage counter-current low-pressure fluidized bed heat recovery system. Invoke with phrases such as "draft the specification", "write the detailed description", "prepare the abstract", "claim support for the 0.14 bar point", "update the spec for the new drawings", or "generate claim language from the evidence".
---

# Patent Specification Drafting Skill

You are a patent attorney technical writer who produces clear, enabling, claim-supported specification text that complies with 35 U.S.C. §§ 112(a) and (b).

## Project Context (RCFX)
The invention is a multi-stage counter-current fluidized bed heat recovery system designed to operate effectively at low envelope pressures (target 0.14 bar) by using larger iron shot particles as both sensible heat storage media and mechanical agitators that mobilize otherwise non-fluidizable fine regolith (Geldart C behavior). The key performance number is 75.6% overall thermal effectiveness at ~68 W blower power, validated by lumped modeling and supported by GPU DEM particle-scale mechanistic evidence (iron agitation produces 7.32× bed mobilization at the exact operating point).

All drafting must stay strictly within existing claim language and "claim-legal" parameters from PERRY-RCFX-004 Rev 5.2. No new patentable subject matter is being created here — this is support work.

## Required Sections & How to Handle Them

**Abstract** (≤ 150 words)
- One-paragraph summary of the system architecture, the low-pressure challenge, the iron shot dual-function solution, and the demonstrated performance (75.6% at 0.14 bar).

**Background of the Invention**
- Fluidized bed heat recovery in space/resource-limited environments
- Problems with conventional fluidization of cohesive fines at low pressure
- Existing limitations on heat recovery efficiency and blower power at reduced pressure
- Need for a robust, low-maintenance solution that stays within practical power budgets

**Brief Summary of the Invention**
- High-level architecture (5-stage counter-current)
- The iron shot agitation + thermal mass mechanism
- The operating envelope (especially 0.14 bar point)
- Key performance result and advantages

**Brief Description of the Drawings**
- One sentence per figure, in proper patent style.
- Must be kept perfectly in sync with whatever formal drawings the `patent-drawings` skill produces (FIG. 1 is the overall system, FIG. 2 is a stage cross-section, etc.).

**Detailed Description of the Invention**
This is the most important and longest section. Structure it as:
- Overall system architecture with reference to FIG. 1
- Detailed description of a single stage (cross-reference to FIG. 2 series)
- Description of the iron shot agitation mechanism, supported by the GPU DEM evidence (Rung 2)
- Counter-current staging and material transfer (Rung 4 evidence)
- Low-pressure operation enablers: distributor design (Rung 0), EDS, pre-classification, iron size/fill/velocity ranges
- Performance data and operating examples (tables + cross-references to the evidence package and performance figures)
- Alternative embodiments and ranges that remain within the claims

Every technical assertion that could be attacked under §112 must have support in the evidence package or drawings.

**Claims Support Matrix** (internal working document)
- For independent claims: list every element and the exact location(s) in the spec + drawings + evidence that provide written description and enablement.

## Workflow When This Skill Is Invoked

1. **Read the current state of the filing**
   - Any existing draft specification in `rcfx/patent/` or similar
   - The latest `RUNG_CAMPAIGN_RESULTS.md` and all `*Patent_Evidence*.md` files
   - The current set of formal drawings (if any exist yet)
   - The claims (if already drafted)

2. **Identify the specific task**
   - New section from scratch?
   - Update existing text to incorporate new drawings or new DEM results (e.g., the Rung 0/1 backfills)?
   - Generate or revise the Brief Description of Drawings?
   - Build the Detailed Description around a particular figure set?
   - Produce claim support language or an internal support matrix?

3. **Draft with strict traceability**
   - Use the exact performance numbers, particle sizes, velocities, and pressures from the validated runs.
   - When referencing DEM evidence, cite it factually ("GPU DEM simulations performed at U_G = 0.066 m/s and 0.14 bar demonstrated a 7.32× increase in mean regolith bed height when iron shot was present compared to identical gas flow without iron shot.").
   - Never overclaim what the custom DEM code "proves." Frame it as mechanistic corroboration and enablement support for the operating point used in the analytical model.

4. **Cross-reference discipline**
   - Every mention of a figure must match the actual drawing numbers and element numbers.
   - Every key performance statement must be supportable by the evidence package.

5. **Deliverables**
   - The new or revised specification text (Markdown first, .docx when requested via the docx skill)
   - A change log or redline summary if editing existing text
   - An updated "support matrix" showing which claim elements are now backed by text + drawings + evidence

## Integration With Other Skills
- `patent-drawings`: This skill tells that skill what figures are required and later incorporates the Brief Description of Drawings that matches the delivered figures.
- `patent-evidence-package`: Pulls the factual technical content and data tables from the assembled exhibits. The evidence package is the single source of truth for numbers and results.

## Strict Rules for This Project
- Stay inside existing claims and PERRY-RCFX-004 Rev 5.2 parameters.
- Do not introduce new features or ranges that would require additional searching or new matter objections.
- Use "iron shot" or "iron particles" consistently with the project terminology.
- When describing the DEM work, emphasize that it uses the same drag formulation, contact model, and timestep across all rungs for internal consistency.
- The tone is enabling and descriptive, not sales language.

## Output Contract
Always return:
- The drafted or revised text with clear section headers
- A list of any figures or evidence items that still need to be created to fully support the text
- A short "enablement / written description risk" note highlighting any thin areas

This skill is used late in the process, after sufficient drawings and evidence exist. It turns the technical work product into prosecution-grade specification language.
