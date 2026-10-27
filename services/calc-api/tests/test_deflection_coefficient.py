import numpy as np
import pytest


def fd_max_deflection(q: float, L: float, EI: float, spans: int = 3, per_span: int = 120) -> float:
    """有限差分解 EI v''''=q，四支座等跨连续梁。"""
    n = spans * per_span
    h = L / per_span
    supports = {s * per_span for s in range(1, spans)}
    size = n + 1
    A = np.zeros((size, size))
    rhs = np.full(size, q)
    A[0, 0] = 1
    rhs[0] = 0
    A[n, n] = 1
    rhs[n] = 0
    for s in supports:
        A[s, s] = 1
        rhs[s] = 0
    for i in range(1, n):
        if i in supports:
            continue
        if i == 1:
            A[i, 1], A[i, 2], A[i, 3] = 5, -4, 1
        elif i == n - 1:
            A[i, n - 3], A[i, n - 2], A[i, n - 1] = 1, -4, 5
        else:
            A[i, i - 2], A[i, i - 1], A[i, i], A[i, i + 1], A[i, i + 2] = 1, -4, 6, -4, 1
    v = np.linalg.solve(A, rhs * h**4 / EI)
    return float(np.max(np.abs(v)))


def test_coefficient_00677_matches_numerical_solution():
    q, L, EI = 1.0, 1500.0, 206000.0 * 107830.0
    analytic = 0.00677 * q * L**4 / EI
    numeric = fd_max_deflection(q, L, EI)
    assert numeric == pytest.approx(analytic, rel=0.02)


def test_simply_supported_deflection_matches_closed_form():
    q, L, EI = 1.0, 900.0, 206000.0 * 107830.0
    analytic = 5 * q * L**4 / (384 * EI)
    # 数值解用 1 跨（两端简支）对照
    numeric = fd_max_deflection(q, L, EI, spans=1, per_span=240)
    assert numeric == pytest.approx(analytic, rel=0.02)
