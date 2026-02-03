"""Business Unit: scripts | Status: current.

Dashboard pages for multi-page Streamlit app.

Exports:
    - components: Reusable UI components (hero_metric, metric_card, etc.)
    - styles: Theme colors and CSS injection (inject_styles, get_colors)
"""

from . import components, styles

__all__ = ["components", "styles"]
