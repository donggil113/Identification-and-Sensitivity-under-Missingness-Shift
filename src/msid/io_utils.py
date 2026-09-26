"""Serialisation helpers: exact fractions are stored as strings plus a float."""

from __future__ import annotations

from fractions import Fraction
from typing import Any


def frac(v):
    if v is None:
        return None
    v = Fraction(v)
    return {"exact": f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator),
            "float": float(v)}


def key(obj) -> str:
    """Readable key for cells/patterns/observed tuples."""
    if isinstance(obj, tuple):
        return "(" + ",".join("_" if o is None else key(o) for o in obj) + ")"
    return str(obj)


def policy_json(pi):
    return {f"x={key(c[0])},y={c[1]}": {f"r={key(r)}": frac(p) for r, p in row.items()}
            for c, row in pi.items()}


def to_jsonable(obj: Any):
    if isinstance(obj, Fraction):
        return frac(obj)
    if isinstance(obj, dict):
        return {(k if isinstance(k, str) else key(k)): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
