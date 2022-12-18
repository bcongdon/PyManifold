"""Contains common math functions for working with Manifold."""

from math import log10


def number_to_prob_cpmm1(current: float, start: float, end: float, isLogScale: bool = False) -> float:
    """Go from a numeric answer to a probability."""
    if not (start <= current <= end):
        raise ValueError()
    if isLogScale:
        return log10(current - start + 1) / log10(end - start + 1)
    return (current - start) / (end - start)


def pool_to_prob_cpmm1(yes: float, no: float, p: float) -> float:
    """Go from a pool of YES/NO to a probability using Maniswap."""
    if yes <= 0 or no <= 0 or not (0 < p < 1):
        raise ValueError()
    pno = p * no
    return pno / ((1 - p) * yes + pno)


def pool_to_number_cpmm1(yes: float, no: float, p: float, start: float, end: float, isLogScale: bool = False) -> float:
    """Go from a pool of probability to a numeric answer."""
    if start >= end:
        raise ValueError()
    probability = pool_to_prob_cpmm1(yes, no, p)
    return prob_to_number_cpmm1(probability, start, end, isLogScale)


def prob_to_number_cpmm1(probability: float, start: float, end: float, isLogScale: bool = False) -> float:
    """Go from a probability to a numeric answer."""
    if isLogScale:
        ret: float = (end - start + 1)**probability + start - 1
    else:
        ret = start + (end - start) * probability
    ret = max(start, min(end, ret))
    return ret
