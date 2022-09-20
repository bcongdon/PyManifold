from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, List, Type, TypeVar
import inspect

T = TypeVar("T")


class DictDeserializable:
    """An object which can be deserialized from a known dictionary spec."""

    @classmethod
    def from_dict(cls: Type[T], env: Dict[str, Any]) -> T:
        """Take a dictionary and return an instance of the associated class."""
        return cls(
            **{k: v for k, v in env.items() if k in inspect.signature(cls).parameters}  # type: ignore
        )


@dataclass
class Bet(DictDeserializable):
    """Represents a bet."""

    amount: int
    contractId: str
    createdTime: int
    id: str


@dataclass
class Comment(DictDeserializable):
    """Represents a comment."""

    contractId: str
    createdTime: int
    id: str
    text: str = ""

    userId: str = ""
    userName: str = ""
    userAvatarUrl: str = ""
    userUsername: str = ""


@dataclass
class LiteMarket(DictDeserializable):
    """Represents a lite market."""

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
    # description: str
    tags: List[str]

    outcomeType: str  # BINARY, FREE_RESPONSE, NUMERIC, or PSEUDO_NUMERIC
    pool: float
    volume7Days: float
    volume24Hours: float
    isResolved: bool
    description: str = ""
    probability: Optional[float] = None
    resolutionTime: Optional[int] = None
    resolution: Optional[str] = None

    p: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    isLogScale: Optional[bool] = None

    # This should not be optional, once market creation returns the URL in the response.
    # https://github.com/manifoldmarkets/manifold/issues/508
    url: Optional[str] = None


@dataclass
class Market(LiteMarket):
    """Represents a market."""

    bets: List[Bet] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    answers: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, env):
        """Take a dictionary and return an instance of the associated class."""
        market = super(Market, cls).from_dict(env)
        market.bets = [Bet.from_dict(bet) for bet in env["bets"]]
        market.comments = [Comment.from_dict(bet) for bet in env["comments"]]
        return market


@dataclass
class Group(DictDeserializable):
    """Represents a group."""

    name: str = ""
    creatorId: str = ""
    id: str = ""
    contractIds: List[str] = field(default_factory=list)
    mostRecentActivityTime: int = -1
    anyoneCanJoin: bool = False
    mostRecentContractAddedTime: int = -1
    createdTime: int = -1
    memberIds: List[str] = field(default_factory=list)
    slug: str = ""
    about: str = ""

    def contracts(self, client) -> Iterable[Market]:
        """Iterate over the markets in this group."""
        return (client.get_market_by_id(id_) for id_ in self.contractIds)

    def members(self, client) -> Iterable["LiteUser"]:
        """Iterate over the users in this group."""
        return (client.get_user_by_id(id_) for id_ in self.memberIds)


class LiteUser(DictDeserializable):
    """Basic information about a user."""

    id: str  # user's unique id
    createdTime: float  # as usual, in ms since epoch

    name: str  # display name, may contain spaces
    username: str  # username, used in urls
    url: str  # link to user's profile
    avatarUrl: Optional[str] = None

    bio: Optional[str] = None
    bannerUrl: Optional[str] = None
    website: Optional[str] = None
    twitterHandle: Optional[str] = None
    discordHandle: Optional[str] = None

    # Note: the following are here for convenience only and may be removed in the future.
    balance: float = 0.0
    totalDeposits: float = 0.0
    totalPnLCached: float = 0.0
    creatorVolumeCached: float = 0.0
