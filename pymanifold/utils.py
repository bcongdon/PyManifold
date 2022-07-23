from numpy import log as ln, argmax

def kelly_calc(market, subjective_prob, balance):
    """For a given binary market, find the bet that maximises expected log wealth."""

    def shares_bought(market, bet, outcome):
        """Figure out the number of shares a given purchace yields. Returns the number of shares and the resulting pool.
        This function assumes Manifold Markets are using 'Maniswap' as their Automated Market Maker. More on Maniswap
        can be found here: 'https://manifoldmarkets.notion.site/Maniswap-ce406e1e897d417cbd491071ea8a0c39'."""

        # find the probability the market was initialised at
        p = market.bets[0]['probBefore']

        # find the current liquidity pool
        pool = market.pool

        y = pool['YES']
        n = pool['NO']

        # implement Maniswap
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


    def expected_log_wealth(market, sub_prob, bet, outcome, balance):
        """Calculate the expected log wealth for a hypothetical bet"""
        p = sub_prob

        if outcome == 'YES':
            E = p * ln(balance - bet + shares_bought(market, bet, outcome)[0]) + (1-p) * ln(balance - bet)

        elif outcome == 'NO':
            E = (1-p) * ln(balance - bet + shares_bought(market, bet, outcome)[0]) + p * ln(balance - bet)

        return E

    # figure out which option to buy
    outcome = ['YES', 'NO'][subjective_prob <= market.probability]

    # find the kelly bet
    kelly_bet = argmax([expected_log_wealth(market, subjective_prob, bet, outcome, balance) for bet in range(balance)])

    return kelly_bet, outcome
