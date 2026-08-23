"""Reusable model-evaluation plotting functions (Phases 16-18). Every
function returns the Figure it created; saving/showing is the caller's
decision. Takes raw arrays (y_true/y_score/importances), not fitted model
objects -- keeps this module decoupled from any specific sklearn estimator,
so it works the same for logistic regression, decision tree, random forest,
or any future model added to Phase 14's comparison.
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import auc, confusion_matrix, precision_recall_curve, roc_curve

from src.visualization._utils import get_ax


def plot_confusion_matrix(
    y_true, y_pred, labels: tuple[str, str] = ("Not High-Crime", "High-Crime"), ax=None, title: str | None = None
) -> plt.Figure:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = get_ax(ax, figsize=(5, 5))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels)
    ax.set_yticks([0, 1]); ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title or "Confusion Matrix")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    return fig


def plot_roc_curve(y_true, y_score, ax=None, label: str | None = None, title: str = "ROC Curve") -> plt.Figure:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    fig, ax = get_ax(ax, figsize=(6, 6))
    ax.plot(fpr, tpr, color="#4C72B0", label=f"{label or 'model'} (AUC={roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_pr_curve(y_true, y_score, ax=None, label: str | None = None, title: str = "Precision-Recall Curve") -> plt.Figure:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    fig, ax = get_ax(ax, figsize=(6, 6))
    ax.plot(recall, precision, color="#4C72B0", label=label or "model")
    baseline = float(np.mean(y_true))
    ax.axhline(baseline, linestyle="--", color="grey", label=f"Baseline prevalence ({baseline:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_feature_importance(
    importances, feature_names, n: int = 20, ax=None, title: str = "Feature Importance"
) -> plt.Figure:
    if len(importances) != len(feature_names):
        raise ValueError(f"importances (len {len(importances)}) and feature_names (len {len(feature_names)}) must match")
    order = np.argsort(importances)[::-1][:n]
    fig, ax = get_ax(ax, figsize=(8, max(4, n * 0.3)))
    ax.barh([feature_names[i] for i in order][::-1], [importances[i] for i in order][::-1], color="#4C72B0")
    ax.set_xlabel("Importance")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_model_comparison(results: dict, metric: str = "f1", ax=None, title: str | None = None) -> plt.Figure:
    """`results`: {model_name: {metric_name: value, ...}, ...} -- e.g. the
    dict produced by modeling.evaluate across the baseline/LR/DT/RF models."""
    missing = [name for name, m in results.items() if metric not in m]
    if missing:
        raise KeyError(f"'{metric}' missing for model(s): {missing}")
    names = list(results.keys())
    values = [results[name][metric] for name in names]
    fig, ax = get_ax(ax, figsize=(7, 5))
    ax.bar(names, values, color="#55A868")
    ax.set_ylabel(metric.upper())
    ax.set_title(title or f"Model Comparison — {metric.upper()}")
    fig.tight_layout()
    return fig
