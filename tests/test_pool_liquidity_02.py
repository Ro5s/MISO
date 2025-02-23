import pytest
from brownie import accounts, web3, Wei, reverts, chain
from brownie.convert import to_address
from settings import *

# reset the chain after every test case
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture(scope='function')
def token_1(MintableToken):
    token_1 = MintableToken.deploy({'from': accounts[0]})

    name = "Token1"
    symbol = "TOK1"
    owner = accounts[0]

    token_1.initToken(name, symbol, owner, 0, {'from': owner})

    return token_1

@pytest.fixture(scope='function')
def token_2(MintableToken):
    token_2 = MintableToken.deploy({'from': accounts[0]})

    name = "Token1"
    symbol = "TOK1"
    owner = accounts[0]

    token_2.initToken(name, symbol, owner, 0, {'from': owner})

    return token_2


@pytest.fixture(scope='function')
def pool_liquidity_02(PoolLiquidity02, public_access_controls, token_1, token_2, uniswap_factory):

    deadline = chain.time() + POOL_LAUNCH_DEADLINE
    launch_window = POOL_LAUNCH_WINDOW
    locktime = POOL_LAUNCH_LOCKTIME
    liquidity_percent = POOL_LIQUIDITY_PERCENT
    is_token1_weth = False
    pool_liquidity = PoolLiquidity02.deploy({"from": accounts[0]})
    pool_liquidity.initPoolLiquidity(public_access_controls, 
    token_1, token_2, uniswap_factory, 
    accounts[0], accounts[0], liquidity_percent, deadline, launch_window, locktime, is_token1_weth)

    return pool_liquidity


@pytest.fixture(scope='function')
def deposit_token1(pool_liquidity_02, token_1):
    assert token_1.balance() == 0
    token_1.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})
    assert token_1.balanceOf(accounts[0]) == TOKENS_TO_MINT

    deposit_amount = TOKENS_TO_MINT
    token_1.approve(pool_liquidity_02, deposit_amount, {"from": accounts[0]})
    tx = pool_liquidity_02.depositToken1(deposit_amount, {"from": accounts[0]})
    assert "Transfer" in tx.events
    assert pool_liquidity_02.getToken1Balance() == deposit_amount

@pytest.fixture(scope='function')
def deposit_token2(pool_liquidity_02, token_2):
    assert token_2.balance() == 0
    token_2.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})
    assert token_2.balanceOf(accounts[0]) == TOKENS_TO_MINT

    deposit_amount = TOKENS_TO_MINT
    token_2.approve(pool_liquidity_02, deposit_amount, {"from": accounts[0]})
    tx = pool_liquidity_02.depositToken2(deposit_amount, {"from": accounts[0]})
    assert "Transfer" in tx.events
    assert pool_liquidity_02.getToken2Balance() == deposit_amount

@pytest.fixture(scope='function')
def launch_liquidity_pool(UniswapV2Pair, UniswapV2Factory, pool_liquidity_02, token_1, token_2, deposit_token1, deposit_token2):
    chain.sleep(POOL_LAUNCH_DEADLINE+1)
    tx = pool_liquidity_02.launchLiquidityPool({"from": accounts[0]})

    assert "LiquidityAdded" in tx.events
    assert pool_liquidity_02.getToken1Balance() == 0
    assert pool_liquidity_02.getToken2Balance() == 0

    token_pair = UniswapV2Pair.at(pool_liquidity_02.tokenPair())
    assert token_1.balanceOf(token_pair) == TOKENS_TO_MINT
    assert token_2.balanceOf(token_pair) == TOKENS_TO_MINT

def _finalize_market_and_launch_lp(pool_liquidity_02, operator):
    pool_liquidity_02.finalizeMarketAndLaunchLiquidityPool({"from": operator})


def test_launchPoolWithoutAnyDeposits(pool_liquidity):
    chain.sleep(POOL_LAUNCH_DEADLINE+1)
    ret_value = pool_liquidity.launchLiquidityPool({"from": accounts[0]}).return_value
    assert ret_value == 0

def test_launchLiquidityPoolFromNotOperator(pool_liquidity_02, deposit_token1, deposit_token2):
    with reverts():
        pool_liquidity_02.launchLiquidityPool({"from": accounts[1]})

def test_depositTokensAfterContractExpired(pool_liquidity_02, token_1, token_2):
    chain.sleep(POOL_LAUNCH_DEADLINE + POOL_LAUNCH_WINDOW)

    token_1.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})

    deposit_amount = TOKENS_TO_MINT
    token_1.approve(pool_liquidity_02, deposit_amount, {"from": accounts[0]})
    with reverts("PoolLiquidity02: Contract has expired"):    
        pool_liquidity_02.depositToken1(deposit_amount, {"from": accounts[0]})

    token_2.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})

    token_2.approve(pool_liquidity_02, deposit_amount, {"from": accounts[0]})
    with reverts("PoolLiquidity02: Contract has expired"):    
        pool_liquidity_02.depositToken2(deposit_amount, {"from": accounts[0]})

def test_initPoolLiquidityAgain(pool_liquidity_02, public_access_controls, token_1, token_2, uniswap_factory):
    deadline = chain.time() + POOL_LAUNCH_DEADLINE
    launch_window = POOL_LAUNCH_WINDOW
    liquidity_percent = POOL_LIQUIDITY_PERCENT
    is_token1_weth = False
    locktime = POOL_LAUNCH_LOCKTIME
    with reverts():
        pool_liquidity_02.initPoolLiquidity(public_access_controls, token_1, token_2, uniswap_factory, accounts[0], accounts[0], liquidity_percent, deadline, launch_window, locktime, is_token1_weth)

def test_initPoolLiquidityIncorrectLocktime(pool_liquidity_02, public_access_controls, token_1, token_2, uniswap_factory):
    deadline = chain.time() + POOL_LAUNCH_DEADLINE
    launch_window = POOL_LAUNCH_WINDOW
    liquidity_percent = POOL_LIQUIDITY_PERCENT
    is_token1_weth = False
    locktime = 100000000000
    with reverts("PoolLiquidity02: Enter an unix timestamp in seconds, not miliseconds"):
        pool_liquidity_02.initPoolLiquidity(public_access_controls, token_1, token_2, uniswap_factory, accounts[0], accounts[0], liquidity_percent, deadline, launch_window, locktime, is_token1_weth)

# def test_zapEth(pool_liquidity, weth_token, UniswapV2Pair, mintable_token, launchLiquidityPool):
#     # mintable_token.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})
#     # mintable_token.approve(pool_liquidity, TOKENS_TO_MINT, {"from": accounts[0]})
#     # tokenPair = UniswapV2Pair.at(pool_liquidity.tokenWETHPair())

#     tx = pool_liquidity.zapEth({"from": accounts[0], "value": 1*TENPOW18})
#     assert "LiquidityAdded" in tx.events

# def test_zapEthWithoutPool(pool_liquidity, weth_token, UniswapV2Pair, mintable_token):
#     mintable_token.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})
#     mintable_token.approve(pool_liquidity, TOKENS_TO_MINT, {"from": accounts[0]})

#     with reverts("Liquidity is not added to pool"):
#         pool_liquidity.zapEth({"from": accounts[0], "value": 1*TENPOW18})

# def test_zapEthAfterUnlockTimeExpired(pool_liquidity, weth_token, UniswapV2Pair, mintable_token, launchLiquidityPool):
#     mintable_token.mint(accounts[0], TOKENS_TO_MINT, {'from': accounts[0]})
#     mintable_token.approve(pool_liquidity, TOKENS_TO_MINT, {"from": accounts[0]})
#     chain.sleep(pool_liquidity.locktime())

#     with reverts("The unlock time is passed"):
#         pool_liquidity.zapEth({"from": accounts[0], "value": 1*TENPOW18})

def test_withdrawDepositsWithoutExpiration(pool_liquidity_02, deposit_token1, deposit_token2):
    with reverts("PoolLiquidity02: Timer has not yet expired"):
        pool_liquidity_02.withdrawDeposits({"from": accounts[0]})

def test_withdrawLPTokens(pool_liquidity_02, UniswapV2Pair, launch_liquidity_pool):
    chain.sleep(pool_liquidity_02.locktime())
    wallet = pool_liquidity_02.wallet()
    tokenPair = UniswapV2Pair.at(pool_liquidity_02.tokenPair())
    walletLPBalanceBeforeW = tokenPair.balanceOf(wallet)
    poolLiquidityBalanceBeforeW = tokenPair.balanceOf(pool_liquidity_02)
    
    tx = pool_liquidity_02.withdrawLPTokens({"from": accounts[0]})
    withdrawnLiquidity = tx.return_value

    assert poolLiquidityBalanceBeforeW - withdrawnLiquidity == tokenPair.balanceOf(pool_liquidity_02)
    assert walletLPBalanceBeforeW + withdrawnLiquidity == tokenPair.balanceOf(wallet)

def test_withdrawLPTokensWithLiquidityLocked(pool_liquidity_02, launch_liquidity_pool):
    with reverts("PoolLiquidity02: Liquidity is locked"):
        pool_liquidity_02.withdrawLPTokens({"from": accounts[0]})

def test_withdrawLPTokensWithoutLiquidity(pool_liquidity_02):
    chain.sleep(pool_liquidity_02.locktime())

    with reverts("PoolLiquidity02: Liquidity must be greater than 0"):
        pool_liquidity_02.withdrawLPTokens({"from": accounts[0]})

def test_withdrawLPTokensWrongOperator(pool_liquidity_02):
    with reverts("PoolLiquidity02: Sender must be operator"):
        pool_liquidity_02.withdrawLPTokens({"from": accounts[5]})

# TODO - uncomment
def test_launchLiquidityPoolAfterContractExpires(pool_liquidity_02, deposit_token1, deposit_token2):
    chain.sleep(POOL_LAUNCH_WINDOW)
    with reverts():
        pool_liquidity_02.launchLiquidityPool({"from": accounts[0]})


def test_withdrawDepositsWithLiquidity(pool_liquidity_02):
    chain.sleep(POOL_LAUNCH_WINDOW + 100)
    chain.mine
    with reverts("PoolLiquidity02: Timer has not yet expired"):
        pool_liquidity_02.withdrawDeposits({"from": accounts[0]})

def test_withdrawDeposits(pool_liquidity_02, token_1, token_2, deposit_token1, deposit_token2):
    chain.sleep(POOL_LAUNCH_DEADLINE+POOL_LAUNCH_WINDOW+1) 
    pool_liquidity_02.withdrawDeposits({"from": accounts[0]})

    assert token_1.balanceOf(pool_liquidity_02) == 0
    assert token_2.balanceOf(pool_liquidity_02) == 0

def test_withdrawDepositsWrongOperator(pool_liquidity_02):
    
    with reverts("PoolLiquidity02: Sender must be operator"):
        pool_liquidity_02.withdrawDeposits({"from": accounts[5]})