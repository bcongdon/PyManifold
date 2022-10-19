"""Contains the various types of data that Manifold can return."""

from __future__ import annotations

from dataclasses import dataclass, field
from inspect import signature
from typing import TYPE_CHECKING, Dict, Mapping, Sequence, Union

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable, List, Literal, Optional, Type, TypeVar

    from .lib import ManifoldClient

    T = TypeVar("T")

# To check with mypy, pass in `--enable-recursive-aliases`
JSONType = Union[int, float, bool, str, None, Sequence['JSONType'], Mapping[str, 'JSONType']]
JSONDict = Dict[str, JSONType]


class DictDeserializable:
    """An object which can be deserialized from a known dictionary spec."""

    @classmethod
    def from_dict(cls: Type[T], env: JSONDict) -> T:
        """Take a dictionary and return an instance of the associated class."""
        return cls(
            **{k: v for k, v in env.items() if k in signature(cls).parameters}  # type: ignore
        )


@dataclass
class Bet(DictDeserializable):
    """Represents a bet."""

    amount: int
    contractId: str
    createdTime: int
    id: str

    loanAmount: int | None = None
    userId: str | None = None
    userAvatarUrl: str | None = None
    userUsername: str | None = None
    userName: str | None = None

    orderAmount: int | None = None
    isCancelled: bool = False
    isFilled: bool = True
    fills: list[dict[str, float | str | None]] | None = None
    fees: dict[str, float] | None = None

    probBefore: float | None = None
    probAfter: float | None = None


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

    outcomeType: Literal["BINARY", "FREE_RESPONSE", "NUMERIC", "PSEUDO_NUMERIC", "MULTIPLE_CHOICE"]
    pool: float | Mapping[str, float] | None
    volume7Days: float
    volume24Hours: float
    isResolved: bool
    description: str = ""
    lastUpdatedTime: Optional[int] = None
    probability: Optional[float] = None
    resolutionTime: Optional[int] = None
    resolution: Optional[str] = None
    resolutionProbability: Optional[float] = None

    p: Optional[float] = None
    totalLiquidity: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    isLogScale: Optional[bool] = None

    # This should not be optional, once market creation returns the URL in the response.
    # https://github.com/manifoldmarkets/manifold/issues/508
    url: Optional[str] = None

    @property
    def slug(self) -> str:
        """Generate the slug of a market, given it has an assigned URL."""
        if self.url is None:
            raise ValueError("No url set")
        return self.url.split("/")[-1]


@dataclass
class Market(LiteMarket):
    """Represents a market."""

    bets: List[Bet] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    answers: Optional[List[Dict[str, Union[str, float]]]] = None

    @classmethod
    def from_dict(cls, env: JSONDict) -> 'Market':
        """Take a dictionary and return an instance of the associated class."""
        market = super(Market, cls).from_dict(env)
        bets: Sequence[JSONDict] = env['bets']  # type: ignore[assignment]
        comments: Sequence[JSONDict] = env['comments']  # type: ignore[assignment]
        market.bets = [Bet.from_dict(bet) for bet in bets]
        market.comments = [Comment.from_dict(bet) for bet in comments]
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

    def contracts(self, client: 'ManifoldClient') -> Iterable[Market]:
        """Iterate over the markets in this group."""
        return (client.get_market_by_id(id_) for id_ in self.contractIds)

    def members(self, client: 'ManifoldClient') -> Iterable["LiteUser"]:
        """Iterate over the users in this group."""
        return (client.get_user(id_) for id_ in self.memberIds)


@dataclass
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
