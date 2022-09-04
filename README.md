# PyManifold

Python API client for [Manifold Markets](https://manifold.markets).

This is still a work in progress.

## Usage

```python
from pymanifold import ManifoldClient

# List markets
client = ManifoldClient()
markets = client.list_markets()

# Get market by slug
slug = "will-bitcoins-price-fall-below-25k"
market = client.get_market_by_slug("will-bitcoins-price-fall-below-25k")

# Get market by id
id = "rIR6mWqaO9xKLifr6cLL"
market = client.get_market_by_id(id)

# Create a bet
betId = client.create_bet(contractId="BxFQCoaaxBqRcnzJb1mV", amount=1, outcome="NO")

# Create a market
client = ManifoldClient(api_key=API_KEY)
market = client.create_binary_market(
    question="Testing Binary Market creation through API",
    initialProb=99,
    description="Going to resolves as N/A",
    tags=["fun"],
    closeTime=4102444800000,
)

# Find optimal Kelly bet
from pymanifold.utils import kelly_calc

market = client.get_market_by_slug("for-this-study-published-in-nature")
utils.kelly_calc(
     market = market
     subjective_probability = 0.8
     balance = 800
     initial_market_probability = 0.5
)

```

## TODO

- [ ] Publish a version of this package to PyPI
- [ ] Add instructions for running tests that require an API key (e.g. setting the `MANIFOLD_API_KEY` environment variable)
- [ ] Generalize `kelly_bet` to correlated markets

## Running Tests

```sh
$ poetry run pytest
```
