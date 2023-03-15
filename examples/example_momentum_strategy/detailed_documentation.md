***
## About Example Strategy

**_Momentum Strategy_**

##### For code [click here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py)

This script demonstrates an implementation of the Momentum trading strategy using the SDK and its functions. The strategy involves comparing the historical price data for each block to the current block's price data in order to determine whether to take a long position or close an existing long position. To facilitate this, we create a history data queue to keep track of the most recent n blocks of data.

Algorithm:
- Initialize a history data queue with the last n blocks of data
- At each iteration:
    - Compare the price data for each block in the queue to the current block's price data
    - If the current block's price data is greater than all the historical block price data, take a long position
    - If the current block's price data is less than all the historical block price data and we have a long position, close our position
    - Discard the oldest data from our history data queue and add the current block data for the next iteration

In the example script, we are using pool 678 (Osmo/Usdc pool).

To run this script, you need to define your mnemonic key and RPC URL, LCD URL, and gRPC URL in the strategy.env file, which you need to specifically as explained in README.md


    # Import necessary modules and functions

    # Define mnemonic key and RPC URL, LCD URL, and gRPC URL

    # Define the size of the history data queue (n)

    # Initialize the history data queue with the last n blocks of data

    # Implement the trading strategy

    # Close any existing positions at the end of the script


### Step to run exmaple strategy and SDK use.

The **SDK** is a Python library that helps you interact with the **Osmosis** blockchain. The SDK provides a set of APIs and classes that abstracts away low-level details of interacting with the blockchain, making it easy for developers to focus on building their applications.

You can use the SDK to do the following tasks:

* Query blockchain data
* Send transactions
* Create and manage wallets
* Interact with Osmosis's Automated Market Maker (AMM)

The SDK is built primarily using gRPC which provides efficient mode of communication i.e. faster querying data on-chain, faster sending txns etc. The SDK uses mospy-wallet, osmosis_protobuf which have been tested in production for several months now.

The SDK also includes a **DataFeed** class that provides a high-level interface for retrieving current and historical pricing data from the Osmosis blockchain. You can use this class to easily build trading bots and other applications that require real-time pricing data.

To get started with the SDK, you can follow these steps:

1. Install the osmosis-sdk package:

    ```bash
        pip install osmo_trade
    ```


2. Set up your environment:

    Create a **.env** file with the following environment variables [this file:](https://github.com/0xmercury/osmo_trade/blob/master/envs/strategy.env)
    ```makeile
        MNEMONIC="<your mnemonic>"
        RPC_URL="<osmosis rpc url>"
        gRPC_HOST="<osmosis grpc host>"
        gRPC_PORT=<osmosis grpc port>
        REST_URL="<osmosis rest url>"
    ```
    You can get your Osmosis RPC URL and REST URL by running a full node or using a public endpoint like **https://api.osmosis.zone**. You can get the gRPC host and port from the app.toml file in your Osmosis node's config directory.

    Note: Make sure you keep your mnemonic secret and do not share it with anyone.


3. Import the SDK modules and classes you need: :
    import in our example script [here](https://github.com/0xmercury/osmo_trade/blob/master/example_momentum_strategy.py#L39)

    ```python
        from osmo_trade import create_osmo_wallet
        from osmo_trade import check_dir
        from osmo_trade._pools import Coin, SwapAmountInRoute
        from osmo_trade import DataFeed, HostPort, TransactionBuild, SwapAmountInRoute, Coin, ROOT_DIR, CURR_DIR
        from osmo_trade import create_osmo_wallet, check_dir, grpc_connection, wallet_balance
    ```

4. After that, we inilize the initial variable in our init function of class [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L48).

    In this function: 
    * we read config file [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L49)
    * set varibales value [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L52):
        * define LCD, RPC and gRPC URL and Create a gRPC connection object.
            ```python
                self.rpc_url = os.environ.get("RPC_URL")
                self.rest_url = os.environ.get("REST_URL")
                self.grpc_host = os.environ.get("gRPC_HOST")
                self.grpc_port = os.environ.get("gRPC_PORT")
                self.grpc_ob = grpc_connection(grpc_host, grpc_port)
            ``` 
            You can use the **grpc_connection** function to create a gRPC connection object that can be used to interact with the Osmosis blockchain.
        * set wallet mnemonic key.
            ```python
                self.mnemonic = os.environ.get("MNEMONIC")
          ```
        * Create wallet object by using create_osmo_wallet of SDK
          ```python
          
            self.wallet = create_osmo_wallet(self.mnemonic, self._host_port)
          ```
        * Create a DataFeed object:
            ```python
                self.pool_id = "<your pool id>"
                self.interval = 30 # time interval between data points in seconds
                self.token_0_amount = 100 # amount of token 0 you want to use in the pricing data calculation
                self.token_1_amount = 100 # amount of token 1 you want to use in the pricing data calculation
                
                self._datafeed = DataFeed(pool_id= self.pool_id, interval= self.interval, token_0_amount= self.token_0_amount, token_1_amount= self.token_1_amount, rpc_url= self.rpc_url, grpc_con= self._grpc_ob)
            ```
5.  Then, we check if the directory where our log file will be created is available or not. If the directory is not present, this function will create it and set the logging file configuration, which you can find [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L68).
    
    ```python
        path, file = os.path.split(self.log_file)
        check_dir(path)
        logging.basicConfig(filename= self.log_file, encoding='utf-8', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())
    ```

6. After that, we run the main function  [**run_strategy()**](https://github.com/0xmercury/osmo_trade/blob/master/example_momentum_strategy.py#L214) from where we write our strategy code. You can find the function definition [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L140). Our strategy has two parts:
    
    1. First part: In this part, we collect bid-ask data of the last three blocks and maintain a queue to keep a history of signals. We use a self-defined function, which you can find [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L164) to generate historical price data queue. You can find the function definition [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L82).
        
        ```python
            historical_price_data_queue = self.get_multiple_block_bid_ask_data(historicl_old_block_point)
        ```
    
        Once the historical data is generated, we move to the next step and fetch the current or latest block height data by using another self-defined function, which you can find [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L174)
    
        ```python
        reserve, bid_ask_data, new_block_height = self.get_current_block_bid_ask_data()
        ``` 
        You can find the function definition [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L123). In both the functions, **get_current_block_bid_ask_data()** and **get_multiple_block_bid_ask_data()**, we use an sdk function to get reserve and bid-ask data.
        
        ```python

        reserve, block_height = datafeed.get_pool_reserves(pool_ids=[self.pool_id])

        bid_ask_data = datafeed._bid_ask_calculation(pool_id=self.pool_id, token_0=self.token_0_amount, token_1=self.token_1_amount, pools_dict=reserve)
        ```
        Then, we run the loop for every block and and and compare the latest block data with the historical data and find the signal [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L189)
    
    2.   Second part: Once we get the signal, we make the transaction using the transaction builder class of the sdk that we imported earlier, which you can find [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L42). Then, we define the transaction builder object [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L155)Finally, we make the transaction using this function [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy.py#L196)
    
        ```
        from osmo_trade import TransactionBuild

        # define tx object to broadcast txs.
        tx = TransactionBuild(account= self.wallet, _host_port = self._host_port)

        tx_hash = tx.broadcast_exact_in_transaction(routes= routes, token_in= Coin(amount= Decimal(int(int(asset_balance.amount)*0.8)), denom= pool_assets[1]), slippage= Decimal(0.002),pools= reserve)                  
        ```
