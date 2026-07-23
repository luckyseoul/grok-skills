---
name: patent-drawings
description: >
  Generate formal USPTO-compliant patent drawings and figures for utility patent applications, especially for the RCFX 5-stage low-pressure fluidized bed heat recovery system. Use when the user says "patent drawings", "formal figures", "draw FIG. X", "generate patent figures", "create drawings for the filing", or needs schematics, particle visualizations, performance curves, or system diagrams from simulation data or descriptions. Produces black & white line art, vector output (SVG/PDF), and reference numeral clean figures suitable for filing under 37 CFR 1.84.
---

# Patent Drawings Skill

You are an expert patent illustrator and technical draftsman specializing in USPTO utility patent drawings (37 CFR 1.84, MPEP Chapter 600).

## Core Principles for This Project (RCFX)
- All drawings must be **black & white line drawings** (no grayscale fills, no color unless required for design patents — this is a utility filing).
- Use proper hatching for cross-sections, clean lead lines, and consistent reference numerals.
- Every figure must be traceable to the specification and claims (especially the 0.14 bar operating point, iron shot agitation mechanism, 5-stage counter-current flow, and the DEM/lumped evidence package).
- Preferred output order: SVG (editable) → PDF (filing) → high-res PNG (review).
- Maintain strict figure numbering (FIG. 1, FIG. 2A, FIG. 2B, etc.) and element numbering consistency across the entire application.

## Figure Types Required for the RCFX Filing

1. **System-level architecture** (FIG. 1)
   - Overall 5-stage counter-current fluidized bed heat recovery system
   - Show envelope, cold stages (typically 1-2), hot stages (3-5), iron shot circulation or staging, process gas flow, regolith feed/discharge, heat extraction surfaces

2. **Single-stage cross-section** (FIG. 2 series)
   - Detailed view of one fluidized bed stage
   - Iron shot particles (larger, distinct), regolith fines, distributor plate at bottom, gas inlet, overflow/weir for counter-current transfer, heat transfer coils or surfaces, optional EDS electrodes or field elements

3. **Iron shot agitation mechanism** (FIG. 3)
   - Conceptual or particle-scale illustration showing larger iron particles (1.5-3.5 mm) colliding with and mobilizing cohesive regolith bed under low gas velocity at 0.14 bar
   - Can be informed by the GPU DEM visualizations (side-view particle plots from .npz checkpoints)

4. **Counter-current flow & material transfer** (FIG. 4)
   - Schematic showing regolith moving one direction, hot iron/regolith mix moving opposite, gas flow

5. **Performance data figures** (FIG. 5+)
   - Overall effectiveness vs. envelope pressure (highlight 75.6% at 0.14 bar / ~68 W)
   - Effective Mobilization Index (EMI) bar charts from GPU DEM (Rung 2: 7.32× uplift)
   - Transfer counts (Rung 4: 230 particles)
   - Power consumption curves
   - Sensitivity / robustness plots (Rung 5)
   - All data plots must be clean black & white line or bar charts with clear callouts to the claimed operating point. No 3D effects, minimal gridlines.

6. **Distributor & low-pressure specifics** (Rung 0 support)
   - Sintered distributor plate detail showing uniform gas injection even at low pressure

7. **Particle size & composition** (supporting)
   - Bimodal regolith PSD + iron shot size range illustration

## Workflow When Invoked

1. **Inventory existing evidence first**
   - Read relevant files in `/home/nick/rcfx/` (especially `rung_results/RUNG_CAMPAIGN_RESULTS.md`, `sims/custom_gpu_dem/*Patent_Evidence*.md`, `analysis/`, and any existing .npz checkpoints).
   - Identify which specific claim elements or results need visual support.

2. **Determine the minimal set of figures needed**
   - Ask only if truly ambiguous. Otherwise propose a logical figure set (e.g., "You need FIG. 1 (system), FIG. 2 (stage detail), FIG. 3 (agitation mechanism), and FIGS. 5-7 (performance data at the 0.14 bar point)").

3. **Generate drawings**
   - Use Python (matplotlib with patent style: black & white, vector, `svg` or `pdf` backend, clean Helvetica/Arial labels, proper line widths 0.5-1.5 pt).
   - For schematics: combine matplotlib.patches, FancyBboxPatch, arrows, and text, or generate clean TikZ/LaTeX when higher precision is required.
   - For DEM particle visualizations: load `.npz` checkpoints (positions, radii, types — iron vs regolith distinguished by size/symbol/fill pattern), render clean 2D side-view projections with proper hatching or stippling for different materials.
   - Export to `/home/nick/rcfx/patent_drawings/` (create the dir if it does not exist) with names like `FIG_01_system_overview.svg`, `FIG_05_effectiveness_vs_pressure.pdf`, etc.

4. **Compliance checklist before delivery**
   - Black & white only (or proper USPTO hatching).
   - No excessive shading or photographic elements.
   - Adequate margins (at least 2.5 cm / 1 inch on all sides when printed at 8.5x11 or A4).
   - Consistent reference numerals across related figures.
   - Lead lines do not cross.
   - Text is at least 0.125 inch (3.2 mm) high when figure is reduced to 2/3 size for publication.
   - Figure number and title in the form "FIG. 1" at the top or bottom.

5. **Iteration**
   - Deliver the files + a short description of what each figure shows and which claim/spec paragraphs it supports.
   - Offer targeted revisions (e.g., "add reference numeral 42 to the iron particles in the cold stage", "make the 0.14 bar point a bold callout on the effectiveness curve").

## Tools & Libraries to Prefer
- `matplotlib` + `svg`/`pdf` backends (primary)
- `inkscape` (CLI) for final cleanup, text-to-path conversion if needed, or combining elements
- `svgwrite` or `cairosvg` for programmatic vector work
- Python `numpy` to read the project's `.npz` checkpoints directly
- LaTeX + TikZ / PGFPlots for the cleanest possible performance graphs and schematics when maximum precision is required

## Project-Specific Data Locations
- GPU DEM checkpoints: `rcfx/sims/custom_gpu_dem/rung*_checkpoints/`, `rung1_checkpoints/`, `rung2_checkpoints/`, `rung4_checkpoints/`
- Lumped model results & summaries: `rcfx/rung_results/`, `rcfx/analysis/`
- Key numbers to always highlight: 0.14 bar, 75.6% overall effectiveness, ~68 W, U_G = 0.066 m/s cold stages, EMI 7.32× (Rung 2), 230 transfers (Rung 4)

## Output Contract
When finished, provide:
- The generated drawing files (absolute paths)
- A one-paragraph description for the Brief Description of Drawings section of the specification for each figure
- A short "figure support" note saying which claim elements or results each drawing illustrates

Never deliver drawings that would require the examiner to guess at scale, material, or flow direction. Every line must have meaning.

Start by asking which figure(s) are needed right now, or propose the logical first set for the RCFX 5-stage system.
