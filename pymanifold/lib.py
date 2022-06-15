from argparse import ArgumentError
import requests
import json
from typing import Optional, List

from .types import Market, LiteMarket, Bet

BASE_URI = "https://manifold.markets/api/v0"


class ManifoldClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def list_markets(
        self, limit: Optional[int] = None, before: Optional[str] = None
    ) -> List[LiteMarket]:
        """
        List all markets
        """
        response = requests.get(
            url=BASE_URI + "/markets", params={"limit": limit, "before": before}
        )
        return [LiteMarket.from_dict(market) for market in response.json()]

    def get_market_by_id(self, market_id: str) -> Market:
        """
        Get a market by id
        """
        response = requests.get(url=BASE_URI + "/market/" + market_id)
        return Market.from_dict(response.json())

    def get_market_by_slug(self, slug: str) -> Market:
        """
        Get a market by slug
        """
        response = requests.get(url=BASE_URI + "/slug/" + slug)
        return Market.from_dict(response.json())

    def _auth_headers(self) -> dict:
        if self.api_key:
            return {"Authorization": "Key " + self.api_key}
        else:
            raise RuntimeError("No API key provided")

    def create_bet(self, contractId: str, amount: int, outcome: str) -> str:
        """
        Place a bet

        Returns the ID of the created bet.
        """
        response = requests.post(
            url=BASE_URI + "/bet",
            json={
                "amount": int(amount),
                "contractId": contractId,
                "outcome": outcome,
            },
            headers=self._auth_headers(),
        )
        return response.json()["betId"]

    def create_market(
        self,
        outcomeType: str,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
        initialProb: Optional[int] = 50,
        minValue: Optional[int] = None,
        maxValue: Optional[int] = None,
    ):
        """
        Create a market
        """

        data = {
            "outcomeType": outcomeType,
            "question": question,
            "description": description,
            "closeTime": closeTime,
            "tags": tags,
        }
        if outcomeType == "BINARY":
            data["initialProb"] = initialProb
        elif outcomeType == "FREE_RESPONSE":
            pass
        elif outcomeType == "NUMERIC":
            data["minValue"] = minValue
            data["maxValue"] = maxValue
        else:
            raise Exception("Invalid outcome type")

        response = requests.post(
            url=BASE_URI + "/market",
            json=data,
            headers=self._auth_headers(),
        )
        return LiteMarket.from_dict(response.json())
