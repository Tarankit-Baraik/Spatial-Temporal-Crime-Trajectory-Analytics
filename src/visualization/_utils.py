"""Internal shared plotting helper -- not part of the package's public API.
Every function in temporal_plots/spatial_plots/model_plots accepts an
optional `ax` so callers can compose multi-panel figures; this is the one
place that logic lives, instead of being copy-pasted into every function."""
import matplotlib.pyplot as plt


def get_ax(ax=None, figsize=(8, 5)):
    """Returns (fig, ax). Creates a new figure/axes if `ax` is None, otherwise
    reuses the caller-supplied axes (and its parent figure) for composition
    into subplots."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax
    return ax.figure, ax
