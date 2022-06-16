from pymanifold import __version__, ManifoldClient
from pymanifold.types import LiteMarket, Market
import vcr
import os

API_KEY = os.getenv("MANIFOLD_API_KEY", "fake_api_key")

manifold_vcr = vcr.VCR(
    cassette_library_dir="tests/fixtures/cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    filter_headers=["authorization"],
)


def test_version():
    assert __version__ == "0.1.0"


@manifold_vcr.use_cassette()
def test_list_markets():
    client = ManifoldClient()
    markets = client.list_markets()

    for m in markets:
        assert m.closeTime > 0
        assert m.url
        assert m.id


@manifold_vcr.use_cassette()
def test_get_market_by_slug():
    client = ManifoldClient()

    slug = "will-bitcoins-price-fall-below-25k"
    market = client.get_market_by_slug("will-bitcoins-price-fall-below-25k")
    assert market.id == "rIR6mWqaO9xKLifr6cLL"
    assert market.url == "https://manifold.markets/bcongdon/" + slug
    validate_market(market)


@manifold_vcr.use_cassette()
def test_get_market_by_id():
    client = ManifoldClient()

    id = "rIR6mWqaO9xKLifr6cLL"
    market = client.get_market_by_id(id)
    assert market.id == id
    assert (
        market.url
        == "https://manifold.markets/bcongdon/will-bitcoins-price-fall-below-25k"
    )
    assert len(market.bets) == 49
    assert len(market.comments) == 5
    validate_market(market)


@manifold_vcr.use_cassette()
def test_create_bet_binary():
    client = ManifoldClient(api_key=API_KEY)
    betId = client.create_bet(contractId="BxFQCoaaxBqRcnzJb1mV", amount=1, outcome="NO")
    assert betId == "ZhwL5DngCKdrZ7TQQFad"


@manifold_vcr.use_cassette()
def test_create_bet_free_response():
    client = ManifoldClient(api_key=API_KEY)
    betId = client.create_bet(contractId="Hbeirep6H6GXHFNiX6M1", amount=1, outcome="4")
    assert betId == "8qgMoiHYfQlvkuyd3NRa"


@manifold_vcr.use_cassette()
def test_create_market_binary():
    client = ManifoldClient(api_key=API_KEY)
    market = client.create_market(
        outcomeType="BINARY",
        question="Testing Binary Market creation through API",
        initialProb=99,
        description="Going to resolves as N/A",
        tags=["fun"],
        closeTime=4102444800000,
    )


@manifold_vcr.use_cassette()
def test_create_market_binary():
    client = ManifoldClient(api_key=API_KEY)
    market = client.create_market(
        outcomeType="BINARY",
        question="Testing Binary Market creation through API",
        initialProb=99,
        description="Going to resolves as N/A",
        tags=["fun"],
        closeTime=4102444800000,
    )
    validate_lite_market(market)


def validate_lite_market(market: LiteMarket):
    assert market.id
    assert market.creatorUsername
    assert market.question
    assert market.description


def validate_market(market: Market):
    validate_lite_market(market)

    for b in market.bets:
        assert b.id
        assert b.amount != 0

    for c in market.comments:
        assert c.id
        assert c.contractId
        assert c.text
        assert c.userAvatarUrl
        assert c.userId
        assert c.userName
        assert c.userUsername
