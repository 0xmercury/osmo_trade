from mospy import Account, Transaction
from mospy.clients import GRPCClient
from osmo_trade import Coin
import osmosis_protobuf.cosmos.bank.v1beta1.query_pb2 as wallet_pb
import osmosis_protobuf.cosmos.bank.v1beta1.query_pb2_grpc as wallet_pb_grpc


def create_osmo_wallet(_seed: str, _host_port) -> Account:
    _hrp: str = "osmo"
    _protobuf: str = "osmosis"
    account = Account(seed_phrase=_seed, hrp=_hrp, protobuf=_protobuf)
    client = GRPCClient(host=_host_port.host, port=_host_port.port, ssl= _host_port.ssl, protobuf=_protobuf)
    client.load_account_data(account)
    return account

def wallet_balance(wallet_address: str, token_data_json: dict, grpc_ob):
    wallet_stub = wallet_pb_grpc.QueryStub(grpc_ob)
    grpc_wallet_data = wallet_stub.AllBalances(wallet_pb.QueryAllBalancesRequest(address= wallet_address))
    coin_list: list = []
    if len(grpc_wallet_data.balances) > 0:
        for balance in grpc_wallet_data.balances:
            new_coin = Coin(denom= balance.denom, amount= balance.amount, denom_symbol= token_data_json['denom_symbol'])
            coin_list.append(new_coin)
        return coin_list
    else:
        print("No coins available in the wallet")
        return 0

