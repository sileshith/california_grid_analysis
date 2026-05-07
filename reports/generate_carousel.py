#!/usr/bin/env python3
"""
California Grid Stress Monitoring Dashboard
LinkedIn Carousel PDF Generator - 9 Slides

  01 - Cover
  02 - Business Question
  03 - Data Scope Validation
  04 - Analytical Workflow  (PREPARE / ENGINEER / DELIVER)
  05 - Grid Stress Index Logic  (compact professional table)
  06 - Dashboard Overview I  (Exec Overview + High-Priority Review Queue)
  07 - Dashboard Overview II (Authority Comparison + full-suite interpretation)
  08 - Main Findings
  09 - Skills and Responsible Interpretation

Output: reports/california_grid_stress_monitoring_linkedin_carousel.pdf
"""

import os, warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.lines as mlines

# -- Paths --------------------------------------------------------------------
BASE   = '/Users/sileshihirpa/Desktop/ASU/projects/california-grid-analysis'
RPTS   = os.path.join(BASE, 'reports')
SHOTS  = os.path.join(BASE, 'outputs', 'dashboard_screenshots')

PDF_OUT  = os.path.join(RPTS, 'california_grid_stress_monitoring_linkedin_carousel.pdf')
EXEC_IMG = os.path.join(SHOTS, 'executive_overview.png')
HIPR_IMG = os.path.join(SHOTS, 'high_priority_review_queue.png')
AUTH_IMG = os.path.join(SHOTS, 'authority_comparison.png')

# -- Design system ------------------------------------------------------------
W, H = 10, 10
DPI  = 150
TOTAL = 9

NAVY    = '#1B2A4A'
ORANGE  = '#E07020'
WHITE   = '#FFFFFF'
LGRAY   = '#F5F7FA'
MGRAY   = '#D8E2EE'
DARK    = '#1A202C'
MUTED   = '#718096'
HIGH_C  = '#BE3A20'
MED_C   = '#C08010'
LOW_C   = '#1A6EA8'
CARD_BG = '#EBF0F6'
DISC_BG = '#FFF4EC'
DISC_BD = '#F4C490'
GREEN   = '#276221'
RED_BG  = '#FDECEA'
GRN_BG  = '#EBF5EB'

FS_H1   = 24
FS_H2   = 18
FS_H3   = 14
FS_BODY = 12
FS_SM   = 10
FS_XS   = 9
FS_KPI  = 26

# -- Base constructors --------------------------------------------------------
def white_slide():
    fig = plt.figure(figsize=(W, H), facecolor=WHITE)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_axis_off()
    return fig, ax

def dark_slide():
    fig = plt.figure(figsize=(W, H), facecolor=NAVY)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_axis_off()
    return fig, ax

# -- Drawing helpers ----------------------------------------------------------
def box(ax, x, y, w, h, fc, ec='none', lw=0, alpha=1.0, zorder=1, radius=0):
    if radius > 0:
        p = mpatches.FancyBboxPatch(
            (x, y), w, h, boxstyle=f'round,pad={radius}',
            facecolor=fc, edgecolor=ec, linewidth=lw,
            alpha=alpha, zorder=zorder)
    else:
        p = mpatches.Rectangle(
            (x, y), w, h, facecolor=fc, edgecolor=ec,
            linewidth=lw, alpha=alpha, zorder=zorder)
    ax.add_patch(p)

def t(ax, x, y, s, fs=12, c=DARK, w='normal', ha='left', va='center',
      zorder=5, ls=1.35, style='normal', alpha=1.0):
    ax.text(x, y, s, fontsize=fs, color=c, fontweight=w,
            ha=ha, va=va, fontstyle=style, zorder=zorder,
            linespacing=ls, alpha=alpha, multialignment=ha)

def hline(ax, x0, x1, y, color=MGRAY, lw=1.0, zorder=3):
    ax.plot([x0, x1], [y, y], color=color, linewidth=lw, zorder=zorder)

def orange_bar(ax):
    box(ax, 0, 9.76, 10, 0.24, ORANGE, zorder=4)

def section_tag(ax, label):
    t(ax, 0.55, 9.55, label, fs=FS_XS, c=ORANGE, w='bold', ha='left', zorder=5)

def slide_num(ax, n):
    t(ax, 9.55, 0.3, f'{n} / {TOTAL}', fs=FS_XS, c=MUTED, ha='right', zorder=6)

def img_panel(fig, x, y, w, h, img_path):
    """Add screenshot image. x,y,w,h in 0-10 coords."""
    ax_i = fig.add_axes([x/10, y/10, w/10, h/10])
    ax_i.set_axis_off()
    if os.path.exists(img_path):
        im = plt.imread(img_path)
        ax_i.imshow(im, aspect='auto')
        for spine in ax_i.spines.values():
            spine.set_visible(True)
            spine.set_color(MGRAY)
            spine.set_linewidth(1.2)
    else:
        ax_i.set_facecolor('#EEEEEE')
        ax_i.text(0.5, 0.5, '[not found]', ha='center', va='center',
                  fontsize=8, color='#999999', transform=ax_i.transAxes)

# =============================================================================
# SLIDE 1 - COVER
# =============================================================================
def slide_01():
    fig, ax = dark_slide()

    box(ax, 0, 0, 0.4, 10, ORANGE, zorder=2)
    box(ax, 0.4, 0, 9.6, 10, NAVY, zorder=3)

    t(ax, 5.2, 6.4,
      'California Grid Stress\nMonitoring Dashboard',
      fs=30, c=WHITE, w='bold', ha='center', va='center', ls=1.25, zorder=5)

    t(ax, 5.2, 5.1,
      'Public EIA-930 grid operations analysis\nacross five California balancing authorities',
      fs=14, c='#A8BDD4', ha='center', va='center', ls=1.45, zorder=5)

    hline(ax, 1.4, 9.0, 4.35, color='#2E4F78', lw=1.5)

    t(ax, 5.2, 3.75, 'Sileshi Hirpa',
      fs=18, c=WHITE, w='bold', ha='center', va='center', zorder=5)

    t(ax, 5.2, 3.1,
      'Data Science  |  Business Analytics  |  Python  |  Tableau',
      fs=11, c='#8AACC8', ha='center', va='center', zorder=5)

    t(ax, 9.55, 0.3, f'1 / {TOTAL}', fs=FS_XS, c='#4A6080', ha='right', zorder=6)

    return fig

# =============================================================================
# SLIDE 2 - BUSINESS QUESTION
# =============================================================================
def slide_02():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '02 / BUSINESS QUESTION')
    slide_num(ax, 2)

    t(ax, 0.55, 8.65,
      'What problem does this project address?',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', ls=1.2, zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    body = (
        "California's electricity grid is managed by five balancing\n"
        "authorities that must match supply and demand in real time.\n\n"
        "Analytical question:\n\n"
        "How can public hourly EIA-930 data be prepared, validated,\n"
        "and visualized so a reviewer can quickly identify periods\n"
        "that may deserve additional attention?"
    )
    t(ax, 0.55, 6.65, body, fs=FS_BODY + 1, c=DARK, ha='left',
      va='center', ls=1.5, zorder=5)

    t(ax, 5.0, 2.95,
      'California Balancing Authorities in Scope',
      fs=FS_SM, c=MUTED, w='bold', ha='center', va='center', zorder=5)

    ba_data = [
        ('BANC', 'Northern California'),
        ('CISO', 'California ISO'),
        ('IID',  'Imperial Irrigation'),
        ('LDWP', 'Los Angeles DWP'),
        ('TIDC', 'Turlock Irrigation'),
    ]
    pill_w = 1.6
    pill_h = 0.52
    total_w = len(ba_data) * pill_w + (len(ba_data) - 1) * 0.22
    x0 = (10 - total_w) / 2

    for i, (code, desc) in enumerate(ba_data):
        px = x0 + i * (pill_w + 0.22)
        py = 1.75
        box(ax, px, py, pill_w, pill_h, NAVY, zorder=3, radius=0.1)
        t(ax, px + pill_w / 2, py + pill_h * 0.62, code,
          fs=FS_SM, c=WHITE, w='bold', ha='center', va='center', zorder=5)
        t(ax, px + pill_w / 2, py + pill_h * 0.22, desc,
          fs=7, c='#A8BDD4', ha='center', va='center', zorder=5)

    return fig

# =============================================================================
# SLIDE 3 - SCOPE VALIDATION  (funnel graphic)
# =============================================================================
def slide_03():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '03 / DATA SCOPE VALIDATION')
    slide_num(ax, 3)

    box(ax, 0.55, 7.4, 0.13, 1.7, ORANGE, zorder=3)
    t(ax, 0.9, 8.35,
      '"A chart can run without error\nand still answer the wrong question."',
      fs=FS_H2, c=NAVY, w='bold', ha='left', va='center', ls=1.3,
      style='italic', zorder=5)

    hline(ax, 0.55, 9.5, 7.1, color=MGRAY, lw=1.2)

    t(ax, 0.55, 6.7,
      'The raw EIA-930 file contains balancing authorities from across the United States.\n'
      'An initial visualization ran without error but produced a misleading result\n'
      'because non-California records were included. Scope was validated before analysis.',
      fs=FS_BODY, c=DARK, ha='left', va='center', ls=1.5, zorder=5)

    funnel_cx = 5.0
    top_hw    = 3.6
    bot_hw    = 1.6
    top_y     = 5.8
    bot_y     = 1.4

    funnel_pts = [
        (funnel_cx - top_hw, top_y),
        (funnel_cx + top_hw, top_y),
        (funnel_cx + bot_hw, bot_y),
        (funnel_cx - bot_hw, bot_y),
    ]
    poly = mpatches.Polygon(funnel_pts, closed=True,
                            facecolor=CARD_BG, edgecolor=MGRAY,
                            linewidth=1.2, zorder=2)
    ax.add_patch(poly)

    top_band = mpatches.Polygon([
        (funnel_cx - top_hw, top_y),
        (funnel_cx + top_hw, top_y),
        (funnel_cx + top_hw, top_y - 0.55),
        (funnel_cx - top_hw, top_y - 0.55),
    ], closed=True, facecolor='#F8D7DA', edgecolor='none', zorder=3)
    ax.add_patch(top_band)

    t(ax, funnel_cx, top_y - 0.27,
      'Raw EIA-930 File  -  All U.S. Balancing Authorities',
      fs=FS_SM, c=HIGH_C, w='bold', ha='center', va='center', zorder=5)

    t(ax, funnel_cx, (top_y + bot_y) / 2,
      'Scope validation: filter to California only',
      fs=FS_XS, c=MUTED, ha='center', va='center', style='italic', zorder=5)

    bot_band = mpatches.Polygon([
        (funnel_cx - bot_hw, bot_y + 0.55),
        (funnel_cx + bot_hw, bot_y + 0.55),
        (funnel_cx + bot_hw, bot_y),
        (funnel_cx - bot_hw, bot_y),
    ], closed=True, facecolor='#D4EDDA', edgecolor='none', zorder=3)
    ax.add_patch(bot_band)

    t(ax, funnel_cx, bot_y + 0.28,
      'California Only  -  13,020 records  -  5 BA codes',
      fs=FS_SM, c=GREEN, w='bold', ha='center', va='center', zorder=5)

    return fig

# =============================================================================
# SLIDE 4 - ANALYTICAL WORKFLOW  (PREPARE / ENGINEER / DELIVER)
# =============================================================================
def slide_04():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '04 / ANALYTICAL WORKFLOW')
    slide_num(ax, 4)

    t(ax, 0.55, 8.65, 'From raw CSV to published dashboard',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    groups = [
        ('PREPARE', CARD_BG, NAVY, [
            'Load and inspect EIA-930 CSV',
            'Standardize column names',
            'Validate California scope',
            'Filter: 5 California BAs',
            'Convert UTC to Pacific Time',
        ]),
        ('ENGINEER', '#EEF4ED', GREEN, [
            'Compute forecast error',
            'Calculate generation gap',
            'Derive import pressure',
            'Build Grid Stress Index',
            'Classify review priority tiers',
        ]),
        ('DELIVER', '#FFF4EC', ORANGE, [
            'Export 4 dashboard CSV files',
            'Build 3-tab Tableau workbook',
            'Publish to Tableau Public',
            'Document pipeline and limits',
            'Commit to GitHub',
        ]),
    ]

    card_w   = 2.72
    card_h   = 5.85
    gap      = 0.35
    y_base   = 1.55
    header_h = 0.52

    def draw_arrow(ax, x_center, y_mid):
        ax.annotate('', xy=(x_center + 0.17, y_mid),
                    xytext=(x_center - 0.17, y_mid),
                    arrowprops=dict(arrowstyle='->', color=MGRAY, lw=2.0), zorder=6)

    for i, (phase, bg, hdr_c, steps) in enumerate(groups):
        x = 0.55 + i * (card_w + gap)

        box(ax, x, y_base, card_w, card_h, bg, zorder=3, radius=0.09)
        box(ax, x, y_base + card_h - header_h, card_w, header_h,
            hdr_c, zorder=4, radius=0.09)
        t(ax, x + card_w / 2, y_base + card_h - header_h / 2,
          phase, fs=FS_SM + 1, c=WHITE, w='bold',
          ha='center', va='center', zorder=5)

        step_y = y_base + card_h - header_h - 0.42
        for step in steps:
            t(ax, x + 0.25, step_y, u'•',
              fs=FS_BODY, c=hdr_c, ha='left', va='center', zorder=5)
            t(ax, x + 0.50, step_y, step,
              fs=FS_XS, c=DARK, ha='left', va='center', ls=1.3, zorder=5)
            step_y -= 0.92

        if i < len(groups) - 1:
            arrow_x = x + card_w + gap / 2
            draw_arrow(ax, arrow_x, y_base + card_h / 2)

    return fig

# =============================================================================
# SLIDE 5 - GRID STRESS INDEX LOGIC  (compact professional table)
# =============================================================================
def slide_05():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '05 / GRID STRESS INDEX LOGIC')
    slide_num(ax, 5)

    t(ax, 0.55, 8.65, 'How the Grid Stress Index works',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    # Formula box
    box(ax, 0.55, 7.25, 8.9, 0.82, CARD_BG, zorder=3, radius=0.1)
    box(ax, 0.55, 7.25, 0.15, 0.82, ORANGE, zorder=4)
    t(ax, 5.0, 7.66,
      'Stress Index  =  ( Demand MW  /  Peak Demand MW )  x  100',
      fs=FS_H3 + 1, c=NAVY, w='bold', ha='center', va='center', zorder=5)

    # One-line normalization note
    t(ax, 0.55, 6.90,
      'Normalized per authority against its own peak - enables fair comparison across scales.',
      fs=FS_BODY, c=MUTED, ha='left', va='center', zorder=5)

    hline(ax, 0.55, 9.45, 6.60, color=MGRAY, lw=1.0)

    # Bar-pair visual
    t(ax, 0.55, 6.32, 'Why relative normalization matters:',
      fs=FS_SM, c=NAVY, w='bold', ha='left', va='center', zorder=5)

    t(ax, 0.75, 5.97, 'CISO', fs=FS_XS, c=DARK, w='bold',
      ha='left', va='center', zorder=5)
    box(ax, 1.45, 5.79, 6.40, 0.30, LOW_C, zorder=3, radius=0.03)
    t(ax, 8.0, 5.94, '32,000 MW', fs=FS_XS, c=MUTED,
      ha='left', va='center', zorder=5)

    t(ax, 0.75, 5.44, 'TIDC', fs=FS_XS, c=DARK, w='bold',
      ha='left', va='center', zorder=5)
    box(ax, 1.45, 5.26, 0.38, 0.30, LOW_C, zorder=3, radius=0.03)
    t(ax, 2.0, 5.41, '1,900 MW', fs=FS_XS, c=MUTED,
      ha='left', va='center', zorder=5)

    t(ax, 0.55, 4.94,
      'Both can reach Stress Index 90+ relative to their own peaks.',
      fs=FS_XS, c=MUTED, ha='left', va='center', style='italic', zorder=5)

    hline(ax, 0.55, 9.45, 4.64, color=MGRAY, lw=1.0)

    # ── Review Priority Tiers table ──────────────────────────────────────────
    # Layout constants
    TBL_L    = 0.55    # left edge
    TBL_R    = 9.00    # right edge (hours right-aligned here)
    COL_BAR  = TBL_L   # color swatch x
    BAR_W    = 0.12
    COL_TIER = 0.83    # tier label x
    COL_RULE = 2.65    # rule x
    ROW_H    = 0.50    # row height

    t(ax, TBL_L, 4.37, 'Review Priority Tiers',
      fs=FS_SM, c=NAVY, w='bold', ha='left', va='center', zorder=5)

    # Column headers
    hline(ax, TBL_L, TBL_R, 4.10, color=MGRAY, lw=0.8)
    t(ax, COL_TIER, 3.96, 'TIER',
      fs=7, c=MUTED, w='bold', ha='left', va='center', zorder=5)
    t(ax, COL_RULE, 3.96, 'THRESHOLD',
      fs=7, c=MUTED, w='bold', ha='left', va='center', zorder=5)
    t(ax, TBL_R, 3.96, 'HOURS',
      fs=7, c=MUTED, w='bold', ha='right', va='center', zorder=5)
    hline(ax, TBL_L, TBL_R, 3.78, color=MGRAY, lw=1.2)

    tiers = [
        (HIGH_C, 'High',   'Stress Index >= 90',       '75'),
        (MED_C,  'Medium', '75 <= Stress Index < 90',  '762'),
        (LOW_C,  'Low',    'Stress Index < 75',         '12,183'),
    ]
    row_tops = [3.78, 3.28, 2.78]

    for (fc, label, rule, hours), row_top in zip(tiers, row_tops):
        cy = row_top - ROW_H / 2
        # Color swatch
        box(ax, COL_BAR, row_top - ROW_H, BAR_W, ROW_H, fc, zorder=3)
        # Tier label
        t(ax, COL_TIER, cy, label,
          fs=FS_SM, c=fc, w='bold', ha='left', va='center', zorder=5)
        # Rule
        t(ax, COL_RULE, cy, rule,
          fs=FS_SM, c=DARK, ha='left', va='center', zorder=5)
        # Hours
        t(ax, TBL_R, cy, f'{hours} hrs',
          fs=FS_SM, c=MUTED, ha='right', va='center', zorder=5)
        # Row separator
        hline(ax, TBL_L, TBL_R, row_top - ROW_H, color=MGRAY, lw=0.6)

    # Dataset caveat
    t(ax, 5.0, 1.65,
      'Note: peak denominator is based on the January-April 2026 dataset window,\n'
      'not a multi-year historical record.',
      fs=FS_XS - 1, c=MUTED, ha='center', va='center', ls=1.4,
      style='italic', zorder=5)

    return fig

# =============================================================================
# SLIDE 6 - DASHBOARD OVERVIEW I  (Exec Overview + High-Priority)
# =============================================================================
def slide_06():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '06 / DASHBOARD OVERVIEW I')
    slide_num(ax, 6)

    t(ax, 0.55, 8.65, 'Published on Tableau Public',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    panel_w = 4.20
    gap     = 0.55
    img_h   = 4.00
    img_y   = 3.65     # bottom of image
    label_y = 7.92
    uline_y = 7.70

    panels = [
        (EXEC_IMG,
         'Executive Overview',
         'KPI summary cards, priority tier composition, and\n'
         'Stress Index trend over the full Jan-Apr 2026 window.\n'
         'Designed for reviewers who need to orient quickly\n'
         'across all five balancing authorities.'),
        (HIPR_IMG,
         'High-Priority Review Queue',
         'The 75 High Review Priority hours ranked by Stress Index,\n'
         'with peak demand, forecast error, and authority code.\n'
         'Structured for record-by-record operational review\n'
         'and drill-down into flagged windows.'),
    ]

    for i, (img_path, label, desc) in enumerate(panels):
        x  = 0.55 + i * (panel_w + gap)
        cx = x + panel_w / 2

        t(ax, cx, label_y, label,
          fs=FS_SM, c=NAVY, w='bold', ha='center', va='center', zorder=5)
        hline(ax, x, x + panel_w, uline_y, color=ORANGE, lw=2.0)
        img_panel(fig, x, img_y, panel_w, img_h, img_path)

        # Interpretation text below image
        t(ax, cx, img_y - 0.32, desc,
          fs=FS_XS, c=MUTED, ha='center', va='top', ls=1.45, zorder=5)

    return fig

# =============================================================================
# SLIDE 7 - DASHBOARD OVERVIEW II  (Authority Comparison + big picture)
# =============================================================================
def slide_07():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '07 / DASHBOARD OVERVIEW II')
    slide_num(ax, 7)

    t(ax, 0.55, 8.65, 'Authority Comparison and full-suite interpretation',
      fs=FS_H1 - 2, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    # Wide single thumbnail
    img_x  = 0.75
    img_w  = 8.50
    img_h  = 3.55
    img_y  = 4.45   # bottom of image -> top at 8.00

    t(ax, 5.0, 8.00 + 0.20, 'Authority Comparison',
      fs=FS_SM, c=NAVY, w='bold', ha='center', va='center', zorder=5)
    hline(ax, img_x, img_x + img_w, 8.02, color=ORANGE, lw=2.0)
    img_panel(fig, img_x, img_y, img_w, img_h, AUTH_IMG)

    # Tab interpretation (1 line below image)
    t(ax, 5.0, 4.14,
      'Places BANC, CISO, IID, LDWP, and TIDC side by side across Stress Index, '
      'forecast error, demand vs. net generation, and total interchange.',
      fs=FS_SM, c=DARK, ha='center', va='center', ls=1.4, zorder=5)

    # Big-picture interpretation card
    card_y = 0.60
    card_h = 3.15
    box(ax, 0.55, card_y, 8.90, card_h, CARD_BG, zorder=3, radius=0.09)
    box(ax, 0.55, card_y + card_h - 0.40, 8.90, 0.40, NAVY, zorder=4, radius=0.09)
    t(ax, 5.0, card_y + card_h - 0.20,
      'Full Dashboard Suite - Big Picture',
      fs=FS_SM, c=WHITE, w='bold', ha='center', va='center', zorder=5)

    big_pic = (
        'Together, the three tabs move a reviewer from grid-wide summary\n'
        'to specific high-priority hours to cross-authority pattern recognition.\n\n'
        'One analytical question answered at three levels of resolution:\n'
        'overview, flagged events, and authority-by-authority comparison.'
    )
    t(ax, 5.0, card_y + (card_h - 0.40) / 2, big_pic,
      fs=FS_SM, c=DARK, ha='center', va='center', ls=1.55, zorder=5)

    return fig

# =============================================================================
# SLIDE 8 - MAIN FINDINGS
# =============================================================================
def slide_08():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '08 / MAIN FINDINGS')
    slide_num(ax, 8)

    t(ax, 0.55, 8.65, 'What the data showed',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    kpis = [
        ('13,020',    'Total Scored Hours',                      NAVY),
        ('75',        'High Review Priority Hours',              HIGH_C),
        ('48.62',     'Average Stress Index',                    NAVY),
        ('35,596 MW', 'Peak Demand\n(CISO)',                     NAVY),
        ('100.0',     'Peak Stress Index',                       ORANGE),
        ('9,555 MW',  'Largest Forecast Error\n(High Priority)', NAVY),
    ]

    card_w  = 3.8
    card_h  = 2.25
    col_gap = 0.32
    x_L = 0.55
    x_R = 0.55 + card_w + col_gap
    y_rows = [5.65, 3.08, 0.51]

    for idx, (val, label, color) in enumerate(kpis):
        row = idx % 3
        col = idx // 3
        x   = x_L if col == 0 else x_R
        y   = y_rows[row]

        box(ax, x, y, card_w, card_h, CARD_BG, zorder=3, radius=0.09)
        box(ax, x, y + card_h - 0.07, card_w, 0.07, color, zorder=4)

        t(ax, x + card_w / 2, y + card_h * 0.57, val,
          fs=FS_KPI, c=color, w='bold', ha='center', va='center', zorder=5)
        t(ax, x + card_w / 2, y + card_h * 0.20, label,
          fs=FS_SM, c=MUTED, ha='center', va='center', ls=1.3, zorder=5)

    return fig

# =============================================================================
# SLIDE 9 - SKILLS AND RESPONSIBLE INTERPRETATION
# =============================================================================
def slide_09():
    fig, ax = white_slide()
    orange_bar(ax)
    section_tag(ax, '09 / SKILLS AND RESPONSIBLE INTERPRETATION')
    slide_num(ax, 9)

    t(ax, 0.55, 8.65, 'What this project demonstrates',
      fs=FS_H1, c=NAVY, w='bold', ha='left', va='center', zorder=5)
    hline(ax, 0.55, 9.5, 8.2, color=MGRAY, lw=1.5)

    # 2-column skill list
    skills_left = [
        'Python - pandas, Plotly, matplotlib',
        'Feature engineering - custom metric design',
        'Time-series analysis across multiple authorities',
        'Dashboard data modeling - layered CSV exports',
    ]
    skills_right = [
        'Tableau Public - 3-tab interactive dashboard',
        'Scope validation and analytical communication',
        'GitHub documentation and reproducible pipelines',
        'Responsible interpretation of public data',
    ]

    y_s = 7.75
    for i, (sl, sr) in enumerate(zip(skills_left, skills_right)):
        yy = y_s - i * 0.62
        t(ax, 0.55, yy, f'•  {sl}',
          fs=FS_SM, c=DARK, ha='left', va='center', zorder=5)
        t(ax, 5.15, yy, f'•  {sr}',
          fs=FS_SM, c=DARK, ha='left', va='center', zorder=5)

    hline(ax, 0.55, 9.5, 5.28, color=MGRAY, lw=1.2)

    # Compact disclaimer box
    box(ax, 0.55, 2.95, 8.9, 2.10, DISC_BG, ec=DISC_BD, lw=1.5, zorder=3, radius=0.1)
    box(ax, 0.55, 4.68, 8.9, 0.37, DISC_BD, zorder=4)
    t(ax, 5.0, 4.865,
      'Responsible Interpretation',
      fs=FS_SM, c='#7B3F00', w='bold', ha='center', va='center', zorder=5)

    disc = (
        'The Grid Stress Index is a custom review indicator for this portfolio project.\n'
        'It is not an official reliability metric or utility methodology.\n'
        'All data is from public EIA-930 records published by the U.S. EIA.'
    )
    t(ax, 5.0, 3.77, disc, fs=FS_BODY - 1, c='#7B3F00',
      ha='center', va='center', ls=1.55, zorder=5)

    # Feedback invitation and link
    t(ax, 5.0, 2.35,
      'Thoughts or questions? I would welcome feedback in the comments.',
      fs=FS_SM, c=MUTED, ha='center', va='center', zorder=5)
    t(ax, 5.0, 1.72,
      'Full project and dashboard links in the first comment.',
      fs=FS_SM, c=MUTED, ha='center', va='center', zorder=5)
    t(ax, 5.0, 1.15,
      'github.com/sileshith/california_grid_analysis',
      fs=FS_SM, c=NAVY, w='bold', ha='center', va='center', zorder=5)

    return fig

# =============================================================================
# BUILD
# =============================================================================
def build():
    slides = [
        slide_01, slide_02, slide_03, slide_04, slide_05,
        slide_06, slide_07, slide_08, slide_09,
    ]
    print(f'Building {len(slides)}-slide LinkedIn carousel PDF...')
    with PdfPages(PDF_OUT) as pdf:
        for i, fn in enumerate(slides, 1):
            print(f'  Slide {i}: {fn.__name__}...')
            fig = fn()
            pdf.savefig(fig, dpi=DPI)
            plt.close(fig)
    size_kb = os.path.getsize(PDF_OUT) / 1024
    print(f'\nPDF saved:  {PDF_OUT}')
    print(f'Size:       {size_kb:.0f} KB  ({size_kb/1024:.2f} MB)')
    print('\nScreenshot check:')
    for name, path in [('executive_overview',         EXEC_IMG),
                       ('high_priority_review_queue', HIPR_IMG),
                       ('authority_comparison',        AUTH_IMG)]:
        print(f'  {name}: {"OK" if os.path.exists(path) else "NOT FOUND"}')

if __name__ == '__main__':
    build()
