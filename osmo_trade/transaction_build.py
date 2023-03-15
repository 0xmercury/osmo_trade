import sys
from mospy import Transaction
from mospy.clients import GRPCClient
from decimal import Decimal
import osmosis_protobuf.osmosis.gamm.v1beta1.tx_pb2 as tx_osmosis
from osmosis_protobuf.osmosis.gamm.v1beta1.tx_pb2 import MsgSwapExactAmountIn, MsgSwapExactAmountOut
from osmo_trade._pools import SwapAmountInRoute, SwapAmountOutRoute, Coin


class TransactionBuild:
    def __init__(self, account, _host_port):
        self._account = account
        self._client = GRPCClient(
            host=_host_port.host, port=_host_port.port, ssl= _host_port.ssl, protobuf='osmosis')

    def _create_message_transaction_swap_exact_amount_in(self, routes: [SwapAmountInRoute], token_in: Coin, token_out_min_amount: Decimal) -> MsgSwapExactAmountIn:
        msg = MsgSwapExactAmountIn()
        msg.sender = self._account.address
        for route in routes:
            _route = tx_osmosis.SwapAmountInRoute()
            _route.pool_id = route.pool_id
            _route.token_out_denom = route.token_out_denom
            msg.routes.append(_route)
        msg.token_in.denom = token_in.denom
        msg.token_in.amount = str(token_in.amount)
        msg.token_out_min_amount = str(token_out_min_amount)
        return msg

    def _create_message_transaction_swap_exact_amount_out(self, routes: [SwapAmountOutRoute], token_out: Coin, token_in_max_amount: Decimal) -> MsgSwapExactAmountOut:
        msg = MsgSwapExactAmountOut()
        msg.sender = self._account.address
        for route in routes:
            _route = tx_osmosis.SwapAmountOutRoute()
            _route.pool_id = route.pool_id
            _route.token_in_denom = route.token_in_denom
            msg.routes.append(_route)
        msg.token_out.denom = token_out.denom
        msg.token_out.amount = str(token_out.amount)
        msg.token_in_max_amount = str(token_in_max_amount)
        return msg

    """
    let's say 10 atom -> 5 OSMO.
    5 OSMO -> 1 USDC
    ATOM->OSMO spot price = 0.5 
    OSMO->USDC spot price = 0.2
    ATOM->USDC spot price = 0.1
    """

    def calculate_price_impact_tolerance_for_exactin(self, token_in: Coin, pools: dict, routes: [SwapAmountInRoute], slippage: Decimal):
        spot_price = 1
        for route in routes:
            if route.token_out_denom == pools[route.pool_id].pool_assets[1].token.denom:
                # reverse = True because spot price is in terms of OSMO i.e. 1 ATOM  would give how much OSMO.
                spot_price *= pools[route.pool_id].spot_price(reverse=True)
            elif route.token_out_denom == pools[route.pool_id].pool_assets[0].token.denom:
                spot_price *= pools[route.pool_id].spot_price()
        return int(spot_price*token_in.amount*(1 - slippage))

    def broadcast_exact_in_transaction(self, routes: [SwapAmountInRoute], token_in: Coin, pools: dict, slippage: Decimal = None) -> str:
        if slippage is None:
            token_out_min_amount = int(1)
        else:
            token_out_min_amount = self.calculate_price_impact_tolerance_for_exactin(
                token_in=token_in, pools=pools, slippage=slippage, routes=routes)
        msg = self._create_message_transaction_swap_exact_amount_in(
            routes, token_in, token_out_min_amount)
        tx = Transaction(account=self._account, chain_id="osmosis-1",
                         gas=300000, protobuf="osmosis")
        tx.add_raw_msg(
            msg, type_url="/osmosis.gamm.v1beta1.MsgSwapExactAmountIn")
        tx.set_fee(amount=5000, denom="uosmo")
        self._client.load_account_data(self._account)
        tx_hash = self._client.broadcast_transaction(transaction=tx)
        return tx_hash

    def calculate_price_impact_tolerance_for_exactout(self, token_out: Coin, pools: dict, routes: [SwapAmountOutRoute], slippage: Decimal):
        spot_price = 1
        for route in reversed(routes):
            if route.token_in_denom == pools[route.pool_id].pool_assets[0].token.denom:
                spot_price *= pools[route.pool_id].spot_price(reverse=True)
            elif route.token_in_denom == pools[route.pool_id].pool_assets[1].token.denom:
                spot_price *= pools[route.pool_id].spot_price()
        return int(token_out.amount/(spot_price * (1 - slippage)))

    def broadcast_exact_out_transaction(self, routes: [SwapAmountOutRoute], token_out: Coin, pools: dict, slippage: Decimal = None) -> str:
        if slippage is None:
            token_in_max_amount = int(sys.maxsize * 2)
        else:
            token_in_max_amount = self.calculate_price_impact_tolerance_for_exactout(
                token_out=token_out, pools=pools, routes=routes, slippage=slippage)
        msg = self._create_message_transaction_swap_exact_amount_out(
            routes, token_out, token_in_max_amount)
        tx = Transaction(account=self._account, chain_id="osmosis-1",
                         gas=300000, protobuf="osmosis")
        tx.add_raw_msg(
            msg, type_url="/osmosis.gamm.v1beta1.MsgSwapExactAmountOut")
        tx.set_fee(amount=5000, denom="uosmo")
        self._client.load_account_data(self._account)
        tx_hash = self._client.broadcast_transaction(transaction=tx)
        return tx_hash
