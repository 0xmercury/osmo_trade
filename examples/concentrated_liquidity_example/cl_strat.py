from osmo_trade.concentrated_liquidity import get_pools,fetch_account_data,read_input_json,create_position_transaction,Account,HTTPClient,rest_endpoint,withdraw_position_transaction,query_user_position,add_to_position_transaction
import json
import time
import math
with open("private_info.json", "r") as file:
	data = json.load(file)

mnemonic_key = data["mnemonic_key"]
osmo_address = data["osmo_address"]

print(mnemonic_key)
print(osmo_address)


pools = get_pools()

keys = ["token0", "token1", "current_tick"]

pool_info = {}

for pool in pools['pools']:
	pool_id = int(pool["id"])
	temp_dict = {}  # Create an empty dictionary for each pool
	for key in keys:
		temp_dict[key] = pool[key]  # Populate the dictionary with key-value pairs from the pool
	pool_info[pool_id] = temp_dict  # Use pool ID as the key and the populated dictionary as its value

print(pool_info)


def createPositionInRange(ppercent_range,pool_id,current_tick,lower_tick,upper_tick,amount0,amount1,token_min_amount0,token_min_amount1):
	 
		account_number, sequence = fetch_account_data(osmo_address)
		amount0 = str(int(amount0))
		amount1 = str(int(amount1))
		token_min_amount0 = str(int(token_min_amount0))
		token_min_amount1 = str(int(token_min_amount1))
		print(amount1,amount0,token_min_amount1,token_min_amount0)
		account = Account(
				seed_phrase=mnemonic_key,
				account_number=account_number,
				next_sequence=sequence,
				hrp="osmo",
				protobuf='osmosis'
		)
		print(account_number,sequence)
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
def hourly_check_and_update_position(osmo_address, percent_range):
	while True:
		for data in input_data:
			pool_id = data["pool_id"]
			current_tick = int(pool_info[pool_id]['current_tick'])
			lower_tick = int( current_tick - current_tick*percent_range/100)
			upper_tick = int(current_tick + current_tick*percent_range/100)
			print(lower_tick,upper_tick)
			amount0 = data['amount0']
			amount1 = data['amount1']
			token_min_amount0 = data['token_min_amount0']
			token_min_amount1 = data['token_min_amount1']
			user_positions = query_user_position(osmo_address,pool_id)
			for position in user_positions['positions']:
				current_tick = int(pool_info[int(position['position']['pool_id'])]['current_tick'])
				lower_tick = int(current_tick - current_tick * percent_range / 100)
				upper_tick = int(current_tick + current_tick * percent_range / 100)

				lower_tick = lower_tick - lower_tick%100
				upper_tick = upper_tick - upper_tick%100
				from decimal import Decimal
				print(current_tick,lower_tick,upper_tick)
				# 2. Check if the position's ticks are out of range
				if  current_tick < int(position['position']['lower_tick'])  or  current_tick > int(position['position']['upper_tick']) :
					value = float(position["position"]["liquidity"])*float(1e18)
					value = int(value)
					print(value)
					liquidity = str(value)
					print(liquidity)
					time.sleep(10)
					account_number, sequence = fetch_account_data(osmo_address)

					account = Account(
							seed_phrase=mnemonic_key,
							account_number=account_number,
							next_sequence=sequence,
							hrp="osmo",
							protobuf='osmosis'
					)
					withdraw = withdraw_position_transaction(account,int(position['position']['position_id']),osmo_address,liquidity)
					client = HTTPClient(api=rest_endpoint)
					withdraw_result = client.broadcast_transaction(transaction=withdraw)
					print(withdraw_result)
					# need to sleep beofre sending another transaction
					time.sleep(10)
					createPositionInRange(percent_range,pool_id,current_tick,lower_tick,upper_tick,amount0,amount1,token_min_amount0,token_min_amount1)
			if len(user_positions["positions"]) < 1:
				time.sleep(10)
				account_number, sequence = fetch_account_data(osmo_address)
				account = Account(
						seed_phrase=mnemonic_key,
						account_number=account_number,
						next_sequence=sequence,
						hrp="osmo",
						protobuf='osmosis'
				)
				createPositionInRange(percent_range,pool_id,current_tick,lower_tick,upper_tick,amount0,amount1,token_min_amount0,token_min_amount1)

		time.sleep(3600)

if __name__ == "__main__":
	percent_range = 1
	input_data = read_input_json("input_data.json")
	hourly_check_and_update_position(osmo_address, percent_range)
