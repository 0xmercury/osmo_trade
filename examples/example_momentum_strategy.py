""""
High Frequency Momentum Strategy

This script demonstrates an implementation of the High Frequency Momentum trading strategy using a module and its functions.
The strategy involves comparing the historical price data for each block to the current block's price data in order to determine whether to take a long position or close an existing long position.
To facilitate this, we create a history data queue to keep track of the most recent n blocks of data.

Algorithm:
- Initialize a history data queue with the last n blocks of data
- At each iteration:
    - Compare the price data for each block in the queue to the current block's price data
    - If the current block's price data is greater than all the historical block price data, take a long position
    - If the current block's price data is less than all the historical block price data and we have a long position, close our position
    - Discard the oldest data from our history data queue and add the current block data for the next iteration

Example:
- Use pool 678 (Osmo/Usdc pool)

To run this script, you need to define your mnemonic key and RPC URL, LCD URL, and gRPC URL in the strategy.env file, which can be found in the envs/ directory of this repository.

    # Import necessary modules and functions

    # Define mnemonic key and RPC URL, LCD URL, and gRPC URL

    # Define the size of the history data queue (n)

    # Initialize the history data queue with the last n blocks of data

    # Implement the trading strategy

    # Close any existing positions at the end of the script

"""

import ipdb
import os
import time
import logging
from osmo_trade import DataFeed
from osmo_trade import create_osmo_wallet
from osmo_trade import check_dir
from decimal import Decimal
from dotenv import load_dotenv
from osmo_trade.pools import Coin, Decimal, SwapAmountInRoute
from osmo_trade import DataFeed, HostPort, TransactionBuild, SwapAmountInRoute, Coin
from osmo_trade import create_osmo_wallet, check_dir, grpc_connection, wallet_balance


class NewStrategyInstance:
    def __init__(self, env_file_path: str):
        load_dotenv(env_file_path)
        self.log_file: str = os.environ.get("LOG_FILE")
        self.mnemonic: str = os.environ.get("MNEMONIC")
        self.rpc_url: str = os.environ.get("RPC_URL")
        self.rest_url: str = os.environ.get("REST_URL")
        self._host_port: HostPort = HostPort(host=os.environ.get(
            "gRPC_host"), port=os.environ.get("gRPC_port"), ssl=True)
        self._grpc_ob = grpc_connection(self._host_port)
        self.wallet = create_osmo_wallet(self.mnemonic, self._host_port)
        self.pool_id: int = 678
        self.token_0_amount: Decimal = Decimal(10)
        self.token_1_amount: Decimal = Decimal(100)
        self.interval: int = 15
        self._datafeed = DataFeed(pool_id=self.pool_id, interval=self.interval, token_0_amount=self.token_0_amount,
                                  token_1_amount=self.token_1_amount, rpc_url=self.rpc_url, grpc_con=self._grpc_ob)

        # Set up logging
        check_dir(self.log_file.split("/")[0])
        logging.basicConfig(filename=os.environ.get(
            "LOG_FILE"), encoding='utf-8', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())

    '''
        This is a function to maintain history queue data this function call only one time intially
       
            get_multiple_block_bid_ask_data() function will need at least 1 parameter
                1). _total_block_data (eg: 1 or 2) => here you give the number how many old block data you want to keep in yout historu queue.

    '''

    def get_multiple_block_bid_ask_data(self, _total_block_data: int):

        datafeed = self._datafeed
        old_block_height = 0
        new_block_height = 0
        historical_price_data_queue = list()
        count = 1

        print("\n\n**** Fetching data of multiple block to maintain history.\nTotal block data we keep as history data are {}".format(_total_block_data))

        while True:

            try:

                if len(historical_price_data_queue) < _total_block_data:
                    reserve, block_height = datafeed.get_pool_reserves(
                        pool_ids=[self.pool_id])
                    new_block_height = block_height
                    if old_block_height != new_block_height:
                        print("Working on block: ", count)
                        bid_ask_data = datafeed._bid_ask_calculation(
                            pool_id=self.pool_id, token_0=self.token_0_amount, token_1=self.token_1_amount, pools_dict=reserve)
                        historical_price_data_queue.append(
                            {'bid': bid_ask_data.bid, 'ask': bid_ask_data.ask, 'block_heigh': block_height})
                        old_block_height = new_block_height
                        count += 1
                else:
                    break
                time.sleep(0.5)
            except Exception as ex:
                print("Getting error:: ", str(ex))
                ipdb.set_trace()

        return historical_price_data_queue

    '''
        This is a function to get current block data and this will be called at every iteration
       
            get_current_block_bid_ask_data() function will need  0 parameter
    '''

    def get_current_block_bid_ask_data(self):

        datafeed = self._datafeed

        reserve, block_height = datafeed.get_pool_reserves(
            pool_ids=[self.pool_id])
        new_height = block_height

        bid_ask_data = datafeed._bid_ask_calculation(
            pool_id=self.pool_id, token_0=self.token_0_amount, token_1=self.token_1_amount, pools_dict=reserve)

        return reserve, bid_ask_data, new_height

    '''
        This is our main strategy function   
    '''

    def run_strategy(self, datafeed: DataFeed = None):
        if datafeed is None:
            datafeed = self._datafeed

        historical_price_data_queue = list()        # store old block data
        # here you can define how many old block data ypu want to keep as a history
        historicl_old_block_point = 3
        old_block_height = 0                        # store always last block height
        new_block_height = 0                        # store always latest block height
        # Flag to check whether we have taken a position or not
        is_long_position = False

        print("\nwallet address: ", self.wallet.address)

        # define tx object to broadcast txs.
        tx = TransactionBuild(account=self.wallet, _host_port=self._host_port)

        # datafeed.get_pool_assets is return the pool assets according to pool id
        # ['ibc/D189335C6E4A68B513C10AB227BF1C1D38C746766278BA3EEB4FB14124F1D858', 'uosmo']
        pool_assets = datafeed.get_pool_assets(pool_id=self.pool_id)
        print("\nPool assets: ", pool_assets)

        print("\nhistorical_price_data_queue", historical_price_data_queue)

        historical_price_data_queue = self.get_multiple_block_bid_ask_data(
            historicl_old_block_point)

        print("\nhistorical_price_data_queue",
              historical_price_data_queue, len(historical_price_data_queue))

        while True:

            try:

                reserve, bid_ask_data, new_block_height = self.get_current_block_bid_ask_data()

                if old_block_height != new_block_height:

                    all_token_balance = wallet_balance(
                        wallet_address=self.wallet.address, grpc_ob=self._grpc_ob, token_data_json=datafeed._all_token_decimal_data)
                    print("\n\n*************** New Block Start*************\n\n")
                    print("Old Height :{}, New Height: {}".format(
                        old_block_height, new_block_height))
                    print("bid_ask data::", bid_ask_data)

                    for token_balance in all_token_balance:
                        print("Token Symbol: {}, Amount: {}, Denom: {}".format(
                            token_balance.symbol, token_balance.amount,  token_balance.denom))

                    if bid_ask_data.ask > historical_price_data_queue[0]['ask'] and bid_ask_data.ask > historical_price_data_queue[1]['ask'] and bid_ask_data.ask > historical_price_data_queue[2]['ask'] and not is_long_position:
                        print("Go For long Position")

                        routes = [SwapAmountInRoute(
                            pool_id=self.pool_id, denom=pool_assets[1])]
                        asset_balance = [
                            item for item in all_token_balance if item.denom == pool_assets[0]][0]
                        tx_hash = tx.broadcast_exact_in_transaction(routes=routes, token_in=Coin(amount=Decimal(int( int(asset_balance.amount)*0.8)), denom=pool_assets[0]), slippage=Decimal(0.002), pools=reserve)
                        print("Transaction Hash: ", tx_hash)
                        is_long_position = True

                    elif bid_ask_data.ask < historical_price_data_queue[0]['ask'] and bid_ask_data.ask < historical_price_data_queue[1]['ask'] and bid_ask_data.ask < historical_price_data_queue[2]['ask'] and is_long_position:
                        print("Left long Position")

                        routes = [SwapAmountInRoute(
                            pool_id=self.pool_id, denom=pool_assets[0])]
                        asset_balance = [
                            item for item in all_token_balance if item.denom == pool_assets[1]][0]
                        tx_hash = tx.broadcast_exact_in_transaction(routes=routes, token_in=Coin(amount=Decimal(int(
                            int(asset_balance.amount)*0.8)), denom=pool_assets[1]), slippage=Decimal(0.002), pools=reserve)
                        print("Transaction Hash: ", tx_hash)
                        is_long_position = False

                    print("\nLong Position:", is_long_position)
                    historical_price_data_queue.append(
                        {'bid': bid_ask_data.bid, 'ask': bid_ask_data.ask, 'block_heigh': new_block_height})
                    historical_price_data_queue.pop(0)

                    print("\nhistorical_price_data_queue",
                          historical_price_data_queue)

                    old_block_height = new_block_height
                    time.sleep(3)

            except Exception as ex:
                print("Got an error: ", str(ex))


ipdb.set_trace()
strategy_obj = NewStrategyInstance("envs/strategy.env")
strategy_obj.run_strategy()
