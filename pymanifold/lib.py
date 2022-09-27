from __future__ import annotations

from itertools import chain
from math import inf
from typing import TYPE_CHECKING

import requests

from .types import Bet, LiteUser, Market, LiteMarket

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Iterable, Optional, List, Sequence, Tuple, Union

BASE_URI = "https://manifold.markets/api/v0"


class ManifoldClient:
    """A client for interacting with the website manifold.markets."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def list_markets(self, *args, **kwargs) -> List[LiteMarket]:
        """List all markets."""
        return list(self.get_markets(*args, **kwargs))

    def get_markets(
        self, limit: Optional[int] = None, before: Optional[str] = None
    ) -> Iterable[LiteMarket]:
        """Iterate over all markets."""
        response = requests.get(
            url=BASE_URI + "/markets", params={"limit": limit, "before": before}
        )
        return (LiteMarket.from_dict(market) for market in response.json())

    def stream_markets(
        self,
        limit: Optional[int] = None,
        before: Optional[str] = None,
    ) -> Iterable[LiteMarket]:
        """Iterate over all markets, including new ones."""
        most_recent = new_most_recent = 0
        least_recent = new_least_recent = inf
        least_recent_id = before
        while True:
            candidates: Iterable[LiteMarket] = self.get_markets(limit=limit, before=least_recent_id)
            if before is None:
                candidates = chain(candidates, self.get_markets(limit=limit))
            candidate: LiteMarket
            idx = 0
            for idx, candidate in enumerate(candidates):
                if candidate.createdTime < most_recent or candidate.createdTime > least_recent:
                    new_most_recent = max(new_most_recent, candidate.createdTime)
                    new_least_recent = max(new_least_recent, candidate.createdTime)
                    if candidate.createdTime == new_least_recent:
                        least_recent_id = candidate.id
                    yield candidate
            if not idx:
                break
            least_recent = new_least_recent
            most_recent = new_most_recent

    def list_bets(self, *args, **kwargs) -> List[Bet]:
        """List all bets."""
        return list(self.get_bets(*args, **kwargs))

    def get_bets(
        self,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        username: Optional[str] = None,
        market: Optional[str] = None,
    ) -> Iterable[Bet]:
        """Iterate over all bets."""
        response = requests.get(
            url=BASE_URI + "/bets", params={"limit": limit, "before": before, "username": username, "market": market}
        )
        return (Bet.from_dict(market) for market in response.json())

    def stream_bets(
        self,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        username: Optional[str] = None,
        market: Optional[str] = None,
    ) -> Iterable[Bet]:
        """Iterate over all bets, including new ones."""
        most_recent = new_most_recent = 0
        least_recent = new_least_recent = inf
        least_recent_id = before
        while True:
            candidates: Iterable[Bet] = self.get_bets(
                limit=limit, before=least_recent_id, username=username, market=market
            )
            if before is None:
                candidates = chain(candidates, self.get_bets(limit=limit, username=username, market=market))
            candidate: Bet
            for idx, candidate in enumerate(candidates):
                if candidate.createdTime < most_recent or candidate.createdTime > least_recent:
                    new_most_recent = max(new_most_recent, candidate.createdTime)
                    new_least_recent = max(new_least_recent, candidate.createdTime)
                    if candidate.createdTime == new_least_recent:
                        least_recent_id = candidate.id
                    yield candidate
            if not idx:
                break
            least_recent = new_least_recent
            most_recent = new_most_recent

    def get_market_by_id(self, market_id: str) -> Market:
        """Get a market by id."""
        return Market.from_dict(self._get_market_by_id_raw(market_id))

    def _get_market_by_id_raw(self, market_id: str) -> Dict[str, Any]:
        """Get a market by id."""
        response = requests.get(url=BASE_URI + "/market/" + market_id)
        return response.json()

    def get_market_by_slug(self, slug: str) -> Market:
        """Get a market by slug."""
        return Market.from_dict(self._get_market_by_slug_raw(slug))

    def _get_market_by_slug_raw(self, slug: str) -> Dict[str, Any]:
        """Get a market by slug."""
        response = requests.get(url=BASE_URI + "/slug/" + slug)
        return response.json()

    def get_market_by_url(self, url: str) -> Market:
        """Get a market by url."""
        return Market.from_dict(self._get_market_by_url_raw(url))

    def _get_market_by_url_raw(self, url: str) -> Dict[str, Any]:
        """Get a market by url."""
        slug = url.split("/")[-1].split("#")[0]
        response = requests.get(url=BASE_URI + "/slug/" + slug)
        return response.json()

    def get_user(self, handle: str) -> LiteUser:
        """Get a user by handle."""
        return LiteUser.from_dict(self._get_user_raw(handle))

    def _get_user_raw(self, handle: str) -> Dict[str, Any]:
        response = requests.get(url=BASE_URI + "/user/" + handle)
        return response.json()

    def _auth_headers(self) -> dict:
        if self.api_key:
            return {"Authorization": "Key " + self.api_key}
        else:
            raise RuntimeError("No API key provided")

    def cancel_market(self, market: Union[LiteMarket, str]):
        """Cancel a market, resolving it N/A."""
        if isinstance(market, LiteMarket):
            marketId = market.id
        else:
            marketId = market
        response = requests.post(
            url=BASE_URI + "/market/" + marketId + "/resolve",
            json={
                "outcome": "CANCEL",
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response

    def create_bet(self, contractId: str, amount: int, outcome: str, limitProb: Optional[float] = None) -> str:
        """Place a bet.

        Returns the ID of the created bet.
        """
        json = {
            "amount": int(amount),
            "contractId": contractId,
            "outcome": outcome,
        }
        if limitProb is not None:
            json['limitProb'] = limitProb
        response = requests.post(
            url=BASE_URI + "/bet",
            json=json,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()["betId"]

    def create_free_response_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
    ):
        """Create a free response market."""
        return self._create_market(
            "FREE_RESPONSE", question, description, closeTime, tags
        )

    def create_multiple_choice_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        answers: List[str],
        tags: Optional[List[str]] = None,
    ):
        """Create a free response market."""
        return self._create_market(
            "MULTIPLE_CHOICE", question, description, closeTime, tags, answers=answers
        )

    def create_numeric_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        minValue: int,
        maxValue: int,
        isLogScale: bool,
        initialValue: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ):
        """Create a numeric market."""
        return self._create_market(
            "PSEUDO_NUMERIC",
            question,
            description,
            closeTime,
            tags,
            minValue=minValue,
            maxValue=maxValue,
            isLogScale=isLogScale,
            initialValue=initialValue,
        )

    def create_binary_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
        initialProb: Optional[int] = 50,
    ):
        """Create a binary market."""
        return self._create_market(
            "BINARY", question, description, closeTime, tags, initialProb=initialProb
        )

    def _create_market(
        self,
        outcomeType: str,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
        initialProb: Optional[int] = 50,
        initialValue: Optional[float] = None,
        minValue: Optional[int] = None,
        maxValue: Optional[int] = None,
        isLogScale: Optional[bool] = None,
        answers: Optional[Sequence[str]] = None,
    ):
        """Create a market."""
        data = {
            "outcomeType": outcomeType,
            "question": question,
            "description": description,
            "closeTime": closeTime,
            "tags": tags or [],
        }
        if outcomeType == "BINARY":
            data["initialProb"] = initialProb
        elif outcomeType == "FREE_RESPONSE":
            pass
        elif outcomeType == "PSEUDO_NUMERIC":
            data["min"] = minValue
            data["max"] = maxValue
            data["isLogScale"] = isLogScale
            if initialValue is None:
                raise ValueError("Needs initial value")
            data["initialValue"] = initialValue
        elif outcomeType == "MULTIPLE_CHOICE":
            data["answers"] = answers
        else:
            raise Exception(
                "Invalid outcome type. Outcome should be one of: BINARY, FREE_RESPONSE, PSEUDO_NUMERIC, MULTIPLE_CHOICE"
            )

        response = requests.post(
            url=BASE_URI + "/market",
            json=data,
            headers=self._auth_headers(),
        )
        if response.status_code in range(400, 500):
            response.raise_for_status()
        elif response.status_code >= 500:
            for mkt in self.list_markets():
                if (question, outcomeType, closeTime) == (mkt.question, mkt.outcomeType, mkt.closeTime):
                    return mkt
        return LiteMarket.from_dict(response.json())

    def resolve_market(self, market: Union[LiteMarket, str], *args, **kwargs):
        """Resolve a market, with different inputs depending on its type."""
        if not isinstance(market, LiteMarket):
            market = self.get_market_by_id(market)
        if market.outcomeType == "BINARY":
            return self._resolve_binary_market(market, *args, **kwargs)
        elif market.outcomeType == "FREE_RESPONSE":
            return self._resolve_free_response_market(market, *args, **kwargs)
        elif market.outcomeType == "MULTIPLE_CHOICE":
            return self._resolve_multiple_choice_market(market, *args, **kwargs)
        elif market.outcomeType == "PSEUDO_NUMERIC":
            return self._resolve_pseudo_numeric_market(market, *args, **kwargs)
        else:
            raise NotImplementedError()

    def _resolve_binary_market(self, market, probabilityInt: float):
        if probabilityInt == 100 or probabilityInt is True:
            json: Dict[str, Union[float, str]] = {"outcome": "YES"}
        elif probabilityInt == 0 or probabilityInt is False:
            json = {"outcome": "NO"}
        else:
            json = {"outcome": "MKT", "probabilityInt": probabilityInt}

        response = requests.post(
            url=BASE_URI + "/market/" + market.id + "/resolve",
            json=json,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response

    def _resolve_pseudo_numeric_market(self, market, resolutionValue: Tuple[float, float]):
        json = {"outcome": "MKT", "value": resolutionValue[0], "probabilityInt": resolutionValue[1]}
        response = requests.post(
            url=BASE_URI + "/market/" + market.id + "/resolve",
            json=json,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response

    def _resolve_free_response_market(self, market, weights: Dict[int, float]):
        if len(weights) == 1:
            json: Dict[str, Any] = {"outcome": next(iter(weights))}
        else:
            total = sum(weights.values())
            json = {
                "outcome": "MKT",
                "resolutions": [
                    {"answer": index, "pct": 100 * weight / total}
                    for index, weight in weights.items()
                ]
            }
        response = requests.post(
            url=BASE_URI + "/market/" + market.id + "/resolve",
            json=json,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response

    _resolve_multiple_choice_market = _resolve_free_response_market

    def _resolve_numeric_market(self, market, number: float):
        raise NotImplementedError("TODO: I suspect the relevant docs are out of date")
