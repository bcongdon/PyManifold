"""Contains the various types of data that Manifold can return."""

from __future__ import annotations

from dataclasses import dataclass, field
from inspect import signature
from typing import TYPE_CHECKING, Dict, Mapping, Sequence, Union

from .utils.math import prob_to_number_cpmm1

if TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime
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

    # Below methods are orignally from manifoldpy/api.py at commit 4b84f8cf7b4d26f02e82eec3c3309a830f65bf09
    # They were taken with permission, under the MIT License, under which this project is also licensed
    @property
    def num_traders(self) -> int:
        """Property which caches the number of unique traders in this market.

        Originally from manifoldpy/api.py, with permission, under the MIT License, under which this project is also
        licensed.
        """
        if not self.bets:
            return 0
        return len({b.userId for b in self.bets})

    def probability_history(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Return the probability/value history of this market as a pair of lockstep tuples."""
        if self.outcomeType == "BINARY":
            return self._binary_probability_history()
        elif self.outcomeType == "PSEUDO_NUMERIC":
            times, probabilities = self._binary_probability_history()
            assert self.min is not None
            assert self.max is not None
            values = (prob_to_number_cpmm1(prob, self.min, self.max, bool(self.isLogScale)) for prob in probabilities)
            return times, tuple(values)
        raise NotImplementedError()

    def _binary_probability_history(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Return the binary probability history of this market as a pair of lockstep tuples.

        Originally from manifoldpy/api.py, with permission, under the MIT License, under which this project is also
        licensed.
        """
        assert (
            self.bets is not None
        ), "Call get_market before accessing probability history"
        times: tuple[float, ...]
        probabilities: tuple[float, ...]
        if len(self.bets) == 0:
            times = (self.createdTime, )
            assert self.probability is not None
            probabilities = (self.probability, )
        else:
            s_bets = sorted(self.bets, key=lambda x: x.createdTime)
            start_prob = s_bets[0].probBefore
            assert start_prob is not None
            start_time = self.createdTime
            t_iter, p_iter = zip(*[(bet.createdTime, bet.probAfter) for bet in s_bets])
            times = (start_time, *t_iter)
            probabilities = (start_prob, *p_iter)
        return times, probabilities

    @property
    def start_probability(self) -> float:
        """Shortcut property that returns the first probability in this market.

        Originally from manifoldpy/api.py, with permission, under the MIT License, under which this project is also
        licensed.
        """
        return self.probability_history()[1][0]

    @property
    def final_probability(self) -> float:
        """Shortcut property that returns the most recent probability in this market.

        Originally from manifoldpy/api.py, with permission, under the MIT License, under which this project is also
        licensed.
        """
        return self.probability_history()[1][-1]

    def probability_at_time(self, timestamp: float, smooth: bool = False) -> float:
        """Return the probability at a given time, where time is represented as ms since origin.

        If smooth is true, then it will give you the weighted mean of the two nearest probabilities.

        Originally from manifoldpy/api.py, with permission, under the MIT License, under which this project is also
        licensed.
        """
        times, probs = self.probability_history()
        if timestamp <= times[0]:
            raise ValueError("Timestamp before market creation")
        elif timestamp >= times[-1]:
            return probs[-1]
        else:
            start_guess = 0
            end_guess = len(times)
            idx = end_guess // 2
            try:
                while not (times[idx - 1] <= timestamp < times[idx]):
                    if times[idx] >= timestamp:
                        start_guess = (start_guess + idx) // 2
                    else:
                        end_guess = (end_guess + idx) // 2
                    new_idx = (start_guess + end_guess) // 2
                    if new_idx == idx:
                        raise RuntimeError("Loop would have repeated")
                    idx = new_idx
            except IndexError:
                # this means that we fell off the edge of the probability map, so just return the nearest one
                if idx <= 0:
                    return probs[0]
                return probs[-1]
            if smooth:
                weight_1 = 1 / abs(timestamp - times[idx - 1])
                weight_2 = 1 / abs(timestamp - times[idx])
                total_weight = weight_1 + weight_2
                return (probs[idx - 1] * weight_1 + probs[idx] * weight_2) / total_weight
            return probs[idx - 1]

    # end section from manifoldpy
    def value_at_time(self, timestamp: float, smooth: bool = False) -> float:
        """Get the value at a given time.

        Note: if this is a binary market, this is the same thing as probability_at_time()
        """
        if self.outcomeType == "BINARY":
            return self.probability_at_time(timestamp, smooth)
        assert self.min is not None
        assert self.max is not None
        return prob_to_number_cpmm1(
            self.probability_at_time(timestamp, smooth),
            self.min,
            self.max,
            bool(self.isLogScale)
        )

    def probability_at_datetime(self, dt: datetime) -> float:
        """Translate your datetime into one that is Manifold-compatible."""
        return self.probability_at_time(dt.timestamp() * 1000)

    def value_at_datetime(self, dt: datetime) -> float:
        """Translate your datetime into one that is Manifold-compatible."""
        return self.value_at_time(dt.timestamp() * 1000)


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
