
import time
import super_global_variables as super_globals
from Bybit_Access import bybit_usdt_perp_client
from market_insertion import stop_loss_filling
from market_insertion.risk_manager import RiskManager
from general_helper_functions import Decistr
from logs_and_data import file_writer
from strategy_execution import helper_classes







def limit_order_status_check(order_id: str):
    '''
    checks the orders' status
     > float return value == (partial) fill of a closed order
      > 'order open' == order is open and 0 is filled
    '''
    if bybit_usdt_perp_client.is_order_open(order_id) == False:
        filled_size = bybit_usdt_perp_client.get_filled_size(order_id, False) # auf False wegen is_order_open()
        if filled_size > 0:
            return filled_size
        else:
            return 'placing limit order not possible'

    return 'order open'



















class OrderHandler:

    def __init__(self,
            cancel_entrys_at_this_timestamp: int,
            long_entry_price: float, long_stop_loss_price: float, long_take_profit_price: float,
            short_entry_price: float, short_stop_loss_price: float, short_take_profit_price: float) -> None:

        risk_manager = RiskManager()

        self.cancel_entrys_at_this_timestamp: int = cancel_entrys_at_this_timestamp

        self.long_entry_price: float = long_entry_price
        self.long_take_profit_price: float = long_take_profit_price
        self.long_stop_loss_price: float = long_stop_loss_price
        self.long_demanded_position_size, self.long_leverage = risk_manager.get_final_position_size('Buy', long_entry_price, long_stop_loss_price)

        self.short_entry_price: float = short_entry_price
        self.short_take_profit_price: float = short_take_profit_price
        self.short_stop_loss_price: float = short_stop_loss_price
        self.short_demanded_position_size, self.short_leverage = risk_manager.get_final_position_size('Sell', short_entry_price, short_stop_loss_price)

        self.entry_cancel_multiplier: float = 0.1 # ab welcher distanz entry order gecancelt wird bei einem partial fill, multipliziert mit risk value ticks


        # für wenn nur eine limit order direkt gesetzt wird
        self.final_entry_order_id: str = None
        self.final_take_profit_order_id: str = None

        self.final_entry_demanded_size: float = None
        self.final_leverage: float = None
        self.final_entry_filled_size: float = None


        self.final_entry_cancel_line: float = None

        self.final_take_profit_remaining_size: float = None
        self.final_take_profit_filled_size: float = 0

        self.final_stop_loss_side: str = None
        self.final_take_profit_side: str = None


        self.final_entry_side: str = None
        self.final_entry_time: float = None
        self.final_entry_price: float = None
        self.final_stop_loss_price: float = None
        self.final_risk_value_ticks: float = None
        self.final_take_profit_price: float = None


        self.entry_distance_split: float = 0.45




    def __check_where_in_distance(self):
        '''
        if sup & res exists, checks where last price is inside the distance
        '''
        long_price = Decistr(self.long_entry_price)
        short_price = Decistr(self.short_entry_price)
        entire_distance = short_price-long_price
        split_portion = entire_distance*Decistr(self.entry_distance_split)

        # price is in upper part: instantly short limit order
        # price is in lower part: instantly long limit order
        # price is in middle part: do nothing
        if bybit_usdt_perp_client.get_ask_price() >= short_price-split_portion:
            return 'in upper part'
        elif bybit_usdt_perp_client.get_bid_price() <= long_price+split_portion:
            return 'in lower part'
        else:
            return 'in middle part'










    def __save_position_trade_to_trade_history_file(self, exit_price: float) -> None:

        exit_time = time.time()

        duration_minutes = float(round((Decistr(exit_time)-Decistr(self.final_entry_time))/60, 4))
        
        if self.final_entry_side == 'Buy':
            performance = (Decistr(exit_price)-Decistr(self.final_entry_price)) /Decistr(self.final_risk_value_ticks)
        else:
            performance = (Decistr(self.final_entry_price)-Decistr(exit_price)) /Decistr(self.final_risk_value_ticks)
        performance = float(round(performance, 3))

        if performance > 0:
            result = 'win'
        elif performance == 0:
            result = 'breakeven'
        else:
            result = 'loss'

        if self.final_entry_side == 'Buy':
            file_side = 'long'
        else:
            file_side = 'short'


        file_writer.append_to_trade_history_file(
            file_side, self.final_entry_time, self.final_entry_price, self.final_stop_loss_price, self.final_risk_value_ticks, exit_time,
            exit_price, duration_minutes, performance, result, self.final_take_profit_price)












    def place_both_entrys(self):

        def __set_long_data():
            self.final_stop_loss_side = 'Sell'
            self.final_take_profit_side = 'Sell'
            self.final_entry_side = 'Buy'
            self.final_entry_price = self.long_entry_price
            self.final_stop_loss_price = self.long_stop_loss_price
            self.final_risk_value_ticks = float(abs(Decistr(self.long_entry_price)-Decistr(self.long_stop_loss_price)))
            self.final_take_profit_price = self.long_take_profit_price
            self.final_entry_demanded_size = self.long_demanded_position_size
            self.final_leverage = self.long_leverage
            self.final_entry_cancel_line = float(Decistr(self.final_entry_price)+(Decistr(self.final_risk_value_ticks)*Decistr(self.entry_cancel_multiplier)))

        def __set_short_data():
            self.final_stop_loss_side = 'Buy'
            self.final_take_profit_side = 'Buy'
            self.final_entry_side = 'Sell'
            self.final_entry_price = self.short_entry_price
            self.final_stop_loss_price = self.short_stop_loss_price
            self.final_risk_value_ticks = float(abs(Decistr(self.short_entry_price)-Decistr(self.short_stop_loss_price)))
            self.final_take_profit_price = self.short_take_profit_price
            self.final_entry_demanded_size = self.short_demanded_position_size
            self.final_leverage = self.short_leverage
            self.final_entry_cancel_line = float(Decistr(self.final_entry_price)-(Decistr(self.final_risk_value_ticks)*Decistr(self.entry_cancel_multiplier)))


        def __did_price_cross_entry_cancel_line() -> bool:
            if self.final_entry_side == 'Buy':
                if bybit_usdt_perp_client.get_ask_price() >= self.final_entry_cancel_line:
                    return True
                else:
                    return False
            
            else:
                if bybit_usdt_perp_client.get_bid_price() <= self.final_entry_cancel_line:
                    return True
                else:
                    return False



        def __cancel_limit_entry_order():

            while super_globals.running:
                bybit_usdt_perp_client.cancel_order(self.final_entry_order_id)
                if bybit_usdt_perp_client.is_order_open(self.final_entry_order_id) == False:
                    break

            self.final_entry_filled_size = bybit_usdt_perp_client.get_filled_size(self.final_entry_order_id)

            if self.final_entry_filled_size == self.final_entry_demanded_size:
                return 'limit entry order filled completely'

            elif self.final_entry_filled_size > 0:
                self.final_entry_demanded_size = float(Decistr(self.final_entry_demanded_size)-Decistr(self.final_entry_filled_size))
                return 'limit entry order filled partially'

            else:
                file_writer.append_to_log_position_manager('limit entry order canceled')
                self.final_entry_side = None
                return 'limit entry order canceled'


        def __check_time():
            if int(time.time()) >= self.cancel_entrys_at_this_timestamp:
                if self.final_entry_side != None:
                    cancel = __cancel_limit_entry_order()
                    if cancel != 'limit entry order canceled':
                        return cancel
                return 'time is over'


        def __check_fill_entry_order():
            self.final_entry_filled_size = bybit_usdt_perp_client.get_filled_size(self.final_entry_order_id)

            if self.final_entry_filled_size == self.final_entry_demanded_size:
                return 'limit entry order filled completely'

            elif self.final_entry_filled_size > 0:
                if __did_price_cross_entry_cancel_line() == True:
                    return __cancel_limit_entry_order()

            distance_state = self.__check_where_in_distance()

            if distance_state == 'in middle part':
                return __cancel_limit_entry_order()
            
            # für wenn Preis stark springen sollte
            if self.final_entry_side == 'Buy' and distance_state == 'in upper part':
                return __cancel_limit_entry_order()

            elif self.final_entry_side == 'Sell' and distance_state == 'in lower part':
                return __cancel_limit_entry_order()







        close = helper_classes.candle_history.get_candle(0)[1]
        if close < self.long_entry_price or close > self.short_entry_price:
            return 'price no good'


        while super_globals.running:
            distance_state = self.__check_where_in_distance()
            if distance_state != 'in middle part':

                if distance_state == 'in upper part':
                    __set_short_data()
                else:
                    __set_long_data()

                bybit_usdt_perp_client.set_leverage(self.final_leverage)

                self.final_entry_order_id = bybit_usdt_perp_client.place_limit_order(self.final_entry_side, self.final_entry_price, self.final_entry_demanded_size)
                file_writer.append_to_log_position_manager(f'{self.final_entry_side} limit entry order placed at {self.final_entry_price} with size {self.final_entry_demanded_size}')

                while super_globals.running:
                    filling_state = __check_fill_entry_order()
                    if filling_state != None:
                        if filling_state != 'limit entry order canceled':
                            file_writer.append_to_log_position_manager(filling_state)
                            file_writer.append_to_log_position_manager(f'completely filled size: {self.final_entry_filled_size}')
                            file_writer.append_to_log_position_manager(f'stop loss is at {self.final_stop_loss_price}')
                            return filling_state
                        else: # kommt hier nur hin wenn gecancelt hat wegen middle part
                            break
                    else:
                        ct = __check_time()
                        if ct != None:
                            return ct
                        else:
                            time.sleep(0.25)

            else:
                ct = __check_time()
                if ct != None:
                    return ct
                else:
                    time.sleep(0.25)








    def place_stop_loss_and_take_profit(self):

        def __place_take_profit_order():
            '''
            nur für take profit (die limit order)
            '''
            self.final_take_profit_order_id = bybit_usdt_perp_client.place_limit_order(self.final_take_profit_side, self.final_take_profit_price, self.final_take_profit_remaining_size)

            status_check = limit_order_status_check(self.final_take_profit_order_id)

            if status_check == 'placing limit order not possible':
                self.final_take_profit_remaining_size = float(Decistr(self.final_take_profit_remaining_size)-Decistr(self.final_take_profit_filled_size))
                bybit_usdt_perp_client.place_market_order(self.final_take_profit_side, self.final_take_profit_remaining_size)
                file_writer.append_to_log_position_manager(f'placing take profit market order with size {self.final_take_profit_remaining_size}')
                return 'take profit market order exit'

            else:
                file_writer.append_to_log_position_manager(f'{self.final_take_profit_side} take profit order placed at {self.final_take_profit_price} with size {self.final_take_profit_remaining_size}')
                if status_check == 'order open':
                    return 'take profit order placed'
                
                elif status_check == self.final_take_profit_remaining_size:
                    self.final_take_profit_filled_size = status_check
                    return 'take profit order filled completely'
                
                else:
                    self.final_take_profit_filled_size = status_check
                    self.final_take_profit_remaining_size = float(Decistr(self.final_take_profit_remaining_size)-Decistr(self.final_take_profit_filled_size))
                    return 'take profit order filled partially'


        def __stop_loss_hit() -> bool:
            if self.final_stop_loss_side == 'Buy':
                if bybit_usdt_perp_client.get_ask_price() >= self.final_stop_loss_price:
                    return True
                else:
                    return False

            else:
                if bybit_usdt_perp_client.get_bid_price() <= self.final_stop_loss_price:
                    return True
                else:
                    return False


        def __check_stop_loss_hit_and_take_profit_fill(counter):
            if counter == 250:
                self.final_take_profit_filled_size = bybit_usdt_perp_client.get_filled_size(self.final_take_profit_order_id)

            # ganz wichtig in dieser Reihenfolge zu überprüfen
            if self.final_take_profit_filled_size == self.final_take_profit_remaining_size:
                return 'take profit order filled completely'

            elif __stop_loss_hit() == True:

                while super_globals.running:
                    bybit_usdt_perp_client.cancel_order(self.final_take_profit_order_id)
                    if bybit_usdt_perp_client.is_order_open(self.final_take_profit_order_id) == False:
                        break
                # kein check auf order size des take profit weil ist stop loss hit, gehe davon aus dass risk value ticks groß sind

                file_writer.append_to_log_position_manager(f'{self.final_take_profit_side} take profit order at {self.final_take_profit_price} with size {self.final_take_profit_remaining_size} canceled')

                sl_filling = stop_loss_filling.start_stop_loss_filling(self.final_stop_loss_side, self.final_stop_loss_price, self.final_entry_filled_size, self.final_risk_value_ticks)
                # kann None zurückgeben wenn super_globals.running False ist, aber dann hört sowieso alles auf

                if sl_filling == 'abort stop loss filling':
                    tp_order = __place_take_profit_order()
                    if tp_order == 'take profit market order exit' or tp_order == 'take profit order filled completely':
                        return tp_order
                    else:
                        return 'take profit order placed'
                else:
                    return sl_filling

            else:
                return 'take profit order placed'



        self.final_take_profit_remaining_size = self.final_entry_filled_size

        filling_state = __place_take_profit_order()
        counter = 0

        while super_globals.running:
            if filling_state != 'take profit order placed':
                file_writer.append_to_log_position_manager(filling_state)
                
                if filling_state == 'take profit order filled completely' or filling_state == 'take profit market order exit':
                    self.__save_position_trade_to_trade_history_file(self.final_take_profit_price)
                    file_writer.append_to_log_position_manager(f'take profit order filled size: {self.final_take_profit_filled_size}')
                
                elif filling_state == 'limit stop loss order filled completely' or filling_state == 'stop loss market order exit':
                    self.__save_position_trade_to_trade_history_file(self.final_stop_loss_price)
                
                # kein else!
                return filling_state
            # time.sleep(0.125)
            time.sleep(0.0005) # 0.5ms
            counter += 1 # mit counter macht die request seltener bzw prüft stop loss hit öfter
            filling_state = __check_stop_loss_hit_and_take_profit_fill(counter)
            if counter == 250:
                counter = 0


















