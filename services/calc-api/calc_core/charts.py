"""内力与变形图：弯矩、剪力、挠度、轴力、风弯矩。"""

from __future__ import annotations

import io

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

COLOR_M = "#e5484d"
COLOR_V = "#3e63dd"
COLOR_D = "#30a46c"
COLOR_N = "#8e4ec6"


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _fmt(ax, ylabel: str) -> None:
    ax.axhline(0, color="#9ca3af", linewidth=0.8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, color="#e5e7eb", linewidth=0.6)
    ax.tick_params(labelsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def _continuous_beam(q: float, L: float, EI: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    spans, per_span = 3, 120
    n = spans * per_span
    h = L / per_span
    supports = {per_span, 2 * per_span}
    size = n + 1
    A = np.zeros((size, size))
    rhs = np.full(size, q)
    A[0, 0] = 1.0
    rhs[0] = 0.0
    A[n, n] = 1.0
    rhs[n] = 0.0
    for s in supports:
        A[s, s] = 1.0
        rhs[s] = 0.0
    for i in range(1, n):
        if i in supports:
            continue
        if i == 1:
            A[i, 1], A[i, 2], A[i, 3] = 5.0, -4.0, 1.0
        elif i == n - 1:
            A[i, n - 3], A[i, n - 2], A[i, n - 1] = 1.0, -4.0, 5.0
        else:
            A[i, i - 2], A[i, i - 1], A[i, i], A[i, i + 1], A[i, i + 2] = 1.0, -4.0, 6.0, -4.0, 1.0
    v = np.linalg.solve(A, rhs * h**4 / EI)
    x = np.arange(size) * h
    M = -EI * np.gradient(np.gradient(v, h), h)
    V = np.gradient(M, x)
    return x, M, V, -v


def beam_diagrams(
    q: float,
    length: float,
    EI: float,
    kind: str = "continuous",
    title: str = "",
    *,
    service_q: float | None = None,
) -> bytes:
    """返回均布荷载梁的 M/V/v 图；挠度可单独采用标准值 service_q。"""
    q_ = q  # 1 kN/m == 1 N/mm
    q_service = q_ if service_q is None else service_q
    L = length * 1000.0

    xs, Ms, Vs, Ds = [], [], [], []

    if kind == "continuous":
        x, M, V, _ = _continuous_beam(q_, L, EI)
        _, _, _, D = _continuous_beam(q_service, L, EI)
        xs, Ms, Vs, Ds = [x], [M], [V], [D]
    else:
        x = np.linspace(0, L, 320)
        M = q_ * x * (L - x) / 2
        V = q_ * (L / 2 - x)
        v = -q_service * x * (L**3 - 2 * L * x**2 + x**3) / (24 * EI)
        xs, Ms, Vs, Ds = [x], [M], [V], [v]

    x = np.concatenate(xs) / 1000.0
    M = np.concatenate(Ms) / 1e6
    V = np.concatenate(Vs) / 1e3
    D = np.concatenate(Ds)

    fig, axes = plt.subplots(3, 1, figsize=(7.4, 5.6), sharex=True)
    axes[0].plot(x, M, color=COLOR_M, linewidth=1.6)
    axes[0].fill_between(x, M, 0, color=COLOR_M, alpha=0.12)
    _fmt(axes[0], "弯矩 M (kN·m)")
    axes[0].set_title(title, fontsize=10)

    axes[1].plot(x, V, color=COLOR_V, linewidth=1.4)
    axes[1].fill_between(x, V, 0, color=COLOR_V, alpha=0.12)
    _fmt(axes[1], "剪力 V (kN)")

    axes[2].plot(x, D, color=COLOR_D, linewidth=1.6)
    axes[2].fill_between(x, D, 0, color=COLOR_D, alpha=0.12)
    _fmt(axes[2], "挠度 v (mm)")
    axes[2].set_xlabel("沿梁长度 x (m)", fontsize=9)

    return _png(fig)


def simple_beam_point_load_diagrams(
    point_load: float,
    q: float,
    length: float,
    EI: float,
    *,
    service_point_load: float | None = None,
    service_q: float | None = None,
    deflection_factor: float = 1.0,
    point_fraction: float = 1.0 / 3.0,
    title: str = "",
) -> bytes:
    """简支梁在三分点集中力与自重下的 M/V/v 图。

    挠度先按标准值计算梁的弹性挠度，再乘明确的样本反算系数；
    该系数不是规范值，图内单独标注其来源和适用范围。
    """
    P = point_load * 1000.0
    q_ = q
    L = length * 1000.0
    a = point_fraction * L
    b = L - a
    R = P + q_ * L / 2.0

    x = np.linspace(0.0, L, 601)
    M = R * x - q_ * x**2 / 2.0 - np.where(x >= a, P * (x - a), 0.0)
    V = R - q_ * x - np.where(x >= a, P, 0.0)

    P_service = point_load if service_point_load is None else service_point_load
    P_service *= 1000.0
    q_service = q if service_q is None else service_q
    point_deflection = np.where(
        x <= a,
        P_service * b * x * (L**2 - b**2 - x**2) / (6.0 * L * EI),
        P_service * a * (L - x) * (L**2 - a**2 - (L - x) ** 2) / (6.0 * L * EI),
    )
    distributed_deflection = (
        q_service
        * x
        * (L**3 - 2.0 * L * x**2 + x**3)
        / (24.0 * EI)
    )
    D = (point_deflection + distributed_deflection) * deflection_factor

    fig, axes = plt.subplots(3, 1, figsize=(7.4, 5.8), sharex=True)
    axes[0].plot(x / 1000.0, M / 1e6, color=COLOR_M, linewidth=1.6)
    axes[0].fill_between(x / 1000.0, M / 1e6, 0, color=COLOR_M, alpha=0.12)
    axes[0].axvline(a / 1000.0, color="#6b7280", linestyle="--", linewidth=0.8)
    _fmt(axes[0], "弯矩 M (kN·m)")
    axes[0].set_title(title, fontsize=10)

    axes[1].plot(x / 1000.0, V / 1e3, color=COLOR_V, linewidth=1.4)
    axes[1].fill_between(x / 1000.0, V / 1e3, 0, color=COLOR_V, alpha=0.12)
    axes[1].axvline(a / 1000.0, color="#6b7280", linestyle="--", linewidth=0.8)
    _fmt(axes[1], "剪力 V (kN)")

    axes[2].plot(x / 1000.0, D, color=COLOR_D, linewidth=1.6)
    axes[2].fill_between(x / 1000.0, D, 0, color=COLOR_D, alpha=0.12)
    _fmt(axes[2], "挠度 v (mm，向下为正)")
    axes[2].set_xlabel("沿梁长度 x (m)", fontsize=9)
    axes[2].text(
        0.02,
        0.96,
        (
            f"模型：P={point_load:.3f} kN @ x=L/{round(1 / point_fraction):d}，"
            f"q={q:.3f} kN/m\n"
            f"v 含单样本反算系数 {deflection_factor:.4f}（非规范值）"
        ),
        transform=axes[2].transAxes,
        va="top",
        ha="left",
        fontsize=7.8,
        bbox={"facecolor": "white", "edgecolor": "#d1d5db", "alpha": 0.92},
    )

    return _png(fig)


def cantilever_beam_diagrams(q: float, L: float, EI: float, title: str = "") -> bytes:
    """q: kN/m；L: m；EI: N·mm²。返回悬挑梁 M/V/v 三子图的 PNG。"""
    q_ = q  # 1 kN/m == 1 N/mm
    length = L * 1000.0
    x = np.linspace(0, length, 320)
    M = q_ * (length - x) ** 2 / 2.0
    V = q_ * (length - x)
    v = q_ * x**2 * (6 * length**2 - 4 * length * x + x**2) / (24 * EI)

    x_m = x / 1000.0
    fig, axes = plt.subplots(3, 1, figsize=(7.4, 5.6), sharex=True)
    axes[0].plot(x_m, M / 1e6, color=COLOR_M, linewidth=1.6)
    axes[0].fill_between(x_m, M / 1e6, 0, color=COLOR_M, alpha=0.12)
    _fmt(axes[0], "弯矩 M (kN·m)")
    axes[0].set_title(title, fontsize=10)

    axes[1].plot(x_m, V / 1e3, color=COLOR_V, linewidth=1.4)
    axes[1].fill_between(x_m, V / 1e3, 0, color=COLOR_V, alpha=0.12)
    _fmt(axes[1], "剪力 V (kN)")

    axes[2].plot(x_m, v, color=COLOR_D, linewidth=1.6)
    axes[2].fill_between(x_m, v, 0, color=COLOR_D, alpha=0.12)
    _fmt(axes[2], "挠度 v (mm)")
    axes[2].set_xlabel("自固定端沿梁长 x (m)", fontsize=9)

    return _png(fig)


def column_diagrams(N: float, mw: float, H: float, title: str = "") -> bytes:
    """N: kN；mw: 单立杆段风弯矩设计值 kN·m；H: m。返回轴力图 + 风弯矩图。"""
    z = np.linspace(0, H, 120)
    axial = N * z / H
    moment = np.full_like(z, mw)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 4.4), sharey=True)
    ax1.plot(axial, z, color=COLOR_N, linewidth=1.8)
    ax1.fill_betweenx(z, axial, 0, color=COLOR_N, alpha=0.12)
    ax1.set_xlabel("轴力 N (kN)", fontsize=9)
    ax1.set_ylabel("高度 z (m)", fontsize=9)
    ax1.set_title("立杆轴力图", fontsize=10)

    ax2.plot(moment, z, color=COLOR_M, linewidth=1.8)
    ax2.fill_betweenx(z, moment, 0, color=COLOR_M, alpha=0.12)
    ax2.set_xlabel("立杆段风弯矩 Mw (kN·m)", fontsize=9)
    ax2.set_title("立杆段风弯矩", fontsize=10)

    for ax in (ax1, ax2):
        ax.grid(True, color="#e5e7eb", linewidth=0.6)
        ax.tick_params(labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    fig.suptitle(title, fontsize=10)
    return _png(fig)
