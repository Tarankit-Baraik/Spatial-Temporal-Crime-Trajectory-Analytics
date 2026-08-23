"""Reusable temporal plotting functions (Phases 9-10 EDA, Phase 19 final
figures). Every function returns the Figure it created -- plots are never
shown or saved inside this module; that decision belongs to the caller
(`fig.savefig(OUTPUTS_DIR / "figures" / "temporal" / "...png")`).
"""
import matplotlib.pyplot as plt
import pandas as pd

from src.visualization._utils import get_ax

SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]


def plot_crime_by_period(
    df: pd.DataFrame, period_col: str, value_col: str = "crime_count", agg: str = "sum", ax=None, title: str | None = None
) -> plt.Figure:
    """Bar chart of `value_col` aggregated by `period_col` (e.g. month,
    day_of_week, hour, year). Sorted by period value, not by size -- the
    x-axis stays chronologically/numerically meaningful."""
    if period_col not in df.columns:
        raise KeyError(f"'{period_col}' not in dataframe")
    agg_series = df.groupby(period_col)[value_col].agg(agg).sort_index()

    fig, ax = get_ax(ax)
    ax.bar(agg_series.index.astype(str), agg_series.values, color="#4C72B0")
    ax.set_xlabel(period_col.replace("_", " ").title())
    ax.set_ylabel(f"{agg.title()} {value_col.replace('_', ' ')}")
    ax.set_title(title or f"{value_col.replace('_', ' ').title()} by {period_col.replace('_', ' ').title()}")
    fig.tight_layout()
    return fig


def plot_seasonal_crime(
    df: pd.DataFrame, value_col: str = "crime_count", agg: str = "sum", ax=None, title: str | None = None
) -> plt.Figure:
    """Bar chart of `value_col` aggregated by season (default sum), in
    calendar order (Winter -> Fall), not alphabetical. Use agg="count" when
    `value_col` is an identifier column (e.g. incident `id`), not a numeric
    measure -- summing a string column silently concatenates instead of
    counting."""
    agg_series = df.groupby("season")[value_col].agg(agg).reindex(SEASON_ORDER)
    fig, ax = get_ax(ax)
    ax.bar(agg_series.index, agg_series.values, color="#55A868")
    ax.set_ylabel(value_col.replace("_", " ").title())
    ax.set_title(title or "Crime by Season")
    fig.tight_layout()
    return fig


def plot_trend_over_time(
    df: pd.DataFrame, date_col: str = "date", value_col: str = "crime_count",
    freq: str = "ME", rolling: int | None = None, ax=None, title: str | None = None,
) -> plt.Figure:
    """Line plot of `value_col` resampled to `freq` (e.g. 'ME' month-end,
    'W' week) over time, with an optional rolling-mean overlay."""
    series = df.set_index(date_col)[value_col].resample(freq).sum()
    fig, ax = get_ax(ax)
    ax.plot(series.index, series.values, color="#4C72B0", label=value_col.replace("_", " ").title())
    if rolling:
        ax.plot(series.index, series.rolling(rolling).mean(), color="#C44E52", linestyle="--", label=f"{rolling}-period rolling mean")
        ax.legend()
    ax.set_xlabel("Date")
    ax.set_title(title or f"{value_col.replace('_', ' ').title()} Over Time")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_weather_vs_crime_over_time(
    df: pd.DataFrame, date_col: str = "date", crime_col: str = "crime_count", weather_col: str = "avg_temp", ax=None,
) -> plt.Figure:
    """Dual-axis line plot: crime volume vs. a weather variable over time, on
    the merged community_area x date frame (aggregated to one line per date
    first, since the source frame has one row per community_area x date)."""
    daily = df.groupby(date_col)[[crime_col, weather_col]].sum() if crime_col in df else df.set_index(date_col)
    daily[weather_col] = df.groupby(date_col)[weather_col].mean()

    fig, ax1 = get_ax(ax)
    ax2 = ax1.twinx()
    ax1.plot(daily.index, daily[crime_col], color="#4C72B0", label=crime_col.replace("_", " ").title())
    ax2.plot(daily.index, daily[weather_col], color="#DD8452", alpha=0.7, label=weather_col.replace("_", " ").title())
    ax1.set_ylabel(crime_col.replace("_", " ").title(), color="#4C72B0")
    ax2.set_ylabel(weather_col.replace("_", " ").title(), color="#DD8452")
    ax1.set_title(f"{crime_col.replace('_', ' ').title()} vs. {weather_col.replace('_', ' ').title()}")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig
