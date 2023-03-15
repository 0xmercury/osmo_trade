import codecs
import base64
import datetime
import requests
import json
from decimal import Decimal
from multiprocessing.pool import ThreadPool
from google.protobuf.json_format import MessageToDict
import osmosis_protobuf.osmosis.gamm.v1beta1.query_pb2 as query_gamms
import osmosis_protobuf.osmosis.gamm.pool_models.balancer.balancerPool_pb2
import osmosis_protobuf.osmosis.gamm.pool_models.balancer.tx.tx_pb2
import osmosis_protobuf.osmosis.gamm.pool_models.stableswap.stableswap_pool_pb2
import osmosis_protobuf.osmosis.gamm.pool_models.stableswap.tx_pb2
import osmosis_protobuf.osmosis.gamm.v1beta1.query_pb2 as query_pb
import osmosis_protobuf.osmosis.gamm.v1beta1.query_pb2_grpc as query_pb_grpc
from osmo_trade._pools import BalancerPool, Coin, StableswapPool, BidAskPrice, SwapAmountInRoute
from osmo_trade.config_data import get_incentive_data, json_file_update, get_block_height


class DataFeed:
    """
    token_0_amount: amount of token_0 to calculate bid/ask of tokens.
    token_1_amount: amount of token_1 to calculate bid/ask of tokens.
    """

    def __init__(self, pool_id: int, token_0_amount: Decimal, token_1_amount: Decimal, rpc_url: str, grpc_con, interval: int = None):
        self._pool_id: int = pool_id
        self._token_0_amount: Decimal = token_0_amount
        self._token_1_amount: Decimal = token_1_amount
        self._interval = interval
        self._rpc = rpc_url
        self._grpc_ob = grpc_con
        self._pools_stub = query_pb_grpc.QueryStub(self._grpc_ob)
        self._incentivized_pools_list: list = get_incentive_data(self._grpc_ob)
        self._all_token_decimal_data: list = json_file_update()

    def get_pool_reserves(self, pool_ids: list):
        """fetching reserves of every pool which will be needed"""
        POOL_RESERVES = {}
        block_height = get_block_height(self._grpc_ob)
        for id in pool_ids:
            grpc_pool_data = self._pools_stub.Pool(
                query_pb.QueryPoolRequest(pool_id=id))
            data = MessageToDict(grpc_pool_data)['pool']
            try:
                if data['@type'] == '/osmosis.gamm.v1beta1.Pool':
                    POOL_RESERVES[int(data['id'])] = BalancerPool(
                        data['address'], data['id'], data['poolParams'], data['poolAssets'], data['totalWeight'], block_height)
                elif data['@type'] == '/osmosis.gamm.poolmodels.stableswap.v1beta1.Pool':
                    POOL_RESERVES[int(data['id'])] = StableswapPool(
                        data['address'], data['id'], data['poolParams'], data['poolLiquidity'], data['scalingFactor'], block_height)
            except Exception as e:
                continue
        return POOL_RESERVES, block_height

    def get_pool_assets(self, pool_id: int):
        """
        fetch pool assets of a given pool_id stored in json file.
        """
        return self._all_token_decimal_data['pool_assets'][str(pool_id)]

    def historical_data(self, height: int, pool_id=None, interval: int = None, token_0_amount: Decimal = None, token_1_amount: Decimal = None) -> dict:
        if pool_id is None:
            pool_id = self._pool_id
        if interval is None:
            interval = self._interval
        if token_0_amount is None:
            token_0_amount = self._token_0_amount
        if token_1_amount is None:
            token_1_amount = self._token_1_amount
        # TODO: check condition to mention the user that only four cases are possible 5 min, 15 min, 30 min, 60 min
        interval_in_sec = interval * 60
        # Assuming each block is of 6s.
        block_skip = int(interval_in_sec/6)
        total_number_of_intervals = int((24 * 60) / interval)
        list_of_heights_based_on_intervals = []
        current_time = datetime.datetime.utcnow()
        time_series = []
        price_series = {}
        for i in range(total_number_of_intervals):
            time_series.append(current_time)
            list_of_heights_based_on_intervals.append(height)
            height -= block_skip
            current_time -= datetime.timedelta(minutes=interval)
        all_args = [(ht, pool_id, token_0_amount, token_1_amount)
                    for ht in list_of_heights_based_on_intervals]
        pool = ThreadPool()
        results = pool.starmap(
            self._send_abci_query_historical_state, all_args)
        for idx, result in enumerate(results):
            price_series[str(time_series[idx])] = result
        return price_series

    def _send_abci_query_historical_state(self, height: int, pool_id: int, token_0: Decimal, token_1: Decimal):
        """Encode and send pre-filled protobuf msg to RPC endpoint."""
        # Some queries have no data to pass.
        request_msg = query_gamms.QueryPoolRequest()
        response_msg = query_gamms.QueryPoolsResponse
        request_msg.pool_id = pool_id
        path: str = "/osmosis.gamm.v1beta1.Query/Pool"
        pool_dict = {}
        if request_msg:
            request_msg = codecs.encode(request_msg.SerializeToString(), 'hex')
            request_msg = str(request_msg, 'utf-8')
        # TODO: convert this into grpc request ``osmosis_protobuf/tendermint/abci``
        req = {"jsonrpc": "2.0", "id": "1", "method": "abci_query", "params": {
            "height": str(height), "path": path, "data": request_msg}}
        req = json.dumps(req)
        response = requests.post(self._rpc, req).json()
        if 'result' not in response:
            print(response)
        response = response['result']['response']['value']
        response = base64.b64decode(response)
        result = response_msg()
        result.ParseFromString(response)
        data = MessageToDict(result)['pools'][0]
        if data['@type'] == '/osmosis.gamm.v1beta1.Pool':
            pool_dict[int(data['id'])] = BalancerPool(
                data['address'], data['id'], data['poolParams'], data['poolAssets'], data['totalWeight'], height)
        elif data['@type'] == '/osmosis.gamm.poolmodels.stableswap.v1beta1.Pool':
            pool_dict[int(data['id'])] = StableswapPool(
                data['address'], data['id'], data['poolParams'], data['poolLiquidity'], data['scalingFactor'], height)
        # print("new height got", height)
        bid_ask_obj = self._bid_ask_calculation(
            pool_id=pool_id, token_0=token_0, token_1=token_1, pools_dict=pool_dict)
        return bid_ask_obj

    def _bid_ask_calculation(self, pool_id: int | list, token_0: Decimal, token_1: Decimal, pools_dict: dict, reverse: bool = False):
        """
        token_0 & token_1: no of tokens with which you want to calculate ask & bid. Recommended to use the figure using which you're actually going to trade. Like if you intend to trade 100 ATOM and 1000 OSMO then use token_0 = 100 & token_1 = 1000. This way you ensure that you'll get least slippages.

        - We are assuming the user will start from OSMO token
        - We define ask & bid as following:
        - ask: number of osmo needed to go swap/buy to get token_x, OSMO -> token_x
        - bid: number of osmo user get when swap/sell happends from token_x to osmo, token_x -> OSMO

        Note: reverse flag will enable to calculate bid/ask in the other asset of the pool. By default, it calculates bid/ask in terms of OSMO.
        """
        pools_list = list(pools_dict.values())
        if len(pools_list) > 1:
            pool_0 = pools_list[0]
            pool_1 = pools_list[1]
            routes = [SwapAmountInRoute(pool_0.id, pool_0.pool_assets[1].token.denom), SwapAmountInRoute(
                pool_1.id, pool_1.pool_assets[0].token.denom)]
            token_in = Coin(denom=pool_0.pool_assets[0].token.denom, amount=token_0*pow(
                10, self._all_token_decimal_data['asset_decimals'][pool_0.pool_assets[0].token.denom]))
            sell_token = self.multihop_routed_swap(
                pools_list, self._incentivized_pools_list, token_in, routes)
            routes = [SwapAmountInRoute(pool_1.id, pool_1.pool_assets[1].token.denom), SwapAmountInRoute(
                pool_0.id, pool_0.pool_assets[0].token.denom)]
            token_in = Coin(denom=pool_1.pool_assets[0].token.denom, amount=token_1*pow(
                10, self._all_token_decimal_data['asset_decimals'][pool_1.pool_assets[0].token.denom]))
            buy_token = self.multihop_routed_swap(
                pools_list, self._incentivized_pools_list, token_in, routes)
        else:
            current_pool = pools_dict[pool_id]
            routes = [SwapAmountInRoute(
                pool_id, current_pool.pool_assets[1].token.denom)]
            pool_filter = self._relevant_pools(pools_list, routes)
            token_in: Coin = Coin(
                denom=current_pool.pool_assets[0].token.denom, amount=token_0*pow(10, self._all_token_decimal_data['asset_decimals'][current_pool.pool_assets[0].token.denom]))
            sell_token = self.multihop_routed_swap(
                pool_filter, self._incentivized_pools_list, token_in, routes)
            routes = [SwapAmountInRoute(
                pool_id, current_pool.pool_assets[0].token.denom)]
            token_in: Coin = Coin(
                denom=current_pool.pool_assets[1].token.denom, amount=token_1*pow(10, self._all_token_decimal_data['asset_decimals'][current_pool.pool_assets[1].token.denom]))
            buy_token = self.multihop_routed_swap(
                pool_filter, self._incentivized_pools_list, token_in, routes)
        if reverse:
            bid_price = Decimal(sell_token.amount/(token_0 * pow( 10, self._all_token_decimal_data['asset_decimals'][sell_token.denom])))
            ask_price = Decimal( (token_1 * pow(10, self._all_token_decimal_data['asset_decimals'][buy_token.denom])) / buy_token.amount)
        else:
            ask_price = Decimal( (token_0 * pow(10, self._all_token_decimal_data['asset_decimals'][sell_token.denom]))/sell_token.amount)
            bid_price = Decimal(buy_token.amount/(token_1 * pow( 10, self._all_token_decimal_data['asset_decimals'][buy_token.denom])))
        return BidAskPrice(bid_price, ask_price)

    @staticmethod
    def _relevant_pools(pools_list: list, routes: list):
        pool_filter: list = []
        for pool in pools_list:
            for route in routes:
                if route.pool_id == pool.get_id():
                    pool_filter.append(pool)
                else:
                    continue
        return pool_filter

    @staticmethod
    def _multihop_bool(routes: list, pool_filter: list, incentivized_pools_list: list, token_in: Coin):
        """
        - the route is of length 2
        - route 1 and route 2 don't trade via the same pool
        - route 1 contains uosmo
        - both route 1 and route 2 are incentivized pools
        """
        if len(routes) != 2:
            return False
        if routes[0].pool_id == routes[1].pool_id:
            return False
        if routes[0].token_out_denom != 'uosmo':
            return False
        if routes[0].token_out_denom == token_in.denom:
            return False
        pool_0_incentive_bool = pool_filter[0].is_incentivized(
            incentivized_pools_list)
        pool_1_incentive_bool = pool_filter[1].is_incentivized(
            incentivized_pools_list)
        return pool_0_incentive_bool & pool_1_incentive_bool

    @staticmethod
    def _get_osmo_routed_multihop_total_swap_fee(routes: list, pool_filter: list):
        """
        if multihop_bool val satisfies all the conditions defined then our swap_fee is gonna get halved.
        """
        additive_swap_fee = Decimal(0.00)
        max_swap_fee = Decimal(0.00)
        for route in routes:
            pool = [i for i in pool_filter if i.get_id() == route.pool_id][0]
            swap_fee = pool.get_swap_fee()
            additive_swap_fee += swap_fee
            max_swap_fee = max(max_swap_fee, swap_fee)
        average_swap_fee = additive_swap_fee/Decimal(2)
        max_swap_fee = max(average_swap_fee, max_swap_fee)
        return max_swap_fee, additive_swap_fee

    def multihop_routed_swap(self, pool_filter: list, incentivized_pools_list: list, token_in: Coin, routes: list):
        """
        multihop main function
        """
        token_out_min_amount = Decimal(1)
        discount_multihop = self._multihop_bool(
            routes, pool_filter, incentivized_pools_list, token_in)
        route_swap_fee, sum_of_swap_fee = self._get_osmo_routed_multihop_total_swap_fee(
            routes, pool_filter)
        for i, route in enumerate(routes):
            _out_min_amount = Decimal(1)
            if len(routes) - 1 == i:
                _out_min_amount = token_out_min_amount

            pool = [i for i in pool_filter if i.get_id() == route.pool_id][0]
            swap_fee = pool.get_swap_fee()
            if discount_multihop:
                swap_fee = route_swap_fee * (swap_fee/sum_of_swap_fee)
            token_out_amount = pool.swap_out_amount_given_in(
                token_in, route.token_out_denom, swap_fee)
            token_in: Coin = Coin(denom=route.token_out_denom,
                                  amount=token_out_amount.amount)
        return token_out_amount
