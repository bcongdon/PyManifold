"""Collection of utility functions that consumers of PyManifold might find useful."""

from .kelly import kelly_calc
from .math import number_to_prob_cpmm1

__all__ = ('kelly_calc', 'number_to_prob_cpmm1')
