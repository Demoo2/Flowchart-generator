"""Chart of measured steps vs. input size, with an optional Big-O reference curve.

Big-O ignores constant factors: bubble sort does about n**2 / 4 swaps, not n**2,
so a raw n**2 curve dwarfs the measured line. The reference curve is therefore
scaled by the constant c that makes c * f(n) fit the measured points best
(least squares), and the legend shows that constant, e.g. "n² / 4".
"""
import io

import numpy as np
from matplotlib.figure import Figure

# f(n) for each complexity, and how it is written in the legend
COMPLEXITIES = {
    "O(1)": (lambda n: np.ones_like(n), "1"),
    "O(log n)": (lambda n: np.log2(np.maximum(n, 1)), "log n"),
    "O(n)": (lambda n: n, "n"),
    "O(n log n)": (lambda n: n * np.log2(np.maximum(n, 1)), "n log n"),
    "O(n**2)": (lambda n: n ** 2, "n²"),
    "O(n**3)": (lambda n: n ** 3, "n³"),
}


def fit_scale(y, f):
    """Constant c that makes c * f closest to y (least squares); 1 if no positive fit exists."""
    denominator = float(np.dot(f, f))
    c = float(np.dot(y, f)) / denominator if denominator else 0.0
    return c if c > 0 else 1.0


def chart_bytes(
    x, 
    y, 
    time_complexity="O(n)", 
    time_chart=True, title="", 
    x_label="", 
    y_label="", 
    label="", 
    fmt="png"
):
    """Image of the chart, rendered in memory (for the web API)."""
    order = np.argsort(x)  # points may come in any order; the line must go left to right
    x = np.asarray(x, dtype=float)[order]
    y = np.asarray(y, dtype=float)[order]

    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    ax.plot(x, y, "o-", color="#2563eb", linewidth=2.5, label=label or "Your algorithm")

    if time_chart:
        f, term = COMPLEXITIES[time_complexity]
        c = fit_scale(y, f(x))
        ax.plot(x, c * f(x), "--", color="gray", label=f"{time_complexity.strip('O()')}")

    ax.set_title(title or (f"Time Complexity: {time_complexity}" if time_chart else "Number of steps"), fontsize=14, fontweight="bold")
    ax.set_xlabel(x_label or "Input size (n)", fontsize=12)
    ax.set_ylabel(y_label or "Number of steps", fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format=fmt, dpi=150)
    return buffer.getvalue()
