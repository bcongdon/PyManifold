import requests
import numpy as np

from typing import Optional, List

from .types import Market, LiteMarket

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

    def create_free_response_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
    ):
        """
        Create a free response market
        """
        return self._create_market(
            "FREE_RESPONSE", question, description, closeTime, tags
        )

    def create_numeric_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        minValue: int,
        maxValue: int,
        tags: Optional[List[str]] = None,
    ):
        """
        Create a numeric market
        """
        return self._create_market(
            "NUMERIC",
            question,
            description,
            closeTime,
            tags,
            minValue=minValue,
            maxValue=maxValue,
        )

    def create_binary_market(
        self,
        question: str,
        description: str,
        closeTime: int,
        tags: Optional[List[str]] = None,
        initialProb: Optional[int] = 50,
    ):
        """
        Create a binary market
        """
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
            data["min"] = minValue
            data["max"] = maxValue
        else:
            raise Exception(
                "Invalid outcome type. Outcome should be one of: BINARY, FREE_RESPONSE, NUMERIC"
            )

        response = requests.post(
            url=BASE_URI + "/market",
            json=data,
            headers=self._auth_headers(),
        )
        return LiteMarket.from_dict(response.json())
    
    def kelly_calc(self, market, subjective_probability, balance):
        """For a given binary market, find the bet that maximises expected log wealth."""
        
        def shares_bought(pool, bet, outcome, p=0.5):
            """Figure out the number of shares a given purchace yields. Returns the number of shares and the resulting pool.
            This function assumes Manifold Markets are using 'Maniswap' as their Automated Market Maker. More on Maniswap
            can be found here: 'https://manifoldmarkets.notion.site/Maniswap-ce406e1e897d417cbd491071ea8a0c39'."""

            y = pool['YES']
            n = pool['NO']

            k = y**p * n**(1-p)

            y += bet
            n += bet

            k2 = y**p * n**(1-p)

            if outcome == "YES":
                y2 = (k / n**(1-p))**(1/p)

                y -= y2
                shares_without_fees = y

                post_bet_probability = p*n / (p*n + (1-p)*y2)

                fee = 0.1 * (1 - post_bet_probability) * bet

                shares_after_fees = shares_without_fees - fee

                pool = {'YES': y2, 'NO': n}

                return shares_after_fees, pool

            elif outcome == "NO":
                n2 = (k / y**p)**(1/(1-p))

                n -= n2
                shares_without_fees = n

                post_bet_probability = p*n2 / (p*n2 + (1-p)*y)

                fee = 0.1 * post_bet_probability * bet

                shares_after_fees = shares_without_fees - fee

                pool = {'YES': y, 'NO': n2}

                return shares_after_fees, pool

            else:
                return "ERROR: Please give a valid outcome"
        
        
        def expected_log_wealth(balance, p, bet, outcome, pool, initial_market_probability):
            """Calculate the expected log wealth for a hypothetical bet"""
            if outcome == 'YES':
                E = p * np.log(balance - bet + shares_bought(pool, bet, outcome, initial_market_probability)[0]) + (1-p) * np.log(balance - bet)

            elif outcome == 'NO':
                E = (1-p) * np.log(balance - bet + shares_bought(pool, bet, outcome, initial_market_probability)[0]) + p * np.log(balance - bet)

            return E

        # find the probability the market was initialised at
        initial_market_probability = market.bets[0]['probBefore']
        
        pool = market.pool

        if subjective_probability == market.probability:
            outcome = 'Error: subjective probability matches market probability.'
            return 0, outcome

        elif subjective_probability > market.probability:
            outcome = 'YES'

        elif subjective_probability < market.probability:
            outcome = 'NO'

        kelly_bet = np.argmax([expected_log_wealth(balance, subjective_probability, bet, outcome, pool, initial_market_probability) for bet in range(balance)])

        return kelly_bet, outcome
