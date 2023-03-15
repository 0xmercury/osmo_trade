***
## About Example Strategy

**_CEX-DEX Arb_**

##### For code [click here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py)

This script demonstrates an implementation of the CEX-DEX arb specifically b/w Binance & Osmosis DEX taken ATOM as the token, using the SDK and its functions. The strategy involves fetching the bid/ask block by block from Osmosis and Binance together then calculate the spread b/w Ask & Bid of both the exchanges. We'll explain in detail below. 

Algorithm:
- At each iteration:
    - Fetch the pool reserves of ATOM/OSMO, USDC/OSMO pool and calculate the bid/ask of the atom-usdc by combining both the pools.
    - Fetch the Bid/Ask of ATOMUSDT on Binance.
    - Calculate the entry_spread & exit_spread b/w the prices of both the exchanges.
    - If entry_spread > 10 bps then we'll swap USDC -> ATOM position. 
    - IF exit_spread > 0 bps then we'll swap back ATOM -> USDC position.

In the example script, we are using pool_id= 678 (USDC/OSMO) pool and pool_id= 1 (ATOM/OSMO) pool.

To run this script, you need to define your mnemonic key and RPC URL, LCD URL, and gRPC URL in the strategy.env file, which you need to specifically as explained in [README.md](https://github.com/0xmercury/osmo_trade#mandatory-step).  

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
    import in our example script [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L5)

    ```python
        from osmo_trade import DataFeed, HostPort, TransactionBuild, SwapAmountInRoute, BidAskPrice, Coin, ROOT_DIR, CURR_DIR
        from osmo_trade import create_osmo_wallet, check_dir, grpc_connection, wallet_balance
    ```

4. After that, we inilize the initial variable in our init function of class [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L12).

    In this function: 
    * we read the config file and initialize the required variables:
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
                self.pool_id = [678, 1]
                # whatever pool is in the start will be considered as token_0 and then token_1.
                # In this case, pool_id = [678, 1] so token_0 is USDC & token_1 is ATOOM.
                self.token_0_amount = 100 # amount of token 0 you want to use in the pricing data calculation
                self.token_1_amount = 10 # amount of token 1 you want to use in the pricing data calculation
                
                self._datafeed = DataFeed(pool_id= self.pool_id, token_0_amount= self.token_0_amount, token_1_amount= self.token_1_amount, rpc_url= self.rpc_url, grpc_con= self._grpc_ob)
            ```
5.  Then, we check if the directory where our log file will be created is available or not. If the directory is not present, this function will create it and set the logging file configuration, which you can find [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L31).
    
    ```python
        path, file = os.path.split(self.log_file)
        check_dir(path)
        logging.basicConfig(filename= self.log_file, encoding='utf-8', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())
    ```

6. After that, we run the main function  [**strategy_core()**](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L61) from where we write our strategy code. Our strategy has two parts:

    1. We start by collecting the pool reserves of pool 678 & 1 then calculating the bid/ask of ATOM/USDC by comininb both the pools. We've assumed to calculate the bid/ask using 100 USDC & 10 ATOM. [Here's the function](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L80)
    
        ```python
            osmosis_bid_ask = datafeed._bid_ask_calculation( self.pool_id, self.token_0_amount, self.token_1_amount, pool_reserves_dict, reverse=False)
        ```
        
        After which we fetch the binance ATOMUSDT bid/ask [using this](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L54)
        
        ```python
            binance_bid_ask = self.get_binance_price()
        ```
        
        Following which, we simply calculate the spread for [entry & exit conditions](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L47)
        
        ```python
            entry_spread, exit_spread = self.signal_using_spread( binance_bid_ask, osmosis_bid_ask)
        ```
        
        Then, we run the loop for every block and check the signal [here](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L81)
        
        ```python
            if entry_spread > 10 and not is_long_position:
            elif exit_spread > 0 and is_long_position:
        ```
    
    2.   Once we get the signal, we make the transaction using the transaction builder class of the sdk that we imported earlier. Then we simply define & make the transaction [using the tx object](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_cex_dex/example_cex_dex.py#L87)
        
        ```python
            from osmo_trade import TransactionBuild
            # define tx object to broadcast txs.
            tx = TransactionBuild(account= self.wallet, _host_port = self._host_port)
            tx_hash = tx.broadcast_exact_in_transaction(routes=routes, token_in=Coin(amount=int(
                    asset_balance.amount*0.98), denom=usdc_pool_assets[0]), slippage=Decimal(0.002), pools=pool_reserves)                  
        ```
