
from typing import List
from decimal import Decimal
from datetime import datetime

import math, statistics


taker_fee_percent = Decimal('0.06') # Bybit reserviert in dieser Höhe








def afunc_private_setup(p_tick_value: str, p_time_frame: int, p_ohlc_data_time_frame: int, p_ohlc_data_file_path: str):
    global tick_value, time_frame, ohlc_data_time_frame, ohlc_data_file_path
    tick_value = Decistr(p_tick_value)
    time_frame = p_time_frame
    ohlc_data_time_frame = p_ohlc_data_time_frame
    ohlc_data_file_path = p_ohlc_data_file_path




def Decistr(number) -> Decimal:
    n_type = type(number)
    if n_type == Decimal:
        return number
    elif n_type == str:
        return Decimal(number)
    elif n_type == int:
        # conversion to str from int no Problem
        return Decimal(str(number))
    else:
        raise Exception(f'bad datatype, its {type(number)}')



def round_up_to(number):
    number = Decistr(number)
    decimal_type = Decistr(tick_value)
    return math.ceil(number/decimal_type)*decimal_type



def round_down_to(number):
    number = Decistr(number)
    decimal_type = Decistr(tick_value)
    return math.floor(number/decimal_type)*decimal_type



def to_nearest(number):
    number = Decistr(number)
    decimal_type = Decistr(tick_value)
    return round(number/decimal_type)*decimal_type



def get_timestamp_to_datetime(timestamp):
    # Must have this format to work for pandas! -> '%Y-%m-%d %H:%M:%S'
    return datetime.utcfromtimestamp(int(Decistr(timestamp))).strftime('%Y-%m-%d %H:%M:%S')








def get_reward_size(trade_history, number_decimals_perf):
    l = []
    for pos_trade in trade_history:
        if pos_trade[9] == 'win':
            l.append(pos_trade[8])
    if len(l) != 0:
        return round(statistics.mean(l), number_decimals_perf)
    else:
        return 'no trades'



def get_risk_size(trade_history, number_decimals_perf):
    l = []
    for pos_trade in trade_history:
        if pos_trade[9] == 'loss':
            l.append(pos_trade[8])
    if len(l) != 0:
        return round(statistics.mean(l), number_decimals_perf)
    else:
        return 'no trades'








def get_risk_value_performance_as_list(trade_history):
    '''
    returns risk value performance course as list in Decimal values
    '''
    perf_list = []
    p = 0
    for pos_trade in trade_history:
        p += pos_trade[8]
        perf_list.append(p)
    return perf_list








'''
r²
'''


def get_regression_line(trade_history) -> List:
    '''
    returns a List with y data only, so linear graph can be plottet
    '''



    def get_regression_function():
        '''
        returns m (slope) and b (y-intercept) as Decimals
        '''
        y_data = get_risk_value_performance_as_list(trade_history)
        x_data = [i for i in range(1, len(y_data)+1)]

        assert len(x_data) == len(y_data), 'input data lists not same length'
        for i in range(len(x_data)):
            x_data[i] = Decistr(x_data[i])
            y_data[i] = Decistr(y_data[i])

        x_sum = 0
        y_sum = 0
        for i in range(len(x_data)):
            x_sum += x_data[i]
            y_sum += y_data[i]
        if x_sum == 0:
            x_avg = 0
        else:
            x_avg = x_sum/Decistr(len(x_data))
        if y_sum == 0:
            y_avg = 0
        else:
            y_avg = y_sum/Decistr(len(y_data))

        Sxx = 0
        Sxy = 0
        for i in range(len(x_data)):
            Sxx += (x_data[i]-x_avg)**Decistr(2)
            Sxy += (x_data[i]-x_avg)*(y_data[i]-y_avg)

        if Sxy == 0 or Sxx == 0:
            m = 0
        else:
            m = Sxy/Sxx
        b = y_avg-(m*x_avg)

        return {'m': m, 'b': b, 'len_y_data': len(y_data)}



    func_dict = get_regression_function()
    m = Decistr(func_dict['m'])
    b = Decistr(func_dict['b'])
    len_y_data = func_dict['len_y_data']

    regression_line_list = []
    x_data = [i for i in range(1, len_y_data+1)]
    for x_data_point in x_data:
        y_data_point = (x_data_point*m)+b
        regression_line_list.append(y_data_point)
    return regression_line_list








'''
Risk Management
'''



def calculate_position_size_by_money_balance(entry_side: str, entry_price: str, leverage: str, money_balance: str, number_decimals_calc_position_size: int):
    bankruptcy_price = get_bankruptcy_price(entry_side, entry_price, leverage)
    position_size = money_balance/( (entry_price/leverage) + (entry_price*(taker_fee_percent/100)) + (bankruptcy_price*(taker_fee_percent/100)) )

    # cutting off rest numbers, Bybit kalkuliert so
    position_size *= 10**number_decimals_calc_position_size
    position_size = Decistr(int(position_size))
    position_size /= 10**number_decimals_calc_position_size

    return position_size



def calculate_position_size_by_fixed_risk(entry_price: str, stop_loss_price: str, risk_per_trade: str, number_decimals_calc_position_size: int):

    risk_value_ticks = abs(Decistr(entry_price)-Decistr(stop_loss_price))
    position_size = Decistr(risk_per_trade)/risk_value_ticks

    # cutting off rest numbers, Bybit kalkuliert so
    position_size *= 10**number_decimals_calc_position_size
    position_size = Decistr(int(position_size))
    position_size /= 10**number_decimals_calc_position_size

    return position_size



def get_liquidation_price(entry_side: str, entry_price: str, initial_margin_rate_percent: str, maintenance_margin_rate_percent: str):
    '''
    Für Bybit, nur für isolated leverage & keine position ist offen!
    initial_margin_rate & maintenance_margin_rate in %
    '''
    if entry_side == 'long':
        liq_price = Decistr(entry_price)*(1-(Decistr(initial_margin_rate_percent)/100)+(Decistr(maintenance_margin_rate_percent)/100))
        return round_up_to(liq_price)
    else:
        liq_price = Decistr(entry_price)*(1+(Decistr(initial_margin_rate_percent)/100)-(Decistr(maintenance_margin_rate_percent)/100))
        return round_down_to(liq_price)



def get_leverage_by_liq_price(entry_side: str, entry_price: str, liq_price: str, maintenance_margin_rate_percent: str):
    '''
    wenn liquidation price weiter weg gesetzt wird als vorher, wird auch leverage somit geringer
    '''
    if entry_side == 'long':
        return 1/(1+(Decistr(maintenance_margin_rate_percent)/100)-(Decistr(liq_price)/Decistr(entry_price)))
    else:
        return 1/(-1+(Decistr(maintenance_margin_rate_percent)/100)+(Decistr(liq_price)/Decistr(entry_price)))



def get_bankruptcy_price(entry_side: str, entry_price: str, leverage: str):
    leverage = Decistr(leverage)
    if entry_side == 'long':
        return Decistr(entry_price)*(1-(1/leverage))
    else:
        return Decistr(entry_price)*(1+(1/leverage))



def get_fee(order_price: str, order_size: str, fee_percent: str):
    return Decistr(order_price)*Decistr(order_size)*(Decistr(fee_percent)/100)



def get_order_cost(entry_side: str, entry_price: str, position_size: str, leverage: str):
    entry_price = Decistr(entry_price)
    position_size = Decistr(position_size)
    leverage = Decistr(leverage)
    bankruptcy_price = get_bankruptcy_price(entry_side, entry_price, leverage)

    order_cost = (entry_price*position_size)/leverage
    # bybit reserviert/addiert dies hinzu
    order_cost += get_fee(entry_price, position_size, taker_fee_percent)
    order_cost += get_fee(bankruptcy_price, position_size, taker_fee_percent)
    return order_cost


