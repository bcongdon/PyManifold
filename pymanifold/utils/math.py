"""Contains common math functions for working with Manifold."""

from math import log10


def number_to_prob_cpmm1(current: float, start: float, end: float, isLogScale: bool = False) -> float:
    """Go from a numeric answer to a probability."""
    if not (start <= current <= end):
        raise ValueError()
    if isLogScale:
        return log10(current - start + 1) / log10(end - start + 1)
    return (current - start) / (end - start)
