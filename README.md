
osmo_trade: Making the trading experience seamless.
====================================

[![License](https://img.shields.io/badge/License-Apache%202.0-informational.svg)](https://github.com/0xmercury/osmo_trade/blob/master/LICENSE.md)

**osmo_trade** is an open source python SDK made from the perspective of Algorithmic Traders. It is built to trade on Osmosis DEX powered by **Cosmos SDK** and **Tendermint** as the consensus engine. 

This code is free and publicly available under the Apache 2.0 open source license!

Features of osmo_trade as a **package**: 
- Very easy to set up any alpha based strategy on osmosis DEX.
- Modular in nature. We can add any new feature coming on osmosis DEX like Concentrated liquidity without altering the exisiting code.
- With a bit of customizations in regards to performance, it also can be used CEX-DEX arb which generates majority of the volume on the DEX.

Components in osmo_trade:
* [DataFeed](https://github.com/0xmercury/osmo_trade/blob/master/osmo_trade/data_feed.py): DataFeed is the class to get the data from the blocks mined already. We haven't configured osmo_trade to have the mempool transactions as of now.
* [TransactionBuilder](https://github.com/0xmercury/osmo_trade/blob/master/osmo_trade/transaction_build.py): This class is used to build your transactions however you want. It'll return the **txn_hash, logs, code** to tell the user whether the transaction is successful.
* [Strategy](https://github.com/0xmercury/osmo_trade/blob/master/examples/example_momentum_strategy/example_momentum_strategy.py): We've setup an example code to really explain what each component is doing. And that is how user just need to make a script like this which will contain the strategy logic.

Detailed documentation can be found in the examples directory where we try to explain each component of the SDK in much detail.

## Installation

```python 
pip install osmo_trade 
```

### Note:
If you want to run by customizing the SDK itself. Then git clone the repo, make your changes and do:

`` pip install .`` in the cloned directory.

## Mandatory Step

- First of all, User have to define the env file in their current working directory with the following fields:

  * MNEMONIC
  * RPC_URL
  * gRPC_host and gRPC_port
  * REST_URL

  A very good example of env file can be found [here](https://github.com/0xmercury/osmo_trade/blob/master/envs/strategy.env)

### FAQ:
What to do when user is getting the following error after installing the package for the first time:
* when you're getting an error that says mpz object has no to_bytes() attributes
  * ``pip uninstall gmpy2``
