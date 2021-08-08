# Import dependencies
import subprocess
import json
import os
from dotenv import load_dotenv
from pprint import pprint


# Import constants.py and necessary functions from bit (for BTCTest) and web3 (for ETH)
from constants import *
from bit import PrivateKeyTestnet
from bit.network import NetworkAPI

from web3 import Web3, middleware, Account
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.middleware import geth_poa_middleware
from eth_account import Account

# connect Web3 to our local network 8545
w3 = Web3(Web3.HTTPProvider('http://localhost:8545')) 


# enable PoA middleware
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# set gas price strategy to built-in "medium" algorythm (default to about 5 per tx)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

# Load and set environment variables
load_dotenv('LT.env')

# Set your mnemonic variable
mnemonic=os.getenv("mnemonic")


# Create a function called `derive_wallets`
def derive_wallets(mnemonic, coin, depth):
    command = f'./derive -g --mnemonic="{mnemonic}" --coin="{coin}" --numderive="{depth}" --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
coins = {
    "ETH": derive_wallets(mnemonic, ETH, "3"),
    "BTC-TEST": derive_wallets(mnemonic, BTCTEST, "3")
}

pprint(coins)

# Extract the two private keys from the two first addresses we will be using to initiate our test transactions
btc_privkey=coins['BTC-TEST'][0]['privkey']
eth_privkey= coins['ETH'][0]['privkey']


# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):
    if coin == ETH:
        value = w3.toWei(amount, 'ether') # convert eth to wei
        gasEstimate = w3.eth.estimateGas({'to':to, 'from':account, 'amount':value})
        return{
            'to': to,
            'from': account,
            'value': value,
            'gas': gasEstimate,
            'gasPrice': w3.eth.generateGasPrice(),
            'nonce': w3.eth.getTransactionCount(account),
            'chainId': w3.eth.chain_id
        }
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):
    if coin == ETH:
        raw_tx = create_tx(coin, account.address, to, amount)
        signed = account.signTransaction(raw_tx)
        return w3.eth.sendRawTransaction(signed.rawTransaction)
    if coin == BTCTEST:
        raw_tx = create_tx(coin, account, to, amount)
        signed = account.sign_transaction(raw_tx)
        return NetworkAPI.broadcast_tx_testnet(signed)

# Create the priv_key object that we will need to send transactions
account_btc1 = priv_key_to_account(BTCTEST, btc_privkey)
account_eth1 = priv_key_to_account(ETH, eth_privkey)