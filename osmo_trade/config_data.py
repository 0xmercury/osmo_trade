import os
import json
import grpc
import requests
from osmo_trade import HostPort
from osmo_trade.constants import ROOT_DIR
import osmosis_protobuf.osmosis.pool_incentives.v1beta1.query_pb2 as incentives_pb
import osmosis_protobuf.osmosis.pool_incentives.v1beta1.query_pb2_grpc as incentives_pb_grpc
import osmosis_protobuf.cosmos.base.tendermint.v1beta1.query_pb2 as query_pb
import osmosis_protobuf.cosmos.base.tendermint.v1beta1.query_pb2_grpc as query_pb_grpc
from google.protobuf.json_format import MessageToDict


def json_file_update() -> dict:
    """
    It is used to store all the relevant information of the pools, tokens, token decimals etc in a json file named **essential_poolId_token_data.json** which is used further in the package

    Side Note: Please run this function atleast once a week to keep the json file updated with all the new tokens getting listed on osmosis.
    """
    POOL_IDS = {}
    POOL_ASSETS = {}
    asset_decimals = {}
    denom_symbols = {}
    symbols_denom = {}
    CURRENT_WORKING_DIRECTORY = os.getcwd()
    ALL_DATA_FILE_NAME = "essential_poolId_token_data.json"
    token_pool_dict = {}
    data = requests.get(
        "https://raw.githubusercontent.com/osmosis-labs/assetlists/main/osmosis-1/osmosis-1.assetlist.json").json()
    for i in data["assets"]:
        asset_decimals[i['base']] = i['denom_units'][-1]['exponent']
        denom_symbols[i['base']] = i['symbol']
        symbols_denom[i['symbol']] = i['base']
    pool_data = requests.get(
        "https://api-osmosis.imperator.co/pools/v2/all?low_liquidity=true").json()
    for key, pool in pool_data.items():
        symbol = str()
        if pool[0]['liquidity'] >= 1000:
            for i in pool:
                symbol += i['symbol'] + "_"
            symbol = symbol[:-1]
        else:
            continue
        POOL_IDS[key] = symbol
        list_of_denom = []
        for asset in pool:
            list_of_denom.append(asset['denom'])
        POOL_ASSETS[key] = list_of_denom
    try:
        os.remove(os.path.join(ROOT_DIR ,ALL_DATA_FILE_NAME))
    except FileNotFoundError:
        # means the file does not exists
        pass

    with open(os.path.join(ROOT_DIR ,ALL_DATA_FILE_NAME), "w") as g:
        token_pool_dict["all_pool_ids"] = POOL_IDS
        token_pool_dict["pool_assets"] = POOL_ASSETS
        token_pool_dict["denom_symbol"] = denom_symbols
        token_pool_dict["symbol_denom"] = symbols_denom
        token_pool_dict["asset_decimals"] = asset_decimals
        json.dump(token_pool_dict, g)

    return token_pool_dict

def read_json_file():
    ALL_DATA_FILE_NAME = "essential_poolId_token_data.json"
    with open(os.path.join(ROOT_DIR ,ALL_DATA_FILE_NAME), "r") as file:
        read_file = json.lood(file)
    return read_file

def get_incentive_data(grpc_ob):
    """
    We're gathering info whether pools are internally incentivised.
    """
    incentives_stub = incentives_pb_grpc.QueryStub(grpc_ob)
    grpc_incentives_data = incentives_stub.IncentivizedPools(
        incentives_pb.QueryIncentivizedPoolsRequest())
    pools_data = MessageToDict(grpc_incentives_data)['incentivizedPools']
    pools = []
    for pool in pools_data:
        pools.append(int(pool['poolId']))
    return pools


def check_dir(dir: str) -> None:
    logs_directory: str = dir
    directory_exists = os.path.isdir(logs_directory)
    if not directory_exists:
        os.makedirs(logs_directory)
        print("created directory : ", logs_directory)
    else:
        print(logs_directory, "directory already exists.")

def grpc_connection(_host_port: HostPort):
    if _host_port.ssl:
        con = grpc.secure_channel(
            f"{_host_port.host}:{_host_port.port}", credentials=grpc.ssl_channel_credentials())
    else:
        con = grpc.insecure_channel(f"{_host_port.host}:{_host_port.port}")
    return con

def get_block_height(grpc_ob):
    height_stub = query_pb_grpc.ServiceStub(grpc_ob)
    height = height_stub.GetLatestBlock(query_pb.GetLatestBlockRequest())
    return height.block.header.height

