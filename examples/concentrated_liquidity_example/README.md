
## README for Osmosis CL Automation Script

### Overview:

This script aims to automate operations related to the Osmosis blockchain CL, such as:

1. Fetching pool data.
2. Retrieving account details.
3. Creating, withdrawing, and adding to positions.

### Prerequisites:

- Required libraries: `requests`, `mospy`, `pandas`, `json`, `cosmospy_protobuf`
  
  Install these using pip:

  ```bash
  pip install requests mospy pandas cosmospy_protobuf
  ```

### Setup:

1. Ensure that you have a `private_info.json` file in the same directory as the script. The file should contain:

   ```json
   {
       "mnemonic_key": "YOUR_MNEMONIC_KEY",
       "osmo_address": "YOUR_STRIDE_ADDRESS"
   }
   ```

2. Ensure that you have an `input_data.json` file in the same directory. This file should contain the necessary information to create positions.
### `input_info.json` Format:

This JSON file contains an array of position data that the script uses to create, withdraw, or add to positions. Each object in the array represents a position and has the following properties:

- `pool_id`: The ID of the pool.
- `position_id`: The ID of the position. (this is optional , in case query postion doesn't work you can use this)
- `lower_tick`: The lower tick value.
- `upper_tick`: The upper tick value.
- `amount0`: Amount of the first token.
- `amount1`: Amount of the second token.
- `token_min_amount0`: Minimum amount of the first token.
- `token_min_amount1`: Minimum amount of the second token.

Example:

```json
[
    {
        
        "pool_id": 1066,
        "position_id": 17706,
        "lower_tick": 100055000,
        "upper_tick": 105079000,
        "amount0": "5000000",
        "amount1": "3829300974491989575",
        "token_min_amount0": "2075000",
        "token_min_amount1": "1033568450129689835"
    }

    
]

```

Concentrated Liquidity Strategy (cl_strat.py)

This script provides an automated strategy for managing concentrated liquidity positions on the Osmosis platform.

Overview
The script performs the following operations:
  Fetches the current pool data.
  Checks user's positions hourly.
  Updates the positions based on the specified percent range. If the current tick is out of the user's range, it withdraws the position and creates a new one.
Requirements
  A private_info.json file containing your mnemonic key, cosmos address, and stride address.
  An input_data.json file containing information about your desired liquidity positions.

Note: refere to below README.md file for tick and amount calculations
https://github.com/osmosis-labs/osmosis/tree/main/x/concentrated-liquidity



Another function you can use:


## Add to Position Transaction Function

### Overview

The `add_to_position_transaction` function allows users to increase their stake in a specific liquidity position on the Osmosis platform. By using this function, you can add more tokens to your existing position.

### Function Parameters

- `account`: An `Account` object that contains the user's account details.
- `amount0`: The amount of the first token you want to add.
- `amount1`: The amount of the second token you want to add.
- `position_id`: The ID of the liquidity position you want to add to.
- `sender_address`: The address of the user sending the tokens.
- `token_min_amount0`: The minimum amount of the first token that must be added for the transaction to be valid.
- `token_min_amount1`: The minimum amount of the second token that must be added for the transaction to be valid.

### How to use

1. Ensure you have initialized an `Account` object with your account details.
2. Call the function with the desired parameters:

```python
account = Account(
    seed_phrase="your_mnemonic_key",
    account_number="your_account_number",
    next_sequence="your_next_sequence",
    hrp="osmo",
    protobuf='osmosis'
)

you will get account number and sequence number from this

account_number, sequence = fetch_account_data(osmo_address)


tx = add_to_position_transaction(
    account=account,
    amount0="desired_amount0",
    amount1="desired_amount1",
    position_id="your_position_id",
    sender_address="your_sender_address",
    token_min_amount0="minimum_required_amount0",
    token_min_amount1="minimum_required_amount1"
)
```

3. Broadcast the returned transaction to the network to execute the operation.
( client = HTTPClient(api=rest_endpoint)
  create_position_result = client.broadcast_transaction(transaction=create_position_tx)
)

Note : All the above steps you will undestand once you check the cl_strat.py file also. 
### Note

- Ensure you set the correct `amount0`, `amount1`, and minimum amounts for the transaction to be valid.
- Ensure you have sufficient funds in your account to add to the position and cover the transaction fee.