from brownie import accounts, web3, Wei, reverts, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *
from test_token_factory import _create_token

# reset the chain after every test case


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

# Crowdsale with a simple operator


@pytest.fixture(scope='module', autouse=True)
def crowdsale(Crowdsale, mintable_token):
    crowdsale = Crowdsale.deploy({"from": accounts[0]})
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS

    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    wallet = accounts[4]
    operator = accounts[0]

    mintable_token.approve(crowdsale, AUCTION_TOKENS, {"from": accounts[0]})
    crowdsale.initCrowdsale(
        accounts[0],
        mintable_token,
        ETH_ADDRESS,
        CROWDSALE_TOKENS,
        start_time,
        end_time,
        CROWDSALE_RATE,
        CROWDSALE_GOAL,
        operator,
        ZERO_ADDRESS,
        wallet,
        {"from": accounts[0]}
    )
    assert mintable_token.balanceOf(crowdsale) == AUCTION_TOKENS
    chain.sleep(10)
    return crowdsale


@pytest.fixture(scope='function')
def miso_helper(MISOHelper, miso_access_controls, token_factory, auction_factory, launcher, farm_factory):
    miso_helper = MISOHelper.deploy(miso_access_controls, token_factory, auction_factory, launcher, farm_factory, {"from": accounts[0]})

    return miso_helper


def test_getTokens(miso_helper, token_factory, fixed_token_template):

    name = "Helper Token"
    symbol = "HP"
    template_id = 1  # Fixed Token Template
    total_supply = 100 * TENPOW18
    integrator_account = accounts[1]

    _create_token(
        token_factory,
        fixed_token_template,
        name,
        symbol,
        total_supply,
        template_id,
        integrator_account,
        accounts[0]
    )

    _create_token(
        token_factory,
        fixed_token_template,
        name,
        symbol,
        total_supply,
        template_id,
        integrator_account,
        accounts[1]
    )

    tokens = miso_helper.getTokens()
    print("tokens:", tokens)


def test_getCrowdsaleInfo(miso_helper, crowdsale):
    crowdsale_info = miso_helper.getCrowdsaleInfo(crowdsale)
    print("crowdsale_info:", crowdsale_info)
    print("totalTokens:", crowdsale.marketInfo()[2])


@pytest.fixture(scope='function')
def fixed_token_cal(FixedToken):
    fixed_token_cal = FixedToken.deploy({'from': accounts[0]})
    name = "Fixed Token Cal"
    symbol = "CAL"
    owner = accounts[0]

    fixed_token_cal.initToken(name, symbol, owner,AUCTION_TOKENS, {'from': owner})
    assert fixed_token_cal.name() == name
    assert fixed_token_cal.symbol() == symbol
    # assert fixed_token_cal.owner() == owner
    # changed to access controls

    assert fixed_token_cal.totalSupply() == AUCTION_TOKENS
    assert fixed_token_cal.balanceOf(owner) == AUCTION_TOKENS

    return fixed_token_cal

def test_getMarkets(miso_helper, auction_factory, dutch_auction_template, fixed_token_cal):

    assert fixed_token_cal.balanceOf(accounts[0]) == AUCTION_TOKENS
    template_id = auction_factory.getTemplateId(dutch_auction_template)
    minimum_fee = 0.1 * TENPOW18
    integrator_fee_percent = 10
    ETH_TO_FEE = 1 * TENPOW18
    auction_factory.setMinimumFee(minimum_fee,{"from":accounts[0]})
    auction_factory.setIntegratorFeePct(integrator_fee_percent, {"from":accounts[0]})
    
    start_date = chain.time() + 20
    end_date = start_date + AUCTION_TIME
    operator = accounts[0]
    wallet = accounts[1]
    
    chain.sleep(10)
    
    fixed_token_cal.approve(auction_factory, AUCTION_TOKENS, {"from": accounts[0]})
    _data = dutch_auction_template.getAuctionInitData(
        auction_factory,
        fixed_token_cal,
        AUCTION_TOKENS,
        start_date,
        end_date,
        ETH_ADDRESS,
        AUCTION_START_PRICE,
        AUCTION_RESERVE,
        operator,
        ZERO_ADDRESS,
        wallet,
        {"from": accounts[0]}
    )
    
    
    tx = auction_factory.createMarket(template_id,fixed_token_cal,AUCTION_TOKENS,wallet, _data,{"from":accounts[0],"value": ETH_TO_FEE})
  
    markets = miso_helper.getMarkets()
    print("markets:", markets)
    

def test_getDutchAuctionInfo(miso_helper, dutch_auction):
    dutch_auction_info = miso_helper.getDutchAuctionInfo(dutch_auction)
    print("dutch_auction_info:", dutch_auction_info)


def test_getBatchAuctionInfo(miso_helper, batch_auction):
    batch_auction_info = miso_helper.getBatchAuctionInfo(batch_auction)
    print("batch_auction_info:", batch_auction_info)


def test_getHyperbolicAuctionInfo(miso_helper, hyperbolic_auction):
    hyperbolic_auction_info = miso_helper.getHyperbolicAuctionInfo(hyperbolic_auction)
    print("hyperbolic_auction_info:", hyperbolic_auction_info)
