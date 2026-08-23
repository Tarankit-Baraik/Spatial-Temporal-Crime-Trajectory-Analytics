"""Reusable spatial plotting functions (Phases 9-10 EDA, Phase 19 final
figures). This project's stack is matplotlib/seaborn only (no geopandas
dependency) -- `plot_choropleth` renders GeoJSON polygons directly via
matplotlib patches. Every function returns the Figure it created; saving/
showing is the caller's decision.
"""
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon

from src.visualization._utils import get_ax


def plot_top_community_areas(
    df: pd.DataFrame, value_col: str = "crime_count", n: int = 15, ax=None, title: str | None = None
) -> plt.Figure:
    """Horizontal bar chart of the top `n` community areas by `value_col`,
    highest at the top."""
    agg = df.groupby("community_area")[value_col].sum().sort_values(ascending=False).head(n)
    fig, ax = get_ax(ax, figsize=(8, max(4, n * 0.35)))
    ax.barh(agg.index.astype(str), agg.values, color="#C44E52")
    ax.invert_yaxis()
    ax.set_xlabel(value_col.replace("_", " ").title())
    ax.set_ylabel("Community Area")
    ax.set_title(title or f"Top {n} Community Areas by {value_col.replace('_', ' ').title()}")
    fig.tight_layout()
    return fig


def plot_community_area_heatmap(
    df: pd.DataFrame, period_col: str = "month", value_col: str = "crime_count", ax=None, title: str | None = None
) -> plt.Figure:
    """community_area x period_col heatmap of `value_col` -- a proxy for a
    geographic map, since this project does not use shapefile-based
    plotting."""
    pivot = df.pivot_table(index="community_area", columns=period_col, values=value_col, aggfunc="sum", fill_value=0)
    fig, ax = get_ax(ax, figsize=(10, max(6, 0.25 * len(pivot))))
    sns.heatmap(pivot, cmap="YlOrRd", ax=ax, cbar_kws={"label": value_col.replace("_", " ").title()})
    ax.set_xlabel(period_col.replace("_", " ").title())
    ax.set_ylabel("Community Area")
    ax.set_title(title or f"Crime Intensity: Community Area x {period_col.replace('_', ' ').title()}")
    fig.tight_layout()
    return fig


def plot_coordinate_density(
    df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude", ax=None, gridsize: int = 50
) -> plt.Figure:
    """Hexbin density of incident coordinates -- a spatial-concentration view
    without shapefiles. Rows with missing coordinates are dropped explicitly
    (never silently, consistent with the ~1.45% coordinate-null rate found in
    01_data_ingestion_and_quality) and the excluded count is shown in the
    title so the plot is never mistaken for complete."""
    valid = df.dropna(subset=[lat_col, lon_col])
    dropped = len(df) - len(valid)

    fig, ax = get_ax(ax, figsize=(7, 7))
    hb = ax.hexbin(valid[lon_col], valid[lat_col], gridsize=gridsize, cmap="inferno", mincnt=1)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Incident Coordinate Density (n={len(valid):,}, {dropped:,} missing excluded)")
    fig.colorbar(hb, ax=ax, label="Incident count")
    fig.tight_layout()
    return fig


def plot_choropleth(
    df: pd.DataFrame,
    geojson: dict,
    value_col: str = "crime_count",
    area_col: str = "community_area",
    agg: str = "sum",
    ax=None,
    cmap: str = "YlOrRd",
    title: str | None = None,
) -> plt.Figure:
    """Chicago community-area choropleth. `geojson` is the dict returned by
    `data.geo_loader.load_or_fetch_boundaries()` -- fetched separately so
    this function stays a pure renderer with no network dependency, and so
    crime and weather-sensitivity maps can share one cached boundary file.

    Renders polygons directly from GeoJSON coordinates via matplotlib patches
    -- no geopandas/shapely dependency. Only the exterior ring of each
    polygon is drawn (interior holes, rare at this resolution, are ignored);
    acceptable at community-area granularity, not for parcel-level mapping.

    Areas present in the boundary file but absent from `df` are shown in
    grey with a note in the corner -- never silently left blank with no
    explanation.
    """
    from src.data.geo_loader import get_area_number_field

    area_field = get_area_number_field(geojson)
    values_by_area = df.groupby(area_col)[value_col].agg(agg)

    fig, ax = get_ax(ax, figsize=(9, 10))
    colormap = plt.get_cmap(cmap)
    norm = mcolors.Normalize(vmin=values_by_area.min(), vmax=values_by_area.max())

    patches, colors = [], []
    missing_areas = []
    for feature in geojson["features"]:
        area_num = int(float(feature["properties"][area_field]))
        value = values_by_area.get(area_num)
        face_color = "#DDDDDD" if value is None else colormap(norm(value))
        if value is None:
            missing_areas.append(area_num)

        geom = feature["geometry"]
        polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polygons:
            patches.append(MplPolygon(poly[0], closed=True))
            colors.append(face_color)

    collection = PatchCollection(patches, facecolor=colors, edgecolor="#555555", linewidth=0.5)
    ax.add_collection(collection)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title or f"{value_col.replace('_', ' ').title()} by Community Area")

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label=value_col.replace("_", " ").title(), fraction=0.04)

    if missing_areas:
        ax.text(
            0.02, 0.02, f"{len(missing_areas)} area(s) with no data shown in grey",
            transform=ax.transAxes, fontsize=8, color="#777777",
        )

    fig.tight_layout()
    return fig
