"""Contains a function to calculate the optimal bet if your estimated probability is the true probability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Literal, cast

from numpy import argmax
from numpy import log as ln

if TYPE_CHECKING:  # pragma: no cover
    from ..types import Market


def expected_log_wealth(
    market: Market, sub_prob: float, bet: float, outcome: Literal["YES", "NO"], balance: int
) -> float:
    """Calculate the expected log wealth for a hypothetical bet."""
    p = sub_prob

    if outcome == 'YES':
        E: float = p * ln(balance - bet + shares_bought(market, bet, outcome)) + (1 - p) * ln(balance - bet)

    elif outcome == 'NO':
        E = (1 - p) * ln(balance - bet + shares_bought(market, bet, outcome)) + p * ln(balance - bet)

    return E


def shares_bought(
    market: Market, bet: float, outcome: Literal["YES", "NO"]
) -> float:
    """Figure out the number of shares a given purchace yields.

    Returns the number of shares and the resulting pool. This function assumes Manifold Markets are using
    'Maniswap' as their Automated Market Maker. More on Maniswap
    can be found here: 'https://manifoldmarkets.notion.site/Maniswap-ce406e1e897d417cbd491071ea8a0c39'.
    """
    # find the probability the market was initialised at
    p = market.p
    assert p is not None

    # find the current liquidity pool
    pool = cast(Dict[Literal['YES', 'NO'], float], market.pool)
    assert not isinstance(pool, float)

    y = pool['YES']
    n = pool['NO']

    # implement Maniswap
    k: float = y**p * n**(1 - p)

    y += bet
    n += bet

    if outcome == "YES":
        y2: float = (k / n**(1 - p))**(1 / p)
        y -= y2
        shares_without_fees = y
        post_bet_probability = p * n / (p * n + (1 - p) * y2)
        fee = 0 * (1 - post_bet_probability) * bet + 0.1
        shares_after_fees = shares_without_fees - fee
        return shares_after_fees

    elif outcome == "NO":
        n2 = (k / y**p)**(1 / (1 - p))
        n -= n2
        shares_without_fees = n
        post_bet_probability = p * n2 / (p * n2 + (1 - p) * y)
        fee = 0 * post_bet_probability * bet + 0.1
        shares_after_fees = shares_without_fees - fee
        return shares_after_fees

    else:
        raise ValueError("Please give a valid outcome")


def kelly_calc(market: Market, subjective_prob: float, balance: int) -> tuple[int, Literal["YES", "NO"]]:
    """For a given binary market, find the bet that maximises expected log wealth."""
    # figure out which option to buy
    assert market.probability
    outcome: Literal['YES', 'NO'] = 'YES' if (subjective_prob > market.probability) else 'NO'

    # find the kelly bet
    kelly_bet = argmax([expected_log_wealth(market, subjective_prob, bet, outcome, balance) for bet in range(balance)])

    return int(kelly_bet), outcome
