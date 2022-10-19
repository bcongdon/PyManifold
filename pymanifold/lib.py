"""Contains the client interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, cast, overload

import requests

from .types import Bet, Group, JSONDict, LiteMarket, LiteUser, Market
from .utils.math import number_to_prob_cpmm1

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable, List, Literal, Optional, Sequence, Union

BASE_URI = "https://manifold.markets/api/v0"


class ManifoldClient:
    """A client for interacting with the website manifold.markets."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize a Manifold client, optionally with an API key."""
        self.api_key = api_key

    def list_markets(
        self, limit: Optional[int] = None, before: Optional[str] = None
    ) -> List[LiteMarket]:
        """List all markets."""
        return list(self.get_markets(limit, before))

    def get_markets(
        self, limit: Optional[int] = None, before: Optional[str] = None
    ) -> Iterable[LiteMarket]:
        """Iterate over all markets."""
        response = requests.get(
            url=BASE_URI + "/markets", params={"limit": limit, "before": before}
        )
        return (LiteMarket.from_dict(market) for market in response.json())

    def list_groups(self, availableToUserId: Optional[str] = None) -> List[Group]:
        """List all markets."""
        return list(self.get_groups(availableToUserId))

    def get_groups(self, availableToUserId: Optional[str] = None) -> Iterable[Group]:
        """Iterate over all markets."""
        response = requests.get(
            url=BASE_URI + "/groups", params={"availableToUserId": availableToUserId}
        )
        return (Group.from_dict(group) for group in response.json())

    def get_group(self, slug: Optional[str] = None, id_: Optional[str] = None) -> Group:
        """Iterate over all markets."""
        if id_ is not None:
            response = requests.get(url=BASE_URI + "/group/by-id/" + id_)
        elif slug is not None:
            response = requests.get(url=BASE_URI + "/group/" + slug)
        else:
            raise ValueError("Requires one or more of (slug, id_)")
        return Group.from_dict(response.json())

    def list_bets(
        self,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        username: Optional[str] = None,
        market: Optional[str] = None,
    ) -> List[Bet]:
        """List all bets."""
        return list(self.get_bets(limit, before, username, market))

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

    def get_market_by_id(self, market_id: str) -> Market:
        """Get a market by id."""
        return Market.from_dict(self._get_market_by_id_raw(market_id))

    def _get_market_by_id_raw(self, market_id: str) -> JSONDict:
        """Get a market by id."""
        response = requests.get(url=BASE_URI + "/market/" + market_id)
        return cast(JSONDict, response.json())

    def get_market_by_slug(self, slug: str) -> Market:
        """Get a market by slug."""
        return Market.from_dict(self._get_market_by_slug_raw(slug))

    def _get_market_by_slug_raw(self, slug: str) -> JSONDict:
        """Get a market by slug."""
        response = requests.get(url=BASE_URI + "/slug/" + slug)
        return cast(JSONDict, response.json())

    def get_market_by_url(self, url: str) -> Market:
        """Get a market by url."""
        return Market.from_dict(self._get_market_by_url_raw(url))

    def _get_market_by_url_raw(self, url: str) -> JSONDict:
        """Get a market by url."""
        slug = url.split("/")[-1].split("#")[0]
        response = requests.get(url=BASE_URI + "/slug/" + slug)
        return cast(JSONDict, response.json())

    def get_user(self, handle: str) -> LiteUser:
        """Get a user by handle."""
        return LiteUser.from_dict(self._get_user_raw(handle))

    def _get_user_raw(self, handle: str) -> JSONDict:
        response = requests.get(url=BASE_URI + "/user/" + handle)
        return cast(JSONDict, response.json())

    def _auth_headers(self) -> dict[str, str]:
        if self.api_key:
            return {"Authorization": "Key " + self.api_key}
        else:
            raise RuntimeError("No API key provided")

    def cancel_market(self, market: Union[LiteMarket, str]) -> requests.Response:
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
        return cast(str, response.json()["betId"])

    def create_free_response_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
    ) -> LiteMarket:
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
    ) -> LiteMarket:
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
    ) -> LiteMarket:
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
    ) -> LiteMarket:
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
    ) -> LiteMarket:
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
            # Sometimes when there is a serverside error the market is still posted
            # We want to make sure we still return it in those instances
            for mkt in self.list_markets():
                if (question, outcomeType, closeTime) == (mkt.question, mkt.outcomeType, mkt.closeTime):
                    return mkt
        return LiteMarket.from_dict(response.json())

    def resolve_market(self, market: Union[LiteMarket, str], *args: Any, **kwargs: Any) -> requests.Response:
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
        else:  # pragma: no cover
            raise NotImplementedError()

    def _resolve_binary_market(self, market: LiteMarket, probabilityInt: float) -> requests.Response:
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

    def _resolve_pseudo_numeric_market(
        self, market: LiteMarket, resolutionValue: float
    ) -> requests.Response:
        assert market.min is not None
        assert market.max is not None
        prob = 100 * number_to_prob_cpmm1(resolutionValue, market.min, market.max, bool(market.isLogScale))
        json = {"outcome": "MKT", "value": resolutionValue, "probabilityInt": prob}
        response = requests.post(
            url=BASE_URI + "/market/" + market.id + "/resolve",
            json=json,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response

    def _resolve_free_response_market(self, market: LiteMarket, weights: Dict[int, float]) -> requests.Response:
        if len(weights) == 1:
            json: JSONDict = {"outcome": next(iter(weights))}
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

    def _resolve_numeric_market(self, market: LiteMarket, number: float) -> requests.Response:
        raise NotImplementedError("TODO: I suspect the relevant docs are out of date")

    @overload
    def create_comment(
        self, market: LiteMarket | str, comment: str, mode: Literal['markdown', 'html']
    ) -> requests.Response:
        ...

    @overload
    def create_comment(
        self, market: LiteMarket | str, comment: JSONDict, mode: Literal['tiptap']
    ) -> requests.Response:
        ...

    def create_comment(
        self, market: LiteMarket | str, comment: str | JSONDict, mode: str
    ) -> requests.Response:
        """Create a comment on a given market, using Markdown, HTML, or TipTap formatting."""
        if isinstance(market, LiteMarket):
            market = market.id
        data: JSONDict = {'contractId': market}
        if mode == 'tiptap':
            data['content'] = comment
        elif mode == 'html':
            data['html'] = comment
        elif mode == 'markdown':
            data['markdown'] = comment
        else:
            raise ValueError("Invalid format mode")
        response = requests.post(
            url=BASE_URI + "/comment",
            json=data,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response
