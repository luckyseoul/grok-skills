#!/usr/bin/env python3
"""
render_dem_bed.py
Load a GPU DEM .npz checkpoint from the RCFX project and render a clean,
black & white side-view particle bed visualization suitable for patent drawings.

Distinguishes iron shot (larger) from regolith using size and hatching.
Produces output via the patent_style helpers.

Example:
    python render_dem_bed.py \
        /home/nick/rcfx/sims/custom_gpu_dem/rung2_checkpoints/with_iron_rung2_step25000.npz \
        --label "FIG. 3" \
        --title "Iron Shot Agitation at 0.14 bar (U_G = 0.066 m/s)" \
        --out /home/nick/rcfx/patent_drawings/FIG_03_iron_agitation
"""

import argparse
import numpy as np
import sys
from pathlib import Path

# Add the patent_style module
sys.path.insert(0, str(Path(__file__).parent))
from patent_style import setup_patent_figure, save_patent_figure, add_figure_label


def load_checkpoint(npz_path):
    d = np.load(npz_path, allow_pickle=True)
    pos = d['pos']
    radii = d['radii']
    # types: 0 = regolith, 1 = iron (common convention in the RCFX DEM runs)
    ptype = d.get('ptype', d.get('types', np.zeros(len(pos), dtype=int)))

    # Some older checkpoints used different key names
    if 'z' in d and 'x' in d:
        x = d['x']
        z = d['z']
    else:
        x = pos[:, 0]
        z = pos[:, 2] if pos.shape[1] > 2 else pos[:, 1]

    return x, z, radii, ptype


def render_bed(npz_path, out_base, fig_label="FIG. 3", title=None, max_points=8000):
    x, z, radii, ptype = load_checkpoint(npz_path)

    # Downsample for clean drawing if the run was very large
    if len(x) > max_points:
        idx = np.random.choice(len(x), max_points, replace=False)
        x, z, radii, ptype = x[idx], z[idx], radii[idx], ptype[idx]

    iron = ptype == 1
    rego = ~iron

    fig, ax = setup_patent_figure(figsize=(7.0, 4.2))

    # Regolith — small open circles with light stippling effect via small markers
    if np.any(rego):
        ax.scatter(
            x[rego], z[rego],
            s=(radii[rego] * 420)**2,   # scale for visibility while remaining line-art
            facecolors='white',
            edgecolors='black',
            linewidths=0.4,
            marker='o',
            label='Regolith fines'
        )

    # Iron shot — larger, cross-hatched appearance via marker + edge
    if np.any(iron):
        ax.scatter(
            x[iron], z[iron],
            s=(radii[iron] * 380)**2,
            facecolors='black',
            edgecolors='black',
            linewidths=0.6,
            marker='o',
            label='Iron shot (1.5–3.5 mm)'
        )

    ax.set_xlabel("Horizontal position (arb. units)")
    ax.set_ylabel("Bed height (mm scaled)")
    ax.set_aspect('equal', adjustable='box')
    ax.grid(False)

    if title:
        ax.set_title(title, pad=8)

    # Add a very light reference line at the distributor
    ymin = np.min(z) - np.max(radii) * 2
    ax.axhline(ymin, color='black', linewidth=1.5, linestyle='-')

    add_figure_label(fig, fig_label)

    out_path = save_patent_figure(fig, out_base, formats=("svg", "pdf"))
    print(f"Rendered clean patent-style bed view from {npz_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render RCFX GPU DEM bed as patent drawing")
    parser.add_argument("npz", help="Path to .npz checkpoint (e.g. with_iron_rung2_step25000.npz)")
    parser.add_argument("--out", required=True, help="Output base path (without extension)")
    parser.add_argument("--label", default="FIG. 3", help="Figure label, e.g. 'FIG. 3'")
    parser.add_argument("--title", default=None, help="Optional title above the figure")
    args = parser.parse_args()

    render_bed(args.npz, args.out, fig_label=args.label, title=args.title)
