

from general_helper_functions import Decistr
from settings import general_specifications
from logs_and_data import file_writer
from Bybit_Access import bybit_usdt_perp_client



risk_per_trade = general_specifications.risk_per_trade
number_decimals_calc_position_size = general_specifications.number_decimals_calc_position_size
maintenance_margin_rate_percent = Decistr(general_specifications.maintenance_margin_rate_percent)
max_possible_leverage = general_specifications.max_possible_leverage
min_distance_liq_sl = Decistr(general_specifications.min_distance_liq_sl)

taker_fee_percent = Decistr('0.06') # Bybit reserviert in dieser Höhe






class RiskManager:
    '''
    bybit schneidet order size nachkommastellen ab und rechnet mit diesen für order cost
    bybit rundet order cost nicht
    mit abgeschnittener position_size kann genau gleiche order cost wie bei bybit berechnet & order gesetzt werden
    '''



    def __init__(self) -> None:
        self.money_balance = Decistr(bybit_usdt_perp_client.get_money_balance())




    def get_final_position_size(self, entry_side, entry_price, stop_loss_price):

        entry_price = Decistr(entry_price)
        stop_loss_price = Decistr(stop_loss_price)


        if entry_side == 'Buy':
            liq_price = stop_loss_price-min_distance_liq_sl
            leverage = self.__get_leverage_by_liq_price(entry_side, entry_price, liq_price)
        else:
            liq_price = stop_loss_price+min_distance_liq_sl
            leverage = self.__get_leverage_by_liq_price(entry_side, entry_price, liq_price)

        # je nach kalkulation kann leverage zu groß werden
        if leverage > max_possible_leverage:
            leverage = max_possible_leverage



        position_size = self.__calculate_position_size_by_fixed_risk(entry_price, stop_loss_price)
        order_cost = self.__get_order_cost(entry_side, entry_price, position_size, leverage)

        if order_cost > self.money_balance:
            # wenn hier hin kommt wird immer risk reduziert
            # leverage muss gleich bleiben damit liq price & bankruptcy price gleich bleiben


            # neue position size und order cost anhand von verfügbarem geld berechnen
            position_size = self.__calculate_position_size_by_money_balance(entry_side, entry_price, leverage)


            order_cost = self.__get_order_cost(entry_side, entry_price, position_size, leverage)

            # prüfen ob order cost passt
            # da bei __calculate_position_size nachkommastellen entfernt werden (weil bybit nur bestimmte anzahl nimmt) sollte order cost immer kleiner oder gleich sein
            if order_cost > self.money_balance:
                self.__raise_exception(entry_side, entry_price, stop_loss_price, position_size, leverage, order_cost)


            temp_fixed_risk = (position_size*entry_price)*(abs(entry_price-stop_loss_price)/entry_price)
            file_writer.append_to_log_position_manager(f'fixed risk changed to {temp_fixed_risk}')
        

        return float(position_size), float(leverage)






    def __raise_exception(self, entry_side, entry_price, stop_loss_price, position_size, leverage, order_cost):
        file_writer.append_to_log_position_manager(f'order cost too much')
        file_writer.append_to_log_position_manager(f'entry_side {entry_side}')
        file_writer.append_to_log_position_manager(f'entry_price {entry_price}')
        file_writer.append_to_log_position_manager(f'stop_loss_price {stop_loss_price}')
        file_writer.append_to_log_position_manager(f'position_size {position_size}')
        file_writer.append_to_log_position_manager(f'leverage {leverage}')
        file_writer.append_to_log_position_manager(f'order_cost {order_cost}')
        file_writer.append_to_log_position_manager(f'money_balance {self.money_balance}')
        raise





    def __get_order_cost(self, entry_side, entry_price, position_size, leverage):
        bankruptcy_price = self.__get_bankruptcy_price(entry_side, entry_price, leverage)

        order_cost = (entry_price*position_size)/leverage # initial margin
        # bybit reserviert/addiert dies hinzu
        order_cost += self.__get_fee(entry_price, position_size, taker_fee_percent) # entry price taker fee
        order_cost += self.__get_fee(bankruptcy_price, position_size, taker_fee_percent) # bankruptcy price taker fee
        return order_cost





    def __calculate_position_size_by_money_balance(self, entry_side, entry_price, leverage):
        bankruptcy_price = self.__get_bankruptcy_price(entry_side, entry_price, leverage)
        position_size = self.money_balance/( (entry_price/leverage) + (entry_price*(taker_fee_percent/100)) + (bankruptcy_price*(taker_fee_percent/100)) )

        # cutting off rest numbers, nicht runden, Bybit kalkuliert so
        position_size *= 10**number_decimals_calc_position_size
        position_size = Decistr(int(position_size))
        position_size /= 10**number_decimals_calc_position_size

        return position_size





    def __calculate_position_size_by_fixed_risk(self, entry_price, stop_loss_price):

        risk_value_ticks = abs(Decistr(entry_price)-Decistr(stop_loss_price))
        position_size = Decistr(risk_per_trade)/risk_value_ticks

        # cutting off rest numbers, Bybit kalkuliert so
        position_size *= 10**number_decimals_calc_position_size
        position_size = Decistr(int(position_size))
        position_size /= 10**number_decimals_calc_position_size

        return position_size






    def __get_leverage_by_liq_price(self, entry_side, entry_price, liq_price):
        '''
        wenn liquidation price weiter weg gesetzt wird als vorher, wird auch leverage somit geringer
        '''
        if entry_side == 'Buy':
            return 1/(1+(maintenance_margin_rate_percent/100)-(Decistr(liq_price)/Decistr(entry_price)))
        else:
            return 1/(-1+(maintenance_margin_rate_percent/100)+(Decistr(liq_price)/Decistr(entry_price)))





    def __get_bankruptcy_price(self, entry_side, entry_price, leverage):
        leverage = Decistr(leverage)
        if entry_side == 'Buy':
            return Decistr(entry_price)*(1-(1/leverage))
        else:
            return Decistr(entry_price)*(1+(1/leverage))





    def __get_fee(self, order_price, order_size, fee_percent):
        return Decistr(order_price)*Decistr(order_size)*(Decistr(fee_percent)/100)






