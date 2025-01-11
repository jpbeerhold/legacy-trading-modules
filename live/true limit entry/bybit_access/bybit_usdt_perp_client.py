
import time, socket, pickle
from typing import Dict, List

from settings import general_specifications
import super_global_variables as super_globals
from logs_and_data import file_writer
from messenger import telegram_bot
from strategy_execution import helper_classes
import general_helper_functions as ghf
from general_helper_functions import Decistr
from threading import Thread

from pybit import unified_trading

symbol = general_specifications.symbol
time_frame = general_specifications.time_frame
tick_value = general_specifications.tick_value
coin = general_specifications.coin
strategy_name = general_specifications.Subaccount_Name
category = general_specifications.category




'''
latenzverhalten 20. Juli 2023
mehr bandwidth aws instanz sorgt für weniger latenz

order setzen dauert lange zB 100ms
cancel, amend, info ganz schnell zB 10ms

orderLinkId Verwendung denn wenn exception kam um zu checken ob order auf ist
'''




# rest api v2 behalten damit nicht alles ändern muss

from Bybit_Access._http_manager import _FuturesHTTPManager
from concurrent.futures import ThreadPoolExecutor



class HTTP(_FuturesHTTPManager):
    def query_kline(self, **kwargs):
        """
        - first item has smallest timestamp

        Get kline.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-querykline.
        :returns: Request results as dictionary.
        """

        # Replace query param "from_time" since "from" keyword is reserved.
        # Temporary workaround until Bybit updates official request params
        if "from_time" in kwargs:
            kwargs["from"] = kwargs.pop("from_time")

        suffix = "/public/linear/kline"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def public_trading_records(self, **kwargs):
        """
        Get recent trades. You can find a complete history of trades on Bybit
        at https://public.bybit.com/.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-publictradingrecords.
        :returns: Request results as dictionary.
        """

        # Replace query param "from_id" since "from" keyword is reserved.
        # Temporary workaround until Bybit updates official request params
        if "from_id" in kwargs:
            kwargs["from"] = kwargs.pop("from_id")

        suffix = "/public/linear/recent-trading-records"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def query_mark_price_kline(self, **kwargs):
        """
        Query mark price kline (like query_kline but for mark price).

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-markpricekline.
        :returns: Request results as dictionary.
        """

        # Replace query param "from_time" since "from" keyword is reserved.
        # Temporary workaround until Bybit updates official request params
        if "from_time" in kwargs:
            kwargs["from"] = kwargs.pop("from_time")

        suffix = "/public/linear/mark-price-kline"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def query_index_price_kline(self, **kwargs):
        """
        Query index price kline (like query_kline but for index price).

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-queryindexpricekline.
        :returns: Request results as dictionary.
        """

        # Replace query param "from_time" since "from" keyword is reserved.
        # Temporary workaround until Bybit updates official request params
        if "from_time" in kwargs:
            kwargs["from"] = kwargs.pop("from_time")

        suffix = "/public/linear/index-price-kline"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def query_premium_index_kline(self, **kwargs):
        """
        Query premium index kline (like query_kline but for the premium index
        discount).

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-querypremiumindexkline.
        :returns: Request results as dictionary.
        """

        # Replace query param "from_time" since "from" keyword is reserved.
        # Temporary workaround until Bybit updates official request params
        if "from_time" in kwargs:
            kwargs["from"] = kwargs.pop("from_time")

        suffix = "/public/linear/premium-index-kline"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def place_active_order(self, **kwargs):
        """
        Places an active order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-activeorders.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-activeorders.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/create"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def get_active_order(self, **kwargs):
        """
        Gets an active order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-getactive.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-getactive.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/list"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def cancel_active_order(self, **kwargs):
        """
        Cancels an active order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-cancelactive.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-cancelactive.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/cancel"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def cancel_all_active_orders(self, **kwargs):
        """
        Cancel all active orders that are unfilled or partially filled. Fully
        filled orders cannot be cancelled.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-cancelallactive.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/cancel-all"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def replace_active_order(self, **kwargs):
        """
        Replace order can modify/amend your active orders.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-replaceactive.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/replace"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def query_active_order(self, **kwargs):
        """
        - Wenn order_id gegeben wird ist 'result' ein Dict
        - Wenn nicht gegeben wird ist 'result' eine Liste mit max 500 nur offene orders als Dicts
        - Wenn order_id nicht existiert dann Exception
        - Wenn order_id gegeben wird aber order nicht offen ist wird trotzdem Dict zurückgegeben

        Query real-time active order information.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-queryactive.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/order/search"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def place_conditional_order(self, **kwargs):
        """
        Places a conditional order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-placecond.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-placecond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/create"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def get_conditional_order(self, **kwargs):
        """
        Gets a conditional order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-getcond.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-getcond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/list"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def cancel_conditional_order(self, **kwargs):
        """
        Cancels a conditional order. For more information, see
        https://bybit-exchange.github.io/docs/linear/#t-cancelcond.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-cancelcond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/cancel"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def cancel_all_conditional_orders(self, **kwargs):
        """
        Cancel all conditional orders that are unfilled or partially filled.
        Fully filled orders cannot be cancelled.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-cancelallcond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/cancel-all"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def replace_conditional_order(self, **kwargs):
        """
        Replace conditional order can modify/amend your conditional orders.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-replacecond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/replace"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def query_conditional_order(self, **kwargs):
        """
        Query real-time conditional order information.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-querycond.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/stop-order/search"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def my_position(self, **kwargs):
        """
        Get my position list.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-myposition.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/list"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def set_auto_add_margin(self, **kwargs):
        """
        For linear markets only. Set auto add margin, or Auto-Margin
        Replenishment.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-setautoaddmargin.
        :returns: Request results as dictionary.
        """

        return self._submit_request(
            method="POST",
            path=self.endpoint + "/private/linear/position/set-auto-add-margin",
            query=kwargs,
            auth=True
        )

    def set_leverage(self, **kwargs):
        """
        Change user leverage.
        If you want to switch between cross margin and isolated margin, please
        see cross_isolated_margin_switch.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-setleverage.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/set-leverage"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def cross_isolated_margin_switch(self, **kwargs):
        """
        Switch Cross/Isolated; must be leverage value when switching from Cross
        to Isolated.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-marginswitch.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/switch-isolated"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def position_mode_switch(self, **kwargs):
        """
        If you are in One-Way Mode, you can only open one position on Buy or
        Sell side. If you are in Hedge Mode, you can open both Buy and Sell
        side positions simultaneously.

        Supports switching between One-Way Mode and Hedge Mode at the coin
        level.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-switchpositionmode.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/switch-mode"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def full_partial_position_tp_sl_switch(self, **kwargs):
        """
        Switch mode between Full or Partial

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-switchmode.
        :returns: Request results as dictionary.
        """
        suffix = "/private/linear/tpsl/switch-mode"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def set_trading_stop(self, **kwargs):
        """
        Set take profit, stop loss, and trailing stop for your open position.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-tradingstop.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/trading-stop"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def add_reduce_margin(self, **kwargs):
        """
        For linear markets only. Add margin.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-addmargin.
        :returns: Request results as dictionary.
        """

        return self._submit_request(
            method="POST",
            path=self.endpoint + "/private/linear/position/add-margin",
            query=kwargs,
            auth=True
        )

    def user_trade_records(self, **kwargs):
        """
        Get user's trading records. The results are ordered in ascending order
        (the first item is the oldest).

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-usertraderecords.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/trade/execution/list"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def extended_user_trade_records(self, **kwargs):
        """
        Get user's trading records. The results are ordered in ascending order
        (the first item is the oldest). Returns records up to 2 years old.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-userhistorytraderecords.
        :returns: Request results as dictionary.
        """

        return self._submit_request(
            method="GET",
            path=self.endpoint + "/private/linear/trade/execution/history-list",
            query=kwargs,
            auth=True
        )

    def closed_profit_and_loss(self, **kwargs):
        """
        Get user's closed profit and loss records. The results are ordered in
        descending order (the first item is the latest).

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-closedprofitandloss.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/trade/closed-pnl/list"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def get_risk_limit(self, **kwargs):
        """
        Get risk limit.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-getrisklimit.
        :returns: Request results as dictionary.
        """

        suffix = "/public/linear/risk-limit"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
        )

    def set_risk_limit(self, **kwargs):
        """
        Set risk limit.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-setrisklimit.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/position/set-risk"

        return self._submit_request(
            method="POST",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def get_the_last_funding_rate(self, **kwargs):
        """
        The funding rate is generated every 8 hours at 00:00 UTC, 08:00 UTC and
        16:00 UTC. For example, if a request is sent at 12:00 UTC, the funding
        rate generated earlier that day at 08:00 UTC will be sent.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-fundingrate.
        :returns: Request results as dictionary.
        """

        suffix = "/public/linear/funding/prev-funding-rate"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs
        )

    def my_last_funding_fee(self, **kwargs):
        """
        Funding settlement occurs every 8 hours at 00:00 UTC, 08:00 UTC and
        16:00 UTC. The current interval's fund fee settlement is based on the
        previous interval's fund rate. For example, at 16:00, the settlement is
        based on the fund rate generated at 8:00. The fund rate generated at
        16:00 will be used at 0:00 the next day.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-mylastfundingfee.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/funding/prev-funding"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    def predicted_funding_rate(self, **kwargs):
        """
        Get predicted funding rate and my funding fee.

        :param kwargs: See
            https://bybit-exchange.github.io/docs/linear/#t-predictedfunding.
        :returns: Request results as dictionary.
        """

        suffix = "/private/linear/funding/predicted-funding"

        return self._submit_request(
            method="GET",
            path=self.endpoint + suffix,
            query=kwargs,
            auth=True
        )

    '''
    Additional Methods
    These methods use two or more requests to perform a specific
    function and are exclusive to pybit.
    '''

    def close_position(self, symbol):
        """
        Closes your open position. Makes two requests (position, order).

        Parameters
        ------------------------
        symbol : str
            Required parameter. The symbol of the market as a string,
            e.g. "BTCUSD".

        """

        # First we fetch the user's position.
        try:
            r = self.my_position(symbol=symbol)

        # If there is no returned position, we want to handle that.
        except KeyError:
            return self.logger.error("No position detected.")

        # Next we generate a list of market orders
        orders = [
            {
                "symbol": symbol,
                "order_type": "Market",
                "side": "Buy" if p["side"] == "Sell" else "Sell",
                "qty": p["size"],
                "time_in_force": "ImmediateOrCancel",
                "reduce_only": True,
                "close_on_trigger": True,
                "position_idx": 0
            } for p in (r if isinstance(r, list) else [r]) if p["size"] > 0
        ]

        if len(orders) == 0:
            return self.logger.error("No position detected.")

        # Submit a market order against each open position for the same qty.
        return self.place_active_order_bulk(orders)

    def place_active_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Places multiple active orders in bulk using multithreading. For more
        information on place_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-activeorders.

        :param list orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.place_active_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]

    def cancel_active_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Cancels multiple active orders in bulk using multithreading. For more
        information on cancel_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-activeorders.

        :param list orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.cancel_active_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]

    def replace_active_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Replaces multiple active orders in bulk using multithreading. For more
        information on replace_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-replaceactive.

        :param list orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.replace_active_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]

    def place_conditional_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Places multiple conditional orders in bulk using multithreading. For
        more information on place_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-placecond.

        :param orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.place_conditional_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]

    def cancel_conditional_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Cancels multiple conditional orders in bulk using multithreading. For
        more information on cancel_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-cancelcond.

        :param list orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.cancel_conditional_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]

    def replace_conditional_order_bulk(self, orders: list, max_in_parallel=10):
        """
        Replaces multiple conditional orders in bulk using multithreading. For
        more information on replace_active_order, see
        https://bybit-exchange.github.io/docs/inverse/#t-replacecond.

        :param list orders: A list of orders and their parameters.
        :param max_in_parallel: The number of requests to be sent in parallel.
            Note that you are limited to 50 requests per second.
        :returns: Future request result dictionaries as a list.
        """

        with ThreadPoolExecutor(max_workers=max_in_parallel) as executor:
            executions = [
                executor.submit(
                    self.replace_conditional_order,
                    **order
                ) for order in orders
            ]
        executor.shutdown()
        return [execution.result() for execution in executions]



v2_rest_client = HTTP(
    api_key=general_specifications.API_Key,
    api_secret=general_specifications.API_Secret,
    return_only_result=True,
    max_retries=99999,
    request_timeout=0.25,
    recv_window=250,
    force_retry=True,
    retry_delay=0,
    retry_codes={
        10002, 10006, 30034, 30035, 130035, 130150, # default from pybit
        10016, # service error, occured while live
        -1, # order request expired due to receive window, occured while live
        502, # bad gateway, occured while live
        10004, # wrong sign, occured while live
        30034, 30035, 130035, 130150
    },


    # ignore_codes={
    #     11039, 20010, 20011, 30009, 30032, 30037, 30041,
    #     130037, 130035
    # }

    ignore_codes={ # wenn diese error code kommt dann wird None zurückgegeben
        20001, # order already closed or order doesnt exist
        34036, # leverage not changed
        30032 # cannot cancel order
    }
)














# rest api v5 nutzen für orders für mehr rate limit


class BybitWrapper:

    def __init__(self):
        self.instance = unified_trading.HTTP(
            api_key=general_specifications.API_Key,
            api_secret=general_specifications.API_Secret,
            domain="bytick",
            recv_window=500,
            timeout=1,
            log_requests=True,
            record_request_time=False,
            force_retry=True,
            max_retries=999,
            retry_delay=0.25,
            ignore_codes={ # wenn diese error code kommt dann wird None zurückgegeben
                110001, # order doesnt exist
                110043, # leverage not changed
                170191, # cannot cancel order
                110010, # The order has been cancelled
                110030 # duplicate orderId
            },
            retry_codes={
                10002, 10006, 30034, 30035, 130035, 130150, # default
                10016, # service error, occured while live
                -1, # order request expired due to receive window, occured while live
                502 # bad gateway, occured while live
            }
        )


    def cancel_order(self, order_link_id: str):
        cancel = self.instance.cancel_order(
            category=category,
            symbol=symbol,
            orderLinkId=order_link_id
        )
        if cancel != None:
            return cancel['result']
        else:
            return


    # def cancel_all_orders(
    #     self,
    #     category: str = "spot",
    #     symbol: str = "ETHUSDT",
    # ) -> dict:
    #     """
    #     Cancel orders by category and symbol
    #     """
    #     return self.instance.cancel_all_orders(
    #         category=category, symbol=symbol
    #     )['result']


    # def get_realtime_orders(
    #     self,
    #     category: str,
    #     symbol: str = None,
    # ) -> dict:
    #     """
    #     Get realtime orders
    #     """
    #     return self.instance.get_open_orders(
    #         category=category,
    #         symbol=symbol,
    #     )


    def get_order_info(self, order_link_id: str):
        return self.instance.get_open_orders(
            category=category,
            symbol=symbol,
            orderLinkId=order_link_id
        )['result']['list'][0]


    def get_order_history(self, **kwargs) -> dict:
        return self.instance.get_order_history(**kwargs)["result"]["list"]


    def amend_order(self, order_link_id: str, new_price: str = None, new_qty: str = None):
        param = {
            'category': category,
            'symbol': symbol,
            'orderLinkId': order_link_id
        }
        if new_price != None:
            param['price'] = new_price
        # kein elif
        if new_qty != None:
            param['qty'] = new_qty 
        return self.instance.amend_order(**param)['result']
            

    def place_limit_order(self, order_link_id: str, side: str, price: str, qty: str):
        return self.instance.place_order(
            category=category,
            symbol=symbol,
            side=side,
            orderType="Limit",
            price=price,
            qty=qty,
            timeInForce='PostOnly',
            reduceOnly=False,
            closeOnTrigger=False,
            positionIdx=0,
            orderLinkId=order_link_id
        )['result']


    def place_market_order(self, order_link_id, side: str, qty: str):
        return self.instance.place_order(
            category=category,
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=qty,
            reduce_only=True,
            close_on_trigger=True,
            position_idx=0,
            order_link_id=order_link_id
        )['result']


    def set_leverage(self, leverage: float):
        leverage = str(leverage)
        self.instance.set_leverage(
            category=category,
            symbol=symbol,
            buyLeverage=leverage,
            sellLeverage=leverage
        )




v5_rest_client = BybitWrapper()

















'''
### GET ###
'''



def is_order_open(order_link_id: str) -> bool:
    __query_order_into_collection(order_link_id)
    for item in all_orders_and_executions_collection:
        if item['order_link_id'] == order_link_id:
            status = item['order_status']
            if status in ['Created', 'PendingCancel']:
                return is_order_open(order_link_id)
            # bei 'PartiallyFilled' True zurückgeben damit weiter canceled
            elif status in ['New', 'PartiallyFilled']:
                return True
            else: # 'Rejected', 'Cancelled', 'Filled'
                return False


def get_filled_size(order_link_id: str, do_request: bool = True) -> float:
    if do_request == True:
        __query_order_into_collection(order_link_id)
    for item in all_orders_and_executions_collection:
        if item['order_link_id'] == order_link_id:
            return item['filled_size']


def get_avg_filled_price(order_link_id: str) -> float:
    __query_order_into_collection(order_link_id)
    for item in all_orders_and_executions_collection:
        if item['order_link_id'] == order_link_id:
            return item['filled_price']







# def get_past_single_candle(number_back: int):
#     '''
#     :number_back:
#         0 aktuelle candle
#         1 erste candle zurückliegend
#         2 zweite candle zurückliegend
#         etc

#     output format in Dict:
#         final_candle = {
#             'timestamp': int,
#             'open': float,
#             'high': float,
#             'low': float,
#             'close': float,
#             'volume': float,
#             'turnover': float
#         }
#     '''
#     assert number_back >= 0, number_back
#     t = int(time.time())
#     while t % (time_frame*60) != 0:
#         t -= 1
#     t -= time_frame*60*number_back
#     candle = v2_rest_client.query_kline(symbol=symbol, interval=str(time_frame), from_time=t, limit=1)[0]
#     return {
#         'timestamp': int(candle['open_time']),
#         'open': float(candle['open']),
#         'high': float(candle['high']),
#         'low': float(candle['low']),
#         'close': float(candle['close']),
#         'volume': float(candle['volume']),
#         'turnover': float(candle['turnover'])
#     }







'''
### POST ###
'''

# use_websocket: bool = False
# dafür sorgen dass bei order placement die order auf jeden fall in collection ist
# ohne dass websocket gleichzeitig auf dict zugreifen kann, damit nichts durcheinander kommt
# websocket ist für orders ein kleines hilfmittel, meißte basiert auf REST



def place_limit_order(side: str, price: float, size: float) -> str:
    '''
    returns order link id
    '''
    order_link_id = ghf.randStr()
    order = v5_rest_client.place_limit_order(order_link_id, side, price, size)
    if order != None:
        return order_link_id
    else:
        # wenn None dann kam exception, prüfen ob order ankam/exisitert
        order = v5_rest_client.get_order_info(order_link_id)
        # wenn auch hier None kam existiert order nicht
        if order != None:
            __insert_raw_order_data_into_collection(order)
            # use_websocket = True
            return order_link_id
        else:
            return place_limit_order(side, price, size)



def place_market_order(side: str, size: float) -> str:
    '''
    returns order link id
    '''
    order_link_id = ghf.randStr()
    order = v5_rest_client.place_market_order(order_link_id, side, size)
    if order != None:
        return order_link_id
    else:
        # wenn None dann kam exception, prüfen ob order ankam/exisitert
        order = v5_rest_client.get_order_info(order_link_id)
        # wenn auch hier None kam existiert order nicht
        if order != None:
            __insert_raw_order_data_into_collection(order)
            # use_websocket = True
            return order_link_id
        else:
            return place_market_order(side, size)



def cancel_order(order_link_id: str) -> Dict:
    '''
    returns order_link_id
    '''
    v5_rest_client.cancel_order(order_link_id)
    return order_link_id



def set_leverage(leverage: float):
    leverage = float(leverage)
    v5_rest_client.set_leverage(leverage)



def get_money_balance():
    return float(v2_rest_client.get_wallet_balance(coin=coin)[coin]['available_balance'])















all_orders_and_executions_collection: List[Dict] = []


def __insert_raw_order_data_into_collection(raw_order_data: Dict):
    global all_orders_and_executions_collection

    # in mein Format ändern
    new_order_data = {}
    new_order_data['order_link_id'] = raw_order_data['orderLinkId']
    new_order_data['filled_price'] = float(raw_order_data['avgPrice'])
    new_order_data['filled_size'] = float(raw_order_data['cumExecQty'])
    new_order_data['order_status'] = raw_order_data['orderStatus']

    # suchen & finden
    for item in all_orders_and_executions_collection:
        if item['order_link_id'] == new_order_data['order_link_id']:
            item['filled_price'] = new_order_data['filled_price']
            item['filled_size'] = new_order_data['filled_size']
            item['order_status'] = new_order_data['order_status']
            return

    # wenn nicht gefunden dann anhängen
    all_orders_and_executions_collection.append(new_order_data)



def __query_order_into_collection(order_link_id: str):
    order = v5_rest_client.get_order_info(order_link_id)
    __insert_raw_order_data_into_collection(order)













class Client:
    buffer_size = 1024
    bytes_encoding = 'utf-8'

    def __init__(self, socket_address: str) -> None:
        self.socket_address = socket_address
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(socket_address)
        
        name_request = self.s.recv(self.buffer_size).decode(self.bytes_encoding)
        if name_request == 'who are you':
            try:
                self.s.sendall(bytes(strategy_name, self.bytes_encoding))
            except BrokenPipeError:
                raise
        else:
            raise
        
        client_thread = Thread(target=self._listen_to_server)
        client_thread.daemon = True
        client_thread.start()

    def _listen_to_server(self):
        while super_globals.running:
            data = self.s.recv(self.buffer_size)
            python_dict = pickle.loads(data)
            self.s.sendall(bytes('data received', self.bytes_encoding))
            self._unpack_data(python_dict['topic'], python_dict['data'])


    def _unpack_data(self, topic: str, data: Dict):
        if topic == 'orderbook':
            helper_classes.latest_ticker_data.set_bid_ask(data['bid_price'], data['ask_price'])
        elif topic == 'kline':
            if super_globals.is_initialization_done:
                helper_classes.candle_history.add_candle(int(data['timestamp']), Decistr(data['close']))
        else:
            raise



path_to_server = f'/home/PublicWebsocketDatabase/'

client = Client(path_to_server+'kline_socket')

client = Client(path_to_server+'orderbook_socket')
















def get_bid_price():
    return helper_classes.latest_ticker_data.get_bid()


def get_ask_price():
    return helper_classes.latest_ticker_data.get_ask()














def terminate_bot():

    super_globals.running = False
    file_writer.position_manager_queue.put(False)
    file_writer.stop_loss_fill_queue.put(False)
    file_writer.append_to_log_bybit_client('Starting termination')
    telegram_bot.send_telegram_message('Starting termination')

    while True:
        # cancel order gibt nur die order_link_id zurück
        v2_rest_client.cancel_active_order_bulk(orders=v2_rest_client.query_active_order(symbol=symbol))

        my_pos = v2_rest_client.close_position(symbol=symbol)
        if my_pos == None: # gibt None zurück wenn Markt noch nie gehandelt wurde oder keine position existiert
            break
        else:
            time.sleep(1) # wait for market order to fill



