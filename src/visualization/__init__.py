"""Visualization: reusable plotting functions for temporal, spatial, and
model-evaluation figures (Phases 9-10, 16-19). Re-exports the public
functions so callers can `from src.visualization import plot_trend_over_time,
plot_top_community_areas, plot_roc_curve` instead of reaching into submodules.
Every function returns a matplotlib Figure -- saving/showing is the caller's
decision, never done inside this package.
"""
from src.visualization.model_plots import (
    plot_confusion_matrix,
    plot_feature_importance,
    plot_model_comparison,
    plot_pr_curve,
    plot_roc_curve,
)
from src.visualization.spatial_plots import (
    plot_choropleth,
    plot_community_area_heatmap,
    plot_coordinate_density,
    plot_top_community_areas,
)
from src.visualization.temporal_plots import (
    plot_crime_by_period,
    plot_seasonal_crime,
    plot_trend_over_time,
    plot_weather_vs_crime_over_time,
)

__all__ = [
    "plot_crime_by_period",
    "plot_seasonal_crime",
    "plot_trend_over_time",
    "plot_weather_vs_crime_over_time",
    "plot_top_community_areas",
    "plot_community_area_heatmap",
    "plot_coordinate_density",
    "plot_choropleth",
    "plot_confusion_matrix",
    "plot_roc_curve",
    "plot_pr_curve",
    "plot_feature_importance",
    "plot_model_comparison",
]
