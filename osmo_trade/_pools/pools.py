from decimal import Decimal
import osmosis_protobuf.osmosis.gamm.v1beta1.query_pb2 as query_pb
import osmosis_protobuf.osmosis.gamm.v1beta1.query_pb2_grpc as query_pb_grpc

class HostPort:
    def __init__(self, host, port, ssl= False):
        self.host: str = host
        self.port: int = port
        self.ssl: bool = ssl

class Coin:
    def __init__(self, amount, denom, denom_symbol = None):
        self.amount: Decimal = Decimal(amount)
        self.denom: str = denom
        if denom_symbol == None:
            self.symbol: str = None
        else:
            self.symbol: str = denom_symbol[self.denom]

class PoolAssets:
    def __init__(self, token, weight):
        self.token: Coin = Coin(denom= token['denom'], amount= token['amount'])
        self.weight: Decimal = Decimal(weight)


class PoolParams:
    def __init__(self, swap_fee, exit_fee):
        self.swap_fee: Decimal = Decimal(swap_fee)/pow(10, 18)
        self.exit_fee: Decimal = Decimal(exit_fee)


class SwapAmountInRoute:
    def __init__(self, pool_id, denom):
        self.pool_id: int = pool_id
        self.token_out_denom: str = denom


class SwapAmountOutRoute:
    def __init__(self, pool_id, denom):
        self.pool_id: int = pool_id
        self.token_in_denom: str = denom


class BidAskPrice:
    def __init__(self, bid_price, ask_price):
        self.bid: Decimal = Decimal(bid_price)
        self.ask: Decimal = Decimal(ask_price)

class BalancerPool():
    def __init__(self, address, id, pool_params, pool_assets, total_weight, block_height):
        self.address: str = address
        self.id: int = int(id)
        self.pool_params: PoolParams = PoolParams(
            pool_params['swapFee'], pool_params['exitFee'])
        self.pool_assets: list = [PoolAssets(
            i['token'], i['weight']) for i in pool_assets]
        self.total_weight: total_weight = Decimal(total_weight)
        self.block_height: int = block_height


    def get_id(self):
        return self.id

    def get_swap_fee(self):
        return self.pool_params.swap_fee

    def get_exit_fee(self):
        return self.pool_params.exit_fee

    def is_incentivized(self, incentivized_pools_list):
        if self.id in incentivized_pools_list:
            return True
        else:
            return False

    def get_pool_assets(self):
        return self.pool_assets

    def new_coin(self, denom: str, amount: Decimal):
        coin = Coin(denom= denom, amount= amount)
        return coin

    def spot_price(self, base_asset: str = None, quote_asset: str = None, reverse = False):
        """
        Ex: BTC-USDT: BTC is the base asset and USDT is the quote asset.
        So, ATOM-OSMO pool spot_price would give you price of 1 OSMO.
        
        Note: when reverse flag is True, then the spot_price would in terms of OSMO. Ex, 1 ATOM = 13 OSMO.
        """
        if base_asset is None:
            base_asset = self.pool_assets[0].token.denom
        if quote_asset is None:
            quote_asset = self.pool_assets[1].token.denom
        if reverse:
            base_asset, quote_asset = quote_asset, base_asset
        for asset in self.pool_assets:
            if base_asset == asset.token.denom:
                base = asset
            elif quote_asset == asset.token.denom:
                quote = asset
        if (base.weight == 0) or (quote.weight == 0):
            print("Pool is not setup correctly")

        inv_weight_ratio = quote.weight/base.weight
        supply_ratio = base.token.amount/quote.token.amount
        spot_price = supply_ratio * inv_weight_ratio
        return spot_price

    def solve_constant_invariant_function(self, token_balance_fixed_before, token_balance_fixed_after, token_weight_fixed, token_balance_unknown_before, token_weight_unknown):
        weight_ratio = token_weight_fixed/token_weight_unknown
        y = token_balance_fixed_before/token_balance_fixed_after
        y_to_weight_ratio = y ** weight_ratio
        parenthetical = (1 - y_to_weight_ratio)
        amount_y = token_balance_unknown_before * parenthetical
        return amount_y

    def swap_out_amount_given_in(self, token_in: Coin, token_out_denom: str, swap_fee: Decimal):
        pool_asset_in = None
        pool_asset_out = None
        for asset in self.pool_assets:
            if token_in.denom == asset.token.denom:
                pool_asset_in = asset
            elif token_out_denom == asset.token.denom:
                pool_asset_out = asset
            else:
                continue
        if (pool_asset_in is None):
            print("Asset {} not found in pool {}".format(
                token_in.denom, self.get_id()))
        elif pool_asset_out is None:
            print("Asset {} not found in pool {}".format(
                token_out_denom, self.get_id()))
        token_amount_in_after_fee = token_in.amount * (1 - swap_fee)
        pool_token_in_balance = pool_asset_in.token.amount
        pool_post_swap_in_balance = pool_token_in_balance + token_amount_in_after_fee
        token_amount_out = self.solve_constant_invariant_function(
            pool_token_in_balance, pool_post_swap_in_balance, pool_asset_in.weight, pool_asset_out.token.amount, pool_asset_out.weight)
        token_amount_out = self.new_coin(token_out_denom, token_amount_out)
        return token_amount_out

    def swap_in_amount_given_out(self, token_out: Coin, token_in_denom: str, swap_fee: Decimal):
        pool_asset_in = None
        pool_asset_out = None
        for asset in self.pool_assets:
            if token_in_denom == asset.token.denom:
                pool_asset_in = asset
            elif token_out.denom == asset.token.denom:
                pool_asset_out = asset
            else:
                continue
        if pool_asset_in is None:
            print("Asset {} not found in pool {}".format(
                token_in_denom, self.get_id()))
        elif pool_asset_out is None:
            print("Asset {} not found in pool {}".format(
                token_out.denom, self.get_id()))
        pool_token_out_balance = pool_asset_out.token.amount
        pool_post_swap_out_balance = pool_token_out_balance - token_out.amount
        token_amount_in = self.solve_constant_invariant_function(
            pool_token_out_balance, pool_post_swap_out_balance, pool_asset_out.weight, pool_asset_in.token.amount, pool_asset_in.weight)
        token_amount_in_after_fee = abs(
            token_amount_in/(1 - swap_fee))
        token_amount_in = self.new_coin(
            token_in_denom, token_amount_in_after_fee)
        return token_amount_in


class StableswapPool:
    def __init__(self, address, id, pool_params, pool_liquidity, scaling_factors, block_height):
        self.address: str = address
        self.id: int = int(id)
        self.pool_params: PoolParams = PoolParams(
            pool_params['swapFee'], pool_params['exitFee'])
        self.pool_liquidity = [Coin(denom= i['denom'], amount= i['amount'])
                               for i in pool_liquidity]
        self.scaling_factors: list = [Decimal(i) for i in scaling_factors]
        self.block_height: int = block_height

