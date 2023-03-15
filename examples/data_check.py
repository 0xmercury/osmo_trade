import ipdb
import os
import time
import logging
import requests
from osmo_trade import DataFeed, HostPort, TransactionBuild, SwapAmountInRoute, BidAskPrice, Coin, ROOT_DIR, CURR_DIR
from osmo_trade import create_osmo_wallet, check_dir, grpc_connection, wallet_balance
from decimal import Decimal
from dotenv import load_dotenv

class NewStrategyInstance:
    def __init__(self, env_file_path: str):
        load_dotenv(env_file_path)
        # Need to update the directory of log_file accordingly from wherever you'd want to store the log file
        self.log_file: str =  os.path.join(CURR_DIR.replace("examples", "") , os.environ.get("LOG_FILE"))
        self.mnemonic: str =  os.environ.get("MNEMONIC")
        self.rpc_url: str = os.environ.get("RPC_URL")
        self.rest_url: str = os.environ.get("REST_URL")
        self._host_port: HostPort = HostPort(host= os.environ.get("gRPC_host"), port= os.environ.get("gRPC_port"), ssl= True)
        self._grpc_ob = grpc_connection(self._host_port)
        self.wallet = create_osmo_wallet(self.mnemonic, self._host_port)
        self.pool_id: list = [678, 1]
        self.token_0_amount: Decimal = Decimal(100)
        self.token_1_amount: Decimal = Decimal(10)
        self.interval: int = 15
        self._datafeed = DataFeed(pool_id= self.pool_id, interval= self.interval, token_0_amount= self.token_0_amount, token_1_amount= self.token_1_amount, rpc_url= self.rpc_url, grpc_con= self._grpc_ob)

        # Set up logging
        ipdb.set_trace()
        path, file = os.path.split(self.log_file)
        check_dir(path)
        logging.basicConfig(filename= self.log_file, encoding='utf-8', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())

    
    def strategy_data(self, datafeed: DataFeed = None):
        if datafeed is None:
            datafeed = self._datafeed
        
        old_block_height = 0                        # store always last block height
        new_block_height = 0                        # store always latest block height
        # Flag to check whether we have taken a position or not
        is_long_position = False
        tx = TransactionBuild(account= self.wallet, _host_port = self._host_port)
        print("\nwallet address: ", self.wallet.address)
        usdc_pool_assets = datafeed.get_pool_assets(pool_id=self.pool_id[0])
        atom_pool_assets = datafeed.get_pool_assets(pool_id=self.pool_id[1])

        while True:
            pool_reserves, height = datafeed.get_pool_reserves(pool_ids= self.pool_id)
            all_token_balance = wallet_balance( wallet_address=self.wallet.address, grpc_ob=self._grpc_ob, token_data_json=datafeed._all_token_decimal_data)
            for token_balance in all_token_balance:
                print("Token Symbol: {}, Amount: {}, Denom: {}".format(token_balance.symbol, token_balance.amount,  token_balance.denom))
            ipdb.set_trace()
            entry_spread, exit_spread = self.get_entry_exit_spreads(pool_reserves)
            if entry_spread > 10 and not is_long_position:
                print("Go For long Position")
                routes = [SwapAmountInRoute(pool_id= self.pool_id[0], denom= usdc_pool_assets[1]), SwapAmountInRoute(pool_id = self.pool_id[1], denom= atom_pool_assets[0])]
                asset_balance = [ item for item in all_token_balance if item.denom == usdc_pool_assets[0]][0]
                tx_hash = tx.broadcast_exact_in_transaction(routes=routes, token_in=Coin(amount=int(asset_balance.amount*0.98), denom=usdc_pool_assets[0]), slippage = Decimal(0.002), pools= pool_reserves)
                print("Transaction Hash: ", tx_hash)
                is_long_position = True
            elif exit_spread > 0 and is_long_position:
                print("unwind position")
                routes = [SwapAmountInRoute(pool_id= self.pool_id[1], denom= atom_pool_assets[1]), SwapAmountInRoute(pool_id = self.pool_id[0], denom= usdc_pool_assets[0])]
                asset_balance = [ item for item in all_token_balance if item.denom == atom_pool_assets[0]][0]
                tx_hash = tx.broadcast_exact_in_transaction(routes=routes, token_in=Coin(amount=int(asset_balance.amount*0.98), denom=atom_pool_assets[0]), slippage = Decimal(0.002), pools= pool_reserves)
                print("Transaction Hash: ", tx_hash)
                is_long_position = False
                
            time.sleep(3)
    
    def get_entry_exit_spreads(self, pool_reserves_dict):
        binance_bid_ask = self.get_binance_price()
        osmosis_bid_ask = datafeed._bid_ask_calculation(self.pool_id, self.token_0_amount, self.token_1_amount, pool_reserves_dict, reverse= False)
        entry_spread, exit_spread = self.signal_using_spread(binance_bid_ask, osmosis_bid_ask)
        return entry_spread, exit_spread

    @staticmethod
    def signal_using_spread(binance_price: BidAskPrice, osmosis_price: BidAskPrice):
    # calc["entry_0"], calc['exit_0'] = (1-calc["osmo_atom_ask"]/calc["ATOM_Binance_bid"])*10000, (1-calc["ATOM_Binance_ask"]/calc["osmo_atom_bid"])*10000
        entry_spread = (1 - osmosis_price.ask/binance_price.bid)*10000
        exit_spread = (1 - binance_price.ask/osmosis_price.bid)*10000
        return entry_spread, exit_spread


    @staticmethod
    def get_binance_price(symbol: str = "ATOMUSDT"):
        price_data = requests.get("https://fapi.binance.com/fapi/v1/ticker/bookTicker?symbol={}".format(symbol)).json()
        bid_ask = BidAskPrice(bid_price= price_data['bidPrice'], ask_price= price_data['askPrice'])
        return bid_ask

ipdb.set_trace()
ENV_FILE_DIR = os.path.join(CURR_DIR.replace("examples", "") , "envs/strategy.env")
strategy_obj = NewStrategyInstance(ENV_FILE_DIR)
strategy_obj.strategy_data()
