from brownie import accounts, web3, Wei, reverts, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *
from test_pool_liquidity import deposit_eth, deposit_tokens


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

# Crowdsale with token payment
@pytest.fixture(scope='module', autouse=True)
def crowdsale_2(Crowdsale, mintable_token, fixed_token2):
    crowdsale = Crowdsale.deploy({"from": accounts[0]})
    mintable_token.mint(accounts[0], CROWDSALE_TOKENS_2, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == CROWDSALE_TOKENS_2

    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    operator = accounts[0]
    wallet = accounts[4]
    
    mintable_token.approve(crowdsale, CROWDSALE_TOKENS_2, {"from": accounts[0]})
    crowdsale.initCrowdsale(
        accounts[0],
        mintable_token,
        fixed_token2,
        CROWDSALE_TOKENS_2,
        start_time,
        end_time,
        CROWDSALE_RATE_2,
        CROWDSALE_GOAL,
        operator,
        ZERO_ADDRESS,
        wallet,
        {"from": accounts[0]}
    )
    assert mintable_token.balanceOf(crowdsale) == CROWDSALE_TOKENS_2
    chain.sleep(10)
    return crowdsale 

# Crowdsale with a pool liquidity operator
@pytest.fixture(scope='module', autouse=True)
def crowdsale_3(Crowdsale, mintable_token, pool_liquidity):
    crowdsale = Crowdsale.deploy({"from": accounts[0]})
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS

    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    wallet = accounts[4]
    operator = pool_liquidity
    
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

#####################################
# Helper Functions 
#####################################
def _buy_tokens(_crowdsale):
    totalAmountRaised = _crowdsale.marketStatus()[0]
    token_buyer =  accounts[1]
    eth_to_transfer = 5 * TENPOW18
    totalAmountRaised += eth_to_transfer
    tx = _crowdsale.buyTokensEth(token_buyer, True, {"value": eth_to_transfer, "from": token_buyer})
    assert 'TokensPurchased' in tx.events
    assert _crowdsale.marketStatus()[0] == totalAmountRaised
    assert _crowdsale.auctionSuccessful() == False

    token_buyer =  accounts[2]
    eth_to_transfer = 5 * TENPOW18
    totalAmountRaised += eth_to_transfer
    tx = _crowdsale.buyTokensEth(token_buyer, True, {"value": eth_to_transfer, "from": token_buyer})
    assert 'TokensPurchased' in tx.events
    assert _crowdsale.marketStatus()[0] == totalAmountRaised
    assert _crowdsale.auctionSuccessful() == True
    return _crowdsale

def _withdraw_tokens(crowdsale, mintable_token):
    token_buyer = accounts[1]
    chain.sleep(CROWDSALE_TIME)
    balance_token_before_withdraw = crowdsale.tokensClaimable(token_buyer)
    crowdsale.withdrawTokens(token_buyer, {"from": token_buyer})
    assert crowdsale.tokensClaimable(token_buyer) == 0
    assert mintable_token.balanceOf(token_buyer) == balance_token_before_withdraw

    with reverts("Crowdsale: no tokens to claim"):
        crowdsale.withdrawTokens(token_buyer, {"from": token_buyer})


def _buy_token_helper(crowdsale, token_buyer, amount):
    eth_to_transfer = amount
    commitments_before = crowdsale.commitments(token_buyer) 
    tokens_claimable_before = crowdsale.tokensClaimable(token_buyer) 
    tx = crowdsale.buyTokensEth(token_buyer, True, {'from': token_buyer, 'value': eth_to_transfer})
    assert 'TokensPurchased' in tx.events  
    commitments_after = crowdsale.commitments(token_buyer)
    # print("crowdsale.commitments(token_buyer):", crowdsale.commitments(token_buyer))
    tokens_claimable_after = tokens_claimable_before + eth_to_transfer * crowdsale.marketPrice()[0] / TENPOW18
    assert commitments_before+eth_to_transfer == commitments_after
    assert tokens_claimable_after == crowdsale.tokensClaimable(token_buyer)
    return crowdsale


#####################################
# Fixture Functions 
#####################################

############## Initialize crowdsale #############################
@pytest.fixture(scope='function')
def crowdsale_init_helper(Crowdsale, mintable_token, fixed_token2):
    crowdsale_init_helper = Crowdsale.deploy({"from": accounts[0]})
    return crowdsale_init_helper 

############## Buy Tokens #############################
@pytest.fixture(scope='function')
def buy_tokens(crowdsale):
    _buy_tokens(crowdsale)

@pytest.fixture(scope='function')
def buy_tokens_3(crowdsale_3):
    _buy_tokens(crowdsale_3)

############## Buy Tokens muitple times without reaching crowdsale goal #############################
@pytest.fixture(scope='function')
def buy_token_multiple_times_goal_not_reached(crowdsale):
    totalAmountRaised = 0
    beneficiary = accounts[1]
    eth_to_transfer = 2 * TENPOW18
    tokens_to_beneficiary = eth_to_transfer * crowdsale.marketPrice()[0] / TENPOW18
    totalAmountRaised += eth_to_transfer

    crowdsale = _buy_token_helper(crowdsale, beneficiary, eth_to_transfer)
    assert crowdsale.marketStatus()[0] == totalAmountRaised
    assert crowdsale.tokensClaimable(beneficiary) == tokens_to_beneficiary

    beneficiary = accounts[2]
    eth_to_transfer = 2 * TENPOW18
    tokens_to_beneficiary = eth_to_transfer * crowdsale.marketPrice()[0]/ TENPOW18
    totalAmountRaised += eth_to_transfer
    crowdsale = _buy_token_helper(crowdsale, beneficiary, eth_to_transfer)
    assert crowdsale.marketStatus()[0] == totalAmountRaised
    assert crowdsale.tokensClaimable(beneficiary) == tokens_to_beneficiary
    
####### Finalize #############
@pytest.fixture(scope='function')
def finalize(crowdsale, buy_tokens, mintable_token):
    old_balance = accounts[4].balance()

    chain.sleep(CROWDSALE_TIME)
    crowdsale_balance = crowdsale.balance()
    tx = crowdsale.finalize({"from": accounts[0]})
    assert 'CrowdsaleFinalized' in tx.events
    assert accounts[4].balance() == old_balance + crowdsale_balance

####### Withdraw Tokens #############
@pytest.fixture(scope='function')
def withdraw_tokens(crowdsale, mintable_token):
    _withdraw_tokens(crowdsale, mintable_token)

####### Withdraw Tokens #############
@pytest.fixture(scope='function')
def withdraw_tokens_3(crowdsale_3, mintable_token):
    _withdraw_tokens(crowdsale_3, mintable_token)


@pytest.fixture(scope='function')
def finalize_and_launch_lp(crowdsale_3, pool_liquidity, mintable_token, buy_tokens_3, deposit_eth, deposit_tokens):
    pool_liquidity.setAuction(crowdsale_3, {"from": accounts[0]})
    assert crowdsale_3 == pool_liquidity.auction()
    old_balance = accounts[4].balance()
    chain.sleep(POOL_LAUNCH_DEADLINE+10)
    crowdsale_balance = crowdsale_3.balance()
    wallet = accounts[4]
    amountRaised = crowdsale_3.marketStatus()[0]
    rate = crowdsale_3.rate()
    tokenBought = amountRaised * rate / TENPOW18
    totalTokens = crowdsale_3.marketInfo()[2]
    unsoldTokens = totalTokens - tokenBought
    balance_before_finalized = mintable_token.balanceOf(wallet)
    pool_liquidity.finalizeMarketAndLaunchLiquidityPool({"from": accounts[0]})
    assert accounts[4].balance() == old_balance + crowdsale_balance
    balance_after_finalized = mintable_token.balanceOf(wallet)
    assert balance_after_finalized - balance_before_finalized == unsoldTokens


#####################################
# Payment currency ETHEREUM
######################################

def test_crowdsale_buy_tokens_with_receive(crowdsale):
    token_buyer = accounts[3]
    eth_to_transfer = 5 * TENPOW18
    tx = crowdsale.buyTokensEth(token_buyer, True, {"from": token_buyer, "value":eth_to_transfer})
    assert 'TokensPurchased' in tx.events
    assert crowdsale.auctionSuccessful() == False


######### get init Data Test #############
def test_init_market_from_data(crowdsale_init_helper, mintable_token, fixed_token2):
    mintable_token.mint(accounts[0], CROWDSALE_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    funder = accounts[0]
    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    wallet = accounts[4]
    operator = accounts[0]
    
    mintable_token.approve(crowdsale_init_helper, CROWDSALE_TOKENS, {"from": funder})
    
    _data = crowdsale_init_helper.getCrowdsaleInitData(accounts[0],mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator, ZERO_ADDRESS, wallet, {"from": accounts[0]})
    
    crowdsale_init_helper.initMarket(_data)
    
    totalAmountRaised = 0
    token_buyer =  accounts[1]
    eth_to_transfer = 5 * TENPOW18
    totalAmountRaised += eth_to_transfer
    chain.sleep(10)
    tx = crowdsale_init_helper.buyTokensEth(token_buyer, True, {"value": eth_to_transfer, "from": token_buyer})
    
    
    assert crowdsale_init_helper.operator() == operator
    assert 'TokensPurchased' in tx.events
    assert crowdsale_init_helper.marketStatus()[0] == totalAmountRaised
    assert crowdsale_init_helper.auctionSuccessful() == False

####### Finalize Test #############3
def test_crowdsale_finalize(crowdsale, buy_tokens, mintable_token):
    old_balance = accounts[4].balance()
    chain.sleep(CROWDSALE_TIME)
    crowdsale_balance = crowdsale.balance()
    wallet = accounts[4]
    amountRaised = crowdsale.marketStatus()[0]
    rate = crowdsale.marketPrice()[0]
    tokenBought = amountRaised * rate / TENPOW18
    totalTokens = crowdsale.marketInfo()[2]
    unsoldTokens = totalTokens - tokenBought
    balance_before_finalized = mintable_token.balanceOf(wallet)
    tx = crowdsale.finalize({"from": accounts[0]})
    assert 'CrowdsaleFinalized' in tx.events
    assert accounts[4].balance() == old_balance + crowdsale_balance
    balance_after_finalized = mintable_token.balanceOf(wallet)

    assert balance_after_finalized - balance_before_finalized == unsoldTokens

    with reverts("Crowdsale: already finalized"):
        tx = crowdsale.finalize({"from": accounts[0]})

def test_crowdsale_finalize_not_closed(crowdsale):
    with reverts("Crowdsale: Has not finished yet"):
        crowdsale.finalize({"from": accounts[0]})

def test_crowdsale_finalize_goal_not_reached(crowdsale, mintable_token, buy_token_multiple_times_goal_not_reached):
    chain.sleep(CROWDSALE_TIME)
    wallet = accounts[4]
    amountRaised = crowdsale.marketStatus()[0]
    rate = crowdsale.marketPrice()[0]
    tokenBought = amountRaised * rate / TENPOW18
    totalTokens = crowdsale.marketInfo()[2]
    unsoldTokens = totalTokens - tokenBought
    balance_before_finalized = mintable_token.balanceOf(wallet)
    tx = crowdsale.finalize({"from": accounts[0]})
    assert 'CrowdsaleFinalized' in tx.events
    
    # TODO  
    # balance_after_finalized = mintable_token.balanceOf(wallet)

    # assert balance_after_finalized - balance_before_finalized == unsoldTokens




############## INIT Test ###################################
def test_crowdsale_init_done_again(crowdsale, mintable_token):
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    operator = accounts[0]
    wallet = accounts[4]
    mintable_token.approve(crowdsale, AUCTION_TOKENS, {"from": accounts[0]})
    with reverts("Crowdsale: already initialized"):
        crowdsale.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})


############## INIT Test ###################################
def test_crowdsale_init_goal_greater_than_total_tokens(crowdsale_init_helper, mintable_token):
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    operator = accounts[0]
    wallet = accounts[4]
    goal = 10*TENPOW18
    total_token = 100 * TENPOW18
    rate = 100 * TENPOW18
    mintable_token.approve(crowdsale_init_helper, AUCTION_TOKENS, {"from": accounts[0]})
    with reverts("Crowdsale: goal should be equal to or lower than total tokens or equal"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, total_token, start_time, end_time, rate, goal, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})

    
############## INIT Test ###################################
def test_crowdsale_end_less_than_start(crowdsale_init_helper, mintable_token):
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    start_time = chain.time() + 10
    end_time = start_time - 1
    wallet = accounts[4]
    operator = accounts[0]
    mintable_token.approve(crowdsale_init_helper, AUCTION_TOKENS, {"from": accounts[0]})
    with reverts("Crowdsale: start time is not before end time"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})    
    
    end_time = start_time + CROWDSALE_TIME
    start_time = chain.time() - 10
    with reverts("Crowdsale: start time is before current time"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})    
    
    
    start_time = chain.time() + 10
    payment_currency = ZERO_ADDRESS
    with reverts("Crowdsale: payment currency is the zero address"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, payment_currency, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})    

    wallet = ZERO_ADDRESS
    with reverts("Crowdsale: wallet is the zero address"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})    

    wallet = accounts[4]
    operator = ZERO_ADDRESS
    with reverts("Crowdsale: operator is the zero address"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})    


############## INIT Test ###################################
def test_crowdsale_start_time_less_than_current(crowdsale_init_helper, mintable_token):
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    start_time = chain.time() - 10
    end_time = start_time + CROWDSALE_TIME
    operator = accounts[0]
    wallet = accounts[4]
    mintable_token.approve(crowdsale_init_helper, AUCTION_TOKENS, {"from": accounts[0]})
    with reverts("Crowdsale: start time is before current time"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, CROWDSALE_RATE, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})

############## INIT Test ###################################
def test_crowdsale_rate_0(crowdsale_init_helper, mintable_token):
    mintable_token.mint(accounts[0], AUCTION_TOKENS, {"from": accounts[0]})
    assert mintable_token.balanceOf(accounts[0]) == AUCTION_TOKENS
    start_time = chain.time() + 10
    end_time = start_time + CROWDSALE_TIME
    operator = accounts[0]
    wallet = accounts[4]
    mintable_token.approve(crowdsale_init_helper, AUCTION_TOKENS, {"from": accounts[0]})
    with reverts("Crowdsale: rate is 0"):
        crowdsale_init_helper.initCrowdsale(accounts[0], mintable_token, ETH_ADDRESS, CROWDSALE_TOKENS, start_time, end_time, 0, CROWDSALE_GOAL, operator,ZERO_ADDRESS, wallet, {"from": accounts[0]})

############## Buy Tokens Test #############################
def test_crowdsale_buy_token_with_zero_address(crowdsale):
    token_buyer =  ZERO_ADDRESS
    eth_to_transfer = 5 * TENPOW18
    with reverts():
        crowdsale.buyTokensEth(token_buyer, True, {"value": eth_to_transfer, "from": accounts[0]})

############## Buy Tokens Test #############################
def test_crowdsale_buy_token_multiple_times_goal_not_reached(crowdsale):
    totalAmountRaised = 0
    beneficiary = accounts[1]
    eth_to_transfer = 2 * TENPOW18
    totalAmountRaised += eth_to_transfer

    crowdsale = _buy_token_helper(crowdsale, beneficiary, eth_to_transfer)
    assert crowdsale.marketStatus()[0] == totalAmountRaised
    assert crowdsale.commitments(beneficiary) == eth_to_transfer

    beneficiary = accounts[2]
    eth_to_transfer = 2 * TENPOW18
    totalAmountRaised += eth_to_transfer
    crowdsale = _buy_token_helper(crowdsale, beneficiary, eth_to_transfer)
    assert crowdsale.marketStatus()[0] == totalAmountRaised
    assert crowdsale.commitments(beneficiary) == eth_to_transfer

    return crowdsale

############## Buy Tokens Test #############################
def test_crowdsale_buy_token_after_end_time(crowdsale):
    beneficiary = accounts[1]
    token_buyer = accounts[1]
    chain.sleep(CROWDSALE_TIME)
    eth_to_transfer = 2 * TENPOW18
    with reverts():
        crowdsale.buyTokensEth(beneficiary, True, {"value": eth_to_transfer, "from": token_buyer})

############## Buy Tokens Test #############################
def test_crowdsale_buy_token_greater_than_total_tokens(crowdsale, buy_tokens):
    beneficiary = accounts[3]
    token_buyer = accounts[3]
    eth_to_transfer = 1 * TENPOW18
    with reverts():
        crowdsale.buyTokensEth(beneficiary, True, {"value": eth_to_transfer, "from": token_buyer})

############## Buy Tokens Test #############################
def test_crowdsale_buy_token_with_zero_value(crowdsale, buy_tokens):
    beneficiary = accounts[3]
    token_buyer = accounts[3]
    eth_to_transfer = 0
    with reverts():
        crowdsale.buyTokensEth(beneficiary, True, {"value": eth_to_transfer, "from": token_buyer})

################ Withdraw Token Test##########################
def test_crowdsale_withdraw_tokens_goal_reached(crowdsale, buy_tokens, mintable_token, finalize):
    pass
    

################ Withdraw Token Test##########################
def test_crowdsale_3_withdraw_tokens_after_finalize_expires(crowdsale_3, mintable_token):
    crowdsale_3 = _buy_tokens(crowdsale_3)
    chain.sleep(CROWDSALE_TIME + 14*24*3600)
    tx = crowdsale_3.finalize({"from": accounts[5]})
    assert 'CrowdsaleFinalized' in tx.events
    _withdraw_tokens(crowdsale_3, mintable_token)

############### Withdraw Token Test##########################
def test_crowdsale_withdraw_tokens_goal_not_reached(crowdsale, mintable_token, buy_token_multiple_times_goal_not_reached):
    chain.sleep(CROWDSALE_TIME)
    claimer1 = accounts[1]
    claimer2 = accounts[2]
    
    claimer1_eth_balance_before_withdraw = claimer1.balance()
    claimer1_commitments_before_withdraw = crowdsale.commitments(claimer1)
    claimer2_commitments_before_withdraw = crowdsale.commitments(claimer2)
    claimer2_eth_balance_before_withdraw = claimer2.balance()
    chain.sleep(CROWDSALE_TIME)
    crowdsale.withdrawTokens(claimer1, {"from": claimer1})
    crowdsale.withdrawTokens(claimer2, {"from": claimer1})
    assert crowdsale.commitments(claimer1) == 0
    assert claimer1_eth_balance_before_withdraw + claimer1_commitments_before_withdraw == claimer1.balance()
    assert claimer2_eth_balance_before_withdraw + claimer2_commitments_before_withdraw == claimer2.balance()

################ Withdraw Token Test##########################
def test_crowdsale_withdraw_tokens_has_not_closed(crowdsale,buy_tokens):
    token_buyer = accounts[1]
    with reverts():
        crowdsale.withdrawTokens(token_buyer, {"from": token_buyer})

################ Withdraw Token Test##########################
def test_crowdsale_withdraw_tokens_wrong_beneficiary(crowdsale,buy_tokens):  
    beneficiary = accounts[2]
    token_buyer = accounts[1] 
    with reverts():
        crowdsale.withdrawTokens(beneficiary, {"from": token_buyer})
        
def test_crowdsale_tokenBalance(crowdsale, mintable_token):
    assert mintable_token.balanceOf(crowdsale) == CROWDSALE_TOKENS

def test_crowdsale_buyTokensExtra(crowdsale):
    token_buyer =  accounts[2]
    goal = crowdsale.marketPrice()[1]
    eth_to_transfer = goal + 1

    with reverts():
        crowdsale.buyTokensEth(token_buyer, True, {"value": eth_to_transfer})

def test_crowdsale_commitments(crowdsale, mintable_token, buy_tokens):
    assert crowdsale.commitments(accounts[1]) == 5 * TENPOW18

def test_crowdsale_finalize_time_expired(crowdsale, mintable_token, buy_tokens):
    assert crowdsale.finalizeTimeExpired() == False


#####################################
# Payment currency Token
######################################

############## Buy Tokens Test #############################
def test_crowdsale_2_buy_with_tokens(crowdsale_2, fixed_token2):
    totalAmountRaised = 0
    token_to_transfer = 5 * TENPOW18
    fixed_token2.transfer(accounts[1], token_to_transfer, {"from": accounts[0]})
    token_buyer =  accounts[1]
    fixed_token2.approve(crowdsale_2, token_to_transfer, {"from": accounts[1]})
    totalAmountRaised += token_to_transfer
    tx = crowdsale_2.buyTokens(token_buyer, token_to_transfer, True, {"from": token_buyer})
    assert 'TokensPurchased' in tx.events
    assert crowdsale_2.marketStatus()[0] == totalAmountRaised
    assert crowdsale_2.auctionSuccessful() == False

    token_buyer =  accounts[2]
    token_to_transfer = 2 * TENPOW18
    fixed_token2.transfer(token_buyer, token_to_transfer, {"from": accounts[0]})
    fixed_token2.approve(crowdsale_2, token_to_transfer, {"from": token_buyer})
    totalAmountRaised += token_to_transfer
    tx = crowdsale_2.buyTokens(token_buyer, token_to_transfer, True, {"from": token_buyer})
    
    assert 'TokensPurchased' in tx.events
    assert crowdsale_2.marketStatus()[0] == totalAmountRaised
    assert crowdsale_2.auctionSuccessful() == False
    with reverts("Crowdsale: Has not finished yet"):
        crowdsale_2.finalize({"from": accounts[0]})

    #########  FAIL CASE: #####################
    token_buyer =  accounts[3]
    token_to_transfer = 5 * TENPOW18
    
    fixed_token2.transfer(token_buyer, token_to_transfer, {"from": accounts[0]})
    fixed_token2.approve(crowdsale_2, token_to_transfer, {"from": token_buyer})
    
    with reverts("Crowdsale: amount of tokens exceeded"):
        crowdsale_2.buyTokens(token_buyer, token_to_transfer, True, {"from": token_buyer})
   
    ##################################################
    
    token_to_transfer = 3 * TENPOW18
    
    fixed_token2.transfer(token_buyer, token_to_transfer, {"from": accounts[0]})
    fixed_token2.approve(crowdsale_2, token_to_transfer, {"from": token_buyer})
    
    totalAmountRaised += token_to_transfer
    crowdsale_2.buyTokens(token_buyer, token_to_transfer, True, {"from": token_buyer})

    assert 'TokensPurchased' in tx.events
    assert crowdsale_2.marketStatus()[0] == totalAmountRaised
    assert crowdsale_2.auctionSuccessful() == True
    ###### Finalize success as total tokens reached #########
    crowdsale_2.finalize({"from": accounts[0]})
    
    token_buyer =  accounts[1]
    crowdsale_2.withdrawTokens(token_buyer,{"from": token_buyer})
    token_buyer = accounts[2]
    crowdsale_2.withdrawTokens(token_buyer,{"from": token_buyer})
    token_buyer =  accounts[3]
    crowdsale_2.withdrawTokens(token_buyer,{"from": token_buyer})


############## Buy Tokens Test #############################
def test_buy_tokens_with_token_for_currency_ETH(crowdsale, fixed_token2):
    token_to_transfer = 5 * TENPOW18
    fixed_token2.transfer(accounts[1], token_to_transfer, {"from": accounts[0]})
    token_buyer =  accounts[1]
    fixed_token2.approve(crowdsale, token_to_transfer, {"from": accounts[1]})
    with reverts():
        crowdsale.buyTokens(token_buyer, token_to_transfer, True, {"from": token_buyer})


############## Buy Tokens Test #############################
def test_crowdsale_2_buy_tokens_with_ETH_for_currency_token(crowdsale_2, fixed_token2):
    token_buyer =  accounts[1]
    eth_to_transfer = 5 * TENPOW18
    with reverts():
            crowdsale_2.buyTokensEth(token_buyer, True, {"value": eth_to_transfer, "from": token_buyer})
