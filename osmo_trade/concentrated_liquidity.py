import csv
import requests
from mospy import Account, Transaction
#mospy.Account.protobuf = 'osmo'
from mospy.clients import HTTPClient
#from cosmospy_protobuf.cosmos.base.v1beta1.coin_pb2 import Coin
import pandas as pd
import os
from .tx_pb4 import MsgCreatePosition, MsgWithdrawPosition, MsgAddToPosition
import json
import requests


rpc_endpoint = "https://cosmos-lcd.easy2stake.com"
rest_endpoint = "https://api.osl.zone"

def query_user_position(address, pool_id=None):
    endpoint = f"{rest_endpoint}/osmosis/concentratedliquidity/v1beta1/positions/{address}"
    if pool_id:
        endpoint += f"?pool_id={pool_id}"

    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            user_positions_data = response.json()
            print(user_positions_data)
            return user_positions_data
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return None
    except Exception as ex:
        print(f"An error occurred: {ex}")
        return None


def read_input_json(file_path):
    with open(file_path, 'r') as jsonfile:
        return json.load(jsonfile)


def get_pools():
    rest_endpoint = "https://api.osl.zone"  # Replace with the correct endpoint for Osmosis API
    query_url = f"{rest_endpoint}/osmosis/concentratedliquidity/v1beta1/pools"
    
    try:
        response = requests.get(query_url)
        if response.status_code == 200:
            pools_data = response.json()
            print(pools_data)
            return pools_data
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return None
    except Exception as ex:
        print(f"An error occurred: {ex}")
        return None



def fetch_account_data(stride_address):
    print(f"Fetching account data for Stride address: {stride_address}")

    response = requests.get(f"{rest_endpoint}/cosmos/auth/v1beta1/accounts/{stride_address}")

    if response.status_code == 200:
        
        account_data = response.json()
        if "base_vesting_account" in account_data["account"]:
            acc_number = int(account_data["account"]['base_vesting_account']['base_account']["account_number"])
            sequence = int(account_data["account"]['base_vesting_account']['base_account']["sequence"])
            print(f"Stride Account number: {acc_number}")
            print(f"Stride Sequence number: {sequence}")
            return acc_number, sequence
        elif "account_number" in account_data["account"]:
            acc_number = int(account_data["account"]["account_number"])
            sequence = int(account_data["account"]["sequence"])
            print(f"Stride Account number: {acc_number}")
            print(f"Stride Sequence number: {sequence}")
            return acc_number, sequence
        else:
            raise Exception("Status code :{}, reason: {}, error: problem in fetching in acc details".format(response.status_code, response.reason))
        
    else:
        print(response.status_code, response.reason)
        return None, None
def create_position_transaction(account, pool_id, sender_address, lower_tick, upper_tick, tokens_provided, token_min_amount0, token_min_amount1):
    ibc_msg = MsgCreatePosition(
        pool_id=pool_id,
        sender=sender_address,
        lower_tick=lower_tick,
        upper_tick=upper_tick,
        tokens_provided=tokens_provided,
        token_min_amount0=token_min_amount0,
        token_min_amount1=token_min_amount1
    )

    tx = Transaction(
        account=account,
        chain_id="osmosis-1",
        gas=3000000,
        protobuf='osmosis'
    )
    tx.set_fee(
        amount=75000,
        denom="uosmo"
    )
    tx.add_raw_msg(ibc_msg, type_url="/osmosis.concentratedliquidity.v1beta1.MsgCreatePosition")

    return tx

def withdraw_position_transaction(account, position_id, sender_address, liquidity_amount):
    ibc_msg = MsgWithdrawPosition(
        position_id=position_id,
        sender=sender_address,
        liquidity_amount=(liquidity_amount)
    )

    tx = Transaction(
        account=account,
        chain_id="osmosis-1",
        gas=3000000,
        protobuf='osmosis'
    )
    tx.set_fee(
        amount=75000,
        denom="uosmo"
    )
    tx.add_raw_msg(ibc_msg, type_url="/osmosis.concentratedliquidity.v1beta1.MsgWithdrawPosition")

    return tx

def add_to_position_transaction(account, amount0, amount1, position_id, sender_address, token_min_amount0, token_min_amount1):
    ibc_msg = MsgAddToPosition(
        amount0=amount0,
        amount1=amount1,
        position_id=position_id,
        sender=sender_address,
        token_min_amount0=token_min_amount0,
        token_min_amount1=token_min_amount1
    )

    tx = Transaction(
        account=account,
        chain_id="osmosis-1",
        gas=3000000,
        protobuf='osmosis'
    )
    tx.set_fee(
        amount=75000,
        denom="uosmo"
    )
    tx.add_raw_msg(ibc_msg, type_url="/osmosis.concentratedliquidity.v1beta1.MsgAddToPosition")

    return tx

