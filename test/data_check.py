import ipdb
import os
import time
import logging
from src import DataFeed, HostPort, TransactionBuild, SwapAmountInRoute, Coin
from src import create_osmo_wallet, check_dir, grpc_connection, wallet_balance
from decimal import Decimal
from dotenv import load_dotenv

class NewStrategyInstance:
    def __init__(self, env_file_path: str):
        load_dotenv(env_file_path)
        self.log_file: str =  os.environ.get("LOG_FILE")
        self.mnemonic: str =  os.environ.get("MNEMONIC")
        self.rpc_url: str = os.environ.get("RPC_URL")
        self.rest_url: str = os.environ.get("REST_URL")
        self._host_port: HostPort = HostPort(host= os.environ.get("gRPC_host"), port= os.environ.get("gRPC_port"))
        self._grpc_ob = grpc_connection(self._host_port)
        self.wallet = create_osmo_wallet(self.mnemonic, self._host_port)
        self.pool_id: int = 1
        self.token_0_amount: Decimal = Decimal(10)
        self.token_1_amount: Decimal = Decimal(100)
        self.interval: int = 15
        self._datafeed = DataFeed(pool_id= self.pool_id, interval= self.interval, token_0_amount= self.token_0_amount, token_1_amount= self.token_1_amount, rpc_url= self.rpc_url, grpc_con= self._grpc_ob)

        # Set up logging
        check_dir(self.log_file.split("/")[0])
        logging.basicConfig(filename=os.environ.get("LOG_FILE"), encoding='utf-8', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())

    def strategy_data(self, datafeed: DataFeed = None):
        if datafeed is None:
            datafeed = self._datafeed

        while True:
            price, height = datafeed.get_pool_reserves(pool_ids= [self.pool_id])
            ipdb.set_trace()
            bid_ask = datafeed._bid_ask_calculation(self.pool_id, self.token_0_amount, self.token_1_amount, price, reverse= True)
            balance = wallet_balance(wallet_address= self.wallet.address, grpc_ob= self._grpc_ob, token_data_json= datafeed._all_token_decimal_data)
            assets = datafeed.get_pool_assets(pool_id= 1)
            # price = datafeed.historical_data(height= height)
            
            tx = TransactionBuild(account= self.wallet, _host_port = self._host_port)
            routes = [SwapAmountInRoute(pool_id= 1, denom= "uosmo")]
            tx_data_dict = tx.broadcast_exact_in_transaction(routes= routes, token_in= Coin(amount= 10 * pow(10,6), denom= "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"), slippage= Decimal(0.002), pools= price)
            # price series
            print("price data series", price)
            time.sleep(10)

ipdb.set_trace()
strategy_obj = NewStrategyInstance("envs/strategy.env")
strategy_obj.strategy_data()
