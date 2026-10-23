"""The notebook's forward affine regression, with validation and persistence."""
import json
from pathlib import Path

import numpy as np


def vectors(values):
    result = np.asarray(values, dtype=float)
    if result.ndim != 2 or result.shape[1] != 3 or not len(result) or not np.isfinite(result).all():
        raise ValueError("Expected nonempty finite N by 3 vectors")
    return result


class AffineCalibration:
    """Fit m = S a + b; correct by solving S a_hat = m - b."""

    def __init__(self, S, b, provenance=None, diagnostics=None):
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
        self.provenance = provenance
        self.diagnostics = diagnostics or {}

    @classmethod
    def fit(cls, reference, measured, provenance, gravity=9.81):
        reference, measured = vectors(reference), vectors(measured)
        if reference.shape != measured.shape or not np.isfinite(gravity) or gravity <= 0:
            raise ValueError("Reference/measured shapes must match; gravity must be positive")
        X = np.column_stack([reference, np.ones(len(reference))])
        B, _, rank, singular = np.linalg.lstsq(X, measured, rcond=None)
        if rank != 4:
            raise ValueError("Design must have rank 4: use affinely independent reference poses")
        return cls(B[:3].T, B[3], provenance, {
            "rank": int(rank), "singular_values": singular.tolist(),
            "design_condition": float(np.linalg.cond(X)),
            "dimensionless_design_condition": float(np.linalg.cond(np.column_stack([reference / gravity, np.ones(len(reference))]))),
            "S_condition": float(np.linalg.cond(B[:3].T)),
        })

    def apply(self, measured):
        measured = np.asarray(measured, dtype=float)
        single = measured.shape == (3,)
        batch = vectors(measured.reshape(1, 3) if single else measured)
        result = np.linalg.solve(self.S, (batch - self.b).T).T
        return result[0] if single else result

    def to_dict(self):
        return {"schema_version": 1, "name": "S25 Ultra / nominal six-face fit",
                "units": "m/s^2", "S": self.S.tolist(), "b": self.b.tolist(),
                "fitted": bool(self.provenance), "provenance": self.provenance,
                "diagnostics": self.diagnostics}

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, allow_nan=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("units") != "m/s^2":
            raise ValueError("Expected units m/s^2")
        if data.get("fitted") is True and not data.get("provenance"):
            raise ValueError("A fitted calibration requires training provenance")
        return cls(data["S"], data["b"], data.get("provenance"), data.get("diagnostics"))
