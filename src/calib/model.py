"""Affine accelerometer model m = S a + b: least-squares fit, correction and JSON."""
import json
from pathlib import Path

import numpy as np

STRUCTURES = ("full", "diagonal")


def vectors(values):
    result = np.asarray(values, dtype=float)
    if result.ndim != 2 or result.shape[1] != 3 or not len(result) or not np.isfinite(result).all():
        raise ValueError("Expected nonempty finite N by 3 vectors")
    return result


def write_json(path, value):
    """UTF-8 JSON with LF newlines on every platform, so bytes are reproducible."""
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


class AffineCalibration:
    """Fit m = S a + b; correct by solving S a_hat = m - b.

    ``structure="full"`` estimates all twelve parameters from rows
    X_i = [a_ix, a_iy, a_iz, 1] (rank 4 required). ``structure="diagonal"``
    is the classical six-position estimator: per axis j it fits
    m_j = s_j a_j + b_j using only references aligned with +/-e_j (rank 2 per
    axis, so both opposite faces are required). It ignores the perpendicular
    components, which nominal references know only to first order in the
    placement error, and assumes no cross-axis coupling.
    """

    def __init__(self, S, b, provenance=None, diagnostics=None, fitted=False, name=None):
        self.S = np.asarray(S, dtype=float)
        self.b = np.asarray(b, dtype=float)
        if self.S.shape != (3, 3) or self.b.shape != (3,) or not np.isfinite(self.S).all() or not np.isfinite(self.b).all():
            raise ValueError("Expected finite S (3 by 3) and b (3)")
        if np.linalg.cond(self.S) > 1e8:
            raise ValueError("Singular or unusably ill-conditioned calibration")
        # Same conservative infinity-norm guard as the JavaScript viewer.
        if np.linalg.cond(self.S, np.inf) > 1e8:
            raise ValueError("Calibration exceeds viewer conditioning limit")
        if provenance is not None and not isinstance(provenance, dict):
            raise ValueError("Provenance must be an object")
        if not isinstance(fitted, bool):
            raise ValueError("fitted must be true or false")
        if fitted and not provenance:
            raise ValueError("A fitted calibration requires training provenance")
        self.provenance = provenance
        self.diagnostics = diagnostics or {}
        # Only fit() or an explicit stored flag establishes fitting; metadata alone does not.
        self.fitted = fitted
        self.name = name or "S25 Ultra / nominal six-face fit"

    @classmethod
    def fit(cls, reference, measured, provenance, gravity=9.81, structure="full", name=None):
        reference, measured = vectors(reference), vectors(measured)
        if reference.shape != measured.shape or not np.isfinite(gravity) or gravity <= 0:
            raise ValueError("Reference/measured shapes must match; gravity must be positive")
        if structure not in STRUCTURES:
            raise ValueError(f"structure must be one of {STRUCTURES}")
        if structure == "diagonal":
            return cls._fit_diagonal(reference, measured, provenance, gravity, name)
        X = np.column_stack([reference, np.ones(len(reference))])
        B, _, rank, singular = np.linalg.lstsq(X, measured, rcond=None)
        if rank != 4:
            raise ValueError("Design must have rank 4: use affinely independent reference poses")
        return cls(B[:3].T, B[3], provenance, {
            "structure": "full", "parameters": 12,
            "rank": int(rank), "singular_values": singular.tolist(),
            "design_condition": float(np.linalg.cond(X)),
            "dimensionless_design_condition": float(np.linalg.cond(np.column_stack([reference / gravity, np.ones(len(reference))]))),
            "S_condition": float(np.linalg.cond(B[:3].T)),
        }, fitted=True, name=name)

    @classmethod
    def _fit_diagonal(cls, reference, measured, provenance, gravity, name):
        S, b, axes = np.eye(3), np.zeros(3), []
        norms = np.linalg.norm(reference, axis=1)
        for j in range(3):
            axial = np.abs(reference[:, j]) >= .99 * norms
            X = np.column_stack([reference[axial, j], np.ones(axial.sum())])
            rank = int(np.linalg.matrix_rank(X)) if axial.any() else 0
            if rank != 2:
                raise ValueError(f"Axis {'xyz'[j]} needs references along both +{'xyz'[j]} and -{'xyz'[j]} (rank 2)")
            (S[j, j], b[j]), *_ = np.linalg.lstsq(X, measured[axial, j], rcond=None)
            axes.append({"axis": "xyz"[j], "rows": int(axial.sum()), "rank": rank,
                         "condition": float(np.linalg.cond(np.column_stack([reference[axial, j] / gravity, np.ones(axial.sum())])))})
        return cls(S, b, provenance, {"structure": "diagonal", "parameters": 6, "per_axis": axes,
                                      "S_condition": float(np.linalg.cond(S))}, fitted=True, name=name)

    def apply(self, measured):
        measured = np.asarray(measured, dtype=float)
        single = measured.shape == (3,)
        batch = vectors(measured.reshape(1, 3) if single else measured)
        result = np.linalg.solve(self.S, (batch - self.b).T).T
        return result[0] if single else result

    def to_dict(self):
        return {"schema_version": 1, "name": self.name,
                "units": "m/s^2", "S": self.S.tolist(), "b": self.b.tolist(),
                "fitted": self.fitted, "provenance": self.provenance,
                "diagnostics": self.diagnostics}

    def save(self, path):
        write_json(path, self.to_dict())

    @classmethod
    def from_dict(cls, data):
        if data.get("units") != "m/s^2":
            raise ValueError("Expected units m/s^2")
        fitted = data.get("fitted", False)
        if not isinstance(fitted, bool):
            raise ValueError("fitted must be true or false")
        return cls(data["S"], data["b"], data.get("provenance"), data.get("diagnostics"), fitted, data.get("name"))

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
