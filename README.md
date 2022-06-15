# PyManifold

Python API client for [Manifold Markets](https://manifold.markets).

This is still a work in progress.

## Usage

```python
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
market = client.create_market(
    outcomeType="BINARY",
    question="Testing Binary Market creation through API",
    initialProb=99,
    description="Going to resolves as N/A",
    tags=["fun"],
    closeTime=4102444800000,
)
```

## TODO

- [ ] Create test for betting on a free response market
- [ ] Create tests for creating a free response market
- [ ] Create test for creating a numeric market
- [ ] Publish a version of this package to PyPI
- [ ] Setup CI to run tests against PRs
- [ ] Add instructions for running tests that require an API key (e.g. setting the `MANIFOLD_API_KEY` environment variable)

## Running Tests

```sh
$ poetry run pytest
```
