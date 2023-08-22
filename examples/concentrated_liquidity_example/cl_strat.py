# Importing the necessary modules
from osmo_trade.concentrated_liquidity import (get_pools, fetch_account_data, read_input_json, 
                                               create_position_transaction, Account, HTTPClient, 
                                               rest_endpoint, withdraw_position_transaction, 
                                               query_user_position, add_to_position_transaction)
import json
import time
import math

# Loading private information from a JSON file
with open("private_info.json", "r") as file:
    data = json.load(file)

mnemonic_key = data["mnemonic_key"]
osmo_address = data["osmo_address"]


# Fetching pool details
pools = get_pools()

keys = ["token0", "token1", "current_tick"]

# Dictionary to store pool information
pool_info = {}

# Extracting and storing the pool information in the pool_info dictionary
for pool in pools['pools']:
    pool_id = int(pool["id"])
    temp_dict = {}  # Temporary dictionary to store pool details
    for key in keys:
        temp_dict[key] = pool[key]  
    pool_info[pool_id] = temp_dict  

#print(pool_info)

# Function to create a position within a specified range
def createPositionInRange(ppercent_range, pool_id, current_tick, lower_tick, upper_tick, amount0, amount1, token_min_amount0, token_min_amount1):
    # Fetching account data
    account_number, sequence = fetch_account_data(osmo_address)
    
    # Formatting the amounts
    amount0 = str(int(amount0))
    amount1 = str(int(amount1))
    token_min_amount0 = str(int(token_min_amount0))
    token_min_amount1 = str(int(token_min_amount1))
    print( "token_amounts",amount1, amount0, token_min_amount1, token_min_amount0)
    
    # Creating an account instance
    account = Account(
        seed_phrase=mnemonic_key,
        account_number=account_number,
        next_sequence=sequence,
        hrp="osmo",
        protobuf='osmosis'
    )
    print("account number, sequence", account_number, sequence)
    
    # Creating a transaction to create a position
    create_position_tx = create_position_transaction(
        account,
        pool_id=pool_id,
        sender_address=osmo_address,
        lower_tick=lower_tick,
        upper_tick=upper_tick,
        tokens_provided=[
            {
                "amount": amount1,
                "denom": pool_info[pool_id]['token1']
            },
            {
                "amount": amount0,
                "denom": pool_info[pool_id]['token0']
            }
        ],
        token_min_amount0=token_min_amount0,
        token_min_amount1=token_min_amount1
    )
    client = HTTPClient(api=rest_endpoint)
    create_position_result = client.broadcast_transaction(transaction=create_position_tx)
    print("Create Position Result:", create_position_result)


# Function to check and update positions every hour
def hourly_check_and_update_position(osmo_address, percent_range):
    while True:  # Infinite loop to keep checking
        for data in input_data:
            pool_id = data["pool_id"]
            current_tick = int(pool_info[pool_id]['current_tick'])
            lower_tick = int(current_tick - current_tick * percent_range / 100)  # these values you can take from input file also 
            upper_tick = int(current_tick + current_tick * percent_range / 100)
            lower_tick = lower_tick - lower_tick%100
            upper_tick = upper_tick - upper_tick%100
            print("current_tick , lower_tick, upper_tick",current_tick,lower_tick, upper_tick)
            
            amount0 = data['amount0']
            amount1 = data['amount1']
            token_min_amount0 = data['token_min_amount0']
            token_min_amount1 = data['token_min_amount1']
            
            # Querying user positions
            user_positions = query_user_position(osmo_address, pool_id)
            for position in user_positions['positions']:
                # Adjusting the tick values
                # Checking if the current tick is out of the position's range
                print("position_ticks", int(position['position']['lower_tick']) , int(position['position']['upper_tick']))
                if 1:
                    value = int(position["position"]["liquidity"].split(".")[0]) * int(1e18)
                    liquidity = str(value)
                    print(liquidity)

                    # Giving some time for the previous transaction to complete
                    time.sleep(10)
                    
                    # Fetching account data
                    account_number, sequence = fetch_account_data(osmo_address)
                    
                    # Creating an account instance
                    account = Account(
                        seed_phrase=mnemonic_key,
                        account_number=account_number,
                        next_sequence=sequence,
                        hrp="osmo",
                        protobuf='osmosis'
                    )

                    # Withdrawing the position
                    withdraw = withdraw_position_transaction(account, int(position['position']['position_id']), osmo_address, liquidity)
                    client = HTTPClient(api=rest_endpoint)
                    withdraw_result = client.broadcast_transaction(transaction=withdraw)
                    print(withdraw_result)

                    # Giving some time for the withdrawal transaction to complete
                    time.sleep(10)

                    # Creating a new position in the specified range
                    createPositionInRange(percent_range, pool_id, current_tick, lower_tick, upper_tick, amount0, amount1, token_min_amount0, token_min_amount1)
            
            # If there are no user positions, create a new one
            if len(user_positions["positions"]) < 1:
            	time.sleep(10)
                createPositionInRange(percent_range, pool_id, current_tick, lower_tick, upper_tick, amount0, amount1, token_min_amount0, token_min_amount1)

        # Wait for an hour before checking again
        time.sleep(3600)

if __name__ == "__main__":
    percent_range = 1
    input_data = read_input_json("input_data.json")
    hourly_check_and_update_position(osmo_address, percent_range)
