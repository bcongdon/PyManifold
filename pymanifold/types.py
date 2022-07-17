from dataclasses import dataclass
from typing import Dict, Optional, List
import inspect


class DictDeserializable:
    @classmethod
    def from_dict(cls, env):
        return cls(
            **{k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        )

@dataclass
class Bet(DictDeserializable):
    amount: int
    contractId: str
    createdTime: int
    id: str


@dataclass
class Comment(DictDeserializable):
    contractId: str
    createdTime: int
    id: str
    text: str

    userId: str
    userName: str
    userAvatarUrl: str
    userUsername: str


@dataclass
class LiteMarket(DictDeserializable):
    """Represents a lite market"""

    # Unique identifer for this market
    id: str

    # Attributes about the creator
    creatorUsername: str
    creatorName: str
    createdTime: int
    creatorAvatarUrl: Optional[str]

    # Market attributes. All times are in milliseconds since epoch
    closeTime: Optional[int]
    question: str
    description: str
    tags: List[str]

    outcomeType: str  # BINARY, FREE_RESPONSE, or NUMERIC
    pool: float
    volume7Days: float
    volume24Hours: float
    isResolved: bool
    probability: Optional[float] = None
    resolutionTime: Optional[int] = None
    resolution: Optional[str] = None

    # This should not be optional, once market creation returns the URL in the response.
    # https://github.com/manifoldmarkets/manifold/issues/508
    url: Optional[str] = None


@dataclass
class Market(LiteMarket):
    """Represents a market"""

    bets: List[Bet] = None
    comments: List[Comment] = None
    answers: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, env):
        market = super(Market, cls).from_dict(env)
        market.bets = [Bet.from_dict(bet) for bet in env["bets"]]
        market.comments = [Comment.from_dict(bet) for bet in env["comments"]]
        return market
