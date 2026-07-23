#!/usr/bin/env python3
"""
patent_style.py
Reusable matplotlib setup for USPTO-compliant black & white patent drawings.
Produces clean vector output (SVG/PDF) with proper line weights, no color,
and publication-ready typography.

Usage:
    from patent_style import setup_patent_figure, save_patent_figure

    fig, ax = setup_patent_figure(figsize=(6.5, 4.0))  # width in inches
    # ... plot using only black, white, grayscale, and hatching ...
    save_patent_figure(fig, "/path/to/FIG_05_effectiveness.svg")
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

# USPTO-friendly defaults (37 CFR 1.84)
# - Black & white / line art only
# - Minimum line weight ~0.5 pt when reduced
# - Sans-serif font, readable at 2/3 reproduction size

def setup_patent_figure(figsize=(6.5, 4.5), dpi=300):
    """
    Create a figure pre-configured for patent drawing standards.
    figsize should be chosen so that when reduced to ~2/3 size in the printed
    patent it remains legible (typically 3.5–6.5 inches wide for single column).
    """
    plt.close('all')

    # Force vector-friendly settings
    mpl.rcParams['pdf.fonttype'] = 42      # TrueType fonts (editable in Illustrator/Inkscape)
    mpl.rcParams['ps.fonttype'] = 42
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans']
    mpl.rcParams['font.size'] = 9
    mpl.rcParams['axes.labelsize'] = 9
    mpl.rcParams['axes.titlesize'] = 10
    mpl.rcParams['xtick.labelsize'] = 8
    mpl.rcParams['ytick.labelsize'] = 8
    mpl.rcParams['legend.fontsize'] = 8

    # Line widths suitable for reduction
    mpl.rcParams['lines.linewidth'] = 1.0
    mpl.rcParams['axes.linewidth'] = 0.8
    mpl.rcParams['xtick.major.width'] = 0.7
    mpl.rcParams['ytick.major.width'] = 0.7

    # No color cycles — force everything toward black / hatching
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['black'])

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Clean spines
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(0.8)

    return fig, ax


def save_patent_figure(fig, filepath, formats=("svg", "pdf")):
    """
    Save the figure in the requested vector formats with tight bounding box.
    SVG is preferred for later editing (Inkscape, Illustrator).
    PDF is preferred for direct submission.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    base = path.with_suffix('')

    for fmt in formats:
        out_path = base.with_suffix(f".{fmt}")
        fig.savefig(
            out_path,
            format=fmt,
            bbox_inches='tight',
            pad_inches=0.05,
            facecolor='white',
            edgecolor='none'
        )
        print(f"Saved: {out_path}")

    return base


def add_figure_label(fig, label="FIG. 1", y=0.02):
    """
    Add a centered "FIG. 1" style label below the figure content.
    Call this after all plotting is finished.
    """
    fig.text(0.5, y, label, ha='center', va='bottom', fontsize=10, fontweight='bold')


# Example hatching patterns for different materials (regolith vs iron shot)
PATENT_HATCHES = {
    'regolith': '....',      # fine dots / stipple
    'iron': 'xxx',           # cross-hatch for larger particles
    'gas': '///',            # flow direction
    'solid': '///',
    'distributor': '---',
}


if __name__ == "__main__":
    # Self-test
    fig, ax = setup_patent_figure(figsize=(5, 3))
    ax.plot([0, 1, 2], [0, 1, 0], 'k-', linewidth=1.2)
    ax.set_xlabel("Envelope Pressure (bar)")
    ax.set_ylabel("Overall Effectiveness (%)")
    add_figure_label(fig, "FIG. 5")
    save_patent_figure(fig, "/tmp/patent_test")
    print("Self-test complete. Check /tmp/patent_test.svg and .pdf")
