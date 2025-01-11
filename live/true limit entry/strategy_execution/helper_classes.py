
from general_helper_functions import Decistr
from settings import Down_Settling_Parameters, general_specifications
from logs_and_data import file_writer
import general_helper_functions as ghf

import numpy as np
from scipy import stats
from collections import deque
from threading import Lock




time_frame = general_specifications.time_frame

daily_iqr_inputs = Down_Settling_Parameters.daily_iqr_inputs

sma_length = Down_Settling_Parameters.sma_length

number_back_use_close = Down_Settling_Parameters.number_back_use_close










class DailyIQRHistory:
    def __init__(self, history_len: int, single_fragment_length: int) -> None:
        self.history_len = history_len
        self.list = []
        self.history_average = 0

        self.temp_fragment = []
        self.single_fragment_length = single_fragment_length
    
    def __add(self, data: float) -> None:
        assert type(data) == np.float64
        if len(self.list) + 1 <= self.history_len:
            self.list.append(data)
            self.history_average = np.mean(self.list)
        else:
            del self.list[0]
            self.list.append(data)
            self.history_average = np.mean(self.list)
    
    def add_source(self, source: float) -> None:
        # assert type(source) == float
        source = float(source)
        self.temp_fragment.append(source)
        if len(self.temp_fragment) == self.single_fragment_length:
            iqr = stats.iqr(self.temp_fragment, interpolation = 'midpoint')
            self.__add(iqr)
            self.temp_fragment = []

    def get_average_iqr(self) -> float:
        return float(self.history_average)




vola_iqr_avg = DailyIQRHistory(daily_iqr_inputs[0], daily_iqr_inputs[1])









class SmoothedMovingAverage:
    def __init__(self, length: int) -> None:
        self.length = Decistr(length)
        self.sma_value = 0
    
    def calculate_sma(self, source: float):
        self.sma_value *= self.length-Decistr(1)
        self.sma_value += Decistr(source)
        self.sma_value /= self.length

    def get_sma(self):
        return float(self.sma_value)


sma_object = SmoothedMovingAverage(sma_length)








class CandleHistory:

    def __init__(self, history_length: int) -> None:
        self.history = deque(maxlen=history_length)
        self.candle_tp_before = None
        self.thread_lock = Lock()
    
    def add_candle(self, timestamp: int, close: float):
        if self.is_timestamp_in_history(timestamp):
            return
        if self.candle_tp_before != None:
            assert timestamp == self.candle_tp_before+(time_frame*60), (timestamp, self.candle_tp_before)
        if number_back_use_close == 0:
            sma_object.calculate_sma(close)
            vola_iqr_avg.add_source(close)
        else:
            raise
        with self.thread_lock:
            self.history.append( (timestamp, close) )
        self.candle_tp_before = timestamp
        file_writer.append_to_candle_history_data_file(timestamp, close, vola_iqr_avg.get_average_iqr(), len(vola_iqr_avg.temp_fragment))

    def get_candle(self, number_back: int):
        '''
        returns Tuple as (timestamp: int, close: float)
        '''
        assert number_back >= 0, number_back
        number_back += 1 # zuerst addieren wegen 0
        return self.history[-number_back]
    
    def is_timestamp_in_history(self, tp: int) -> bool:
        while self.thread_lock.locked():
            continue
        all_candles = list(self.history)
        all_timestamps = [candle[0] for candle in all_candles]
        if tp in all_timestamps:
            return True
        else:
            return False


candle_history = CandleHistory(number_back_use_close+1)









class Ticker:

    def __init__(self) -> None:
        self.bid = None
        self.ask = None
        self.datetime = None
        self.thread_lock = Lock()

    def set_bid_ask(self, bid: str, ask: str):
        with self.thread_lock:
            self.bid = Decistr(bid)
            self.ask = Decistr(ask)
            self.datetime = ghf.current_to_datetime()
    
    def get_bid(self):
        while self.thread_lock.locked():
            continue
        return self.bid
    
    def get_ask(self):
        while self.thread_lock.locked():
            continue
        return self.ask

    def get_all(self):
        return {'bid': self.bid, 'ask': self.ask, 'time': self.datetime}


latest_ticker_data = Ticker()











