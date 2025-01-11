
import time
from threading import Thread
from multiprocessing import Queue

from Bybit_Access import bybit_usdt_perp_client
from settings import general_specifications
import super_global_variables as super_globals
from general_helper_functions import Decistr
from market_insertion import filling_and_orders_manager
from logs_and_data import file_writer

tick_value = Decistr(general_specifications.tick_value)
time_frame = general_specifications.time_frame
smallest_position_size = Decistr(general_specifications.smallest_position_size)
number_decimals_calc_position_size = general_specifications.number_decimals_calc_position_size


'''
auch wenn Preis bei stop loss filling in gute Richtung geht trotzdem neue limit order setzen und position trade mit guten deviations schließen,
weil man backtesting folgen muss (alles muss wie in backtesting sein)

alternativen:
- stop loss filling beenden und auf take profit fill warten oder wieder stop loss filling anfangen wenn stop loss hit
- market exit von vorheriger position wenn eine neue wegen backtesting geöffnet werden soll
- parallele position trades mit Hilfe von mehreren subaccs & threads





egal ob buy oder sell market order, taker fees werden mehr je höher der preis (bei gleicher base currency size zB BTC)

je höher der entry, desto größer die taker fee, da mehr size benötigt wird

je höher der preis auf dem position trade gemacht wird, desto mehr abs price movement ist notwenig damit deviations gleich wie taker fees sind
- weil wegen höherem preis taker fee mehr wird
- volatilität ist aber auch mehr

'''






current_id_counter = 0

def start_stop_loss_filling(stop_loss_side: str, stop_loss_price: str, position_size: str, risk_value_ticks: str):
    '''
    insert desired way to deal with stop loss here 
    '''
    global current_id_counter, filled_quantities_queue

    filled_quantities_queue = Queue()

    current_id_counter += 1
    current_id = 'sl_id_'+str(current_id_counter)

    file_writer.append_to_log_position_manager('starting stop loss filling using SplitFillingAndRapid')
    split_filling = SplitFillingAndRapid(current_id, stop_loss_side, stop_loss_price, position_size, risk_value_ticks)
    stop_loss_result = split_filling.begin()

    if type(stop_loss_result) == tuple:
        file_writer.append_to_log_position_manager('starting stop loss filling using OnlyRapidWithTakerBoundary')
        abs_volatility_stop_loss = OnlyRapidWithTakerBoundary(current_id, stop_loss_side, stop_loss_price, float(stop_loss_result[0]), risk_value_ticks)
        stop_loss_result = abs_volatility_stop_loss.begin(stop_loss_result[1])

    return stop_loss_result




















class OnlyRapidWithTakerBoundary:
    '''
    - only uses rapid limit exit
    - at certain loss distance uses market order
    - at certain win distance aborts sl filling, so tp can be placed
    '''



    def __init__(self, filling_process_id: str, stop_loss_side: str, stop_loss_price: float, position_size: float, risk_value_size: float) -> None:
        self.filling_process_id: str = filling_process_id
        self.stop_loss_side: str = stop_loss_side
        self.stop_loss_price: float = stop_loss_price
        self.risk_value_size: float = risk_value_size

        self.stop_loss_remaining_size: float = position_size
        self.stop_loss_filled_size: float = 0 # 0 für market order exit, ansonsten wird überschrieben

        self.stop_loss_limit_order_id: str = None
        self.current_sl_price: float = stop_loss_price

        self.stop_loss_filling_start: float = None

        distance_for_abort = Decistr(risk_value_size)*Decistr(0.5)
        distance_for_market = Decistr(risk_value_size)*Decistr(0.5)

        if stop_loss_side == 'Buy':
            self.abort_sl_filling_borderline = float(Decistr(stop_loss_price)-distance_for_abort)
            self.market_order_borderline = float(Decistr(stop_loss_price)+distance_for_market)
        else:
            self.abort_sl_filling_borderline = float(Decistr(stop_loss_price)+distance_for_abort)
            self.market_order_borderline = float(Decistr(stop_loss_price)-distance_for_market)



    # gegenteilige Seite nutzen damit orderbook gaps genutzt wird

    def __get_price_for_buy_sl_side(self) -> float:
        return float(Decistr(bybit_usdt_perp_client.get_ask_price())-tick_value)

    def __get_price_for_sell_sl_side(self) -> float:
        return float(Decistr(bybit_usdt_perp_client.get_bid_price())+tick_value)



    


    def __abort_stop_loss_filling(self) -> bool:
        '''
        returns true if the price moved very far into win direction
         > only applies when market is extremely fast
        '''
        # absichtlich ask/bid so herum
        if self.stop_loss_side == 'Buy':
            # besser so rum wenn markt schnell ist (viele takers order kamen rein, erzeugen evtl große lücke)
            if bybit_usdt_perp_client.get_ask_price() < self.abort_sl_filling_borderline:
                return True
            else:
                return False
        else:
            if bybit_usdt_perp_client.get_bid_price() > self.abort_sl_filling_borderline:
                return True
            else:
                return False



    def __should_do_market_order_exit(self) -> bool:
        '''
        True == yes, do taker order exit
        False == no
        '''
        # absichtlich bid/ask so herum
        if self.stop_loss_side == 'Buy':
            if bybit_usdt_perp_client.get_bid_price() > self.market_order_borderline:
                return True
            else:
                return False

        else:
            if bybit_usdt_perp_client.get_ask_price() < self.market_order_borderline:
                return True
            else:
                return False



    def __does_current_price_differ_from_order_price(self) -> bool:
        '''
        True == yes, it does
        False == no
        '''
        if self.stop_loss_side == 'Buy':
            current_price = self.__get_price_for_buy_sl_side()
        else:
            current_price = self.__get_price_for_sell_sl_side()
        
        if current_price != self.current_sl_price:
            return True
        else:
            return False



    def __place_limit_sl_order(self):
        # so herum denn soll auch order book gaps nutzen
        if self.stop_loss_side == 'Buy':
            self.current_sl_price = self.__get_price_for_buy_sl_side()
        else:
            self.current_sl_price = self.__get_price_for_sell_sl_side()

        self.stop_loss_limit_order_id = bybit_usdt_perp_client.place_limit_order(self.stop_loss_side, self.current_sl_price, self.stop_loss_remaining_size)

        status_check = filling_and_orders_manager.limit_order_status_check(self.stop_loss_limit_order_id)

        if status_check == 'placing limit order not possible':
            return f'placing {self.stop_loss_side} limit stop loss order at {self.current_sl_price} not possible, bid: {bybit_usdt_perp_client.get_bid_price()} ask: {bybit_usdt_perp_client.get_ask_price()}'

        elif status_check == 'order open':
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} limit stop loss order placed at {self.current_sl_price} with size {self.stop_loss_remaining_size}')
            return 'limit stop loss order placed'

        elif status_check == self.stop_loss_remaining_size:
            self.stop_loss_filled_size = status_check
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} limit stop loss order at {self.current_sl_price} with size {self.stop_loss_remaining_size} filled completely')
            return 'limit stop loss order filled completely'
        
        else: # partial fill
            self.stop_loss_filled_size = status_check
            self.stop_loss_remaining_size = float(Decistr(self.stop_loss_remaining_size)-Decistr(self.stop_loss_filled_size))
            file_writer.save_stop_loss_fill(self.filling_process_id, self.stop_loss_side, 'limit', self.stop_loss_price, self.current_sl_price, self.stop_loss_filled_size, self.risk_value_size, 'OnlyRapidWithTakerBoundary', str(Decistr(time.time())-self.stop_loss_filling_start))
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} limit stop loss order at {self.current_sl_price} filled partially size {self.stop_loss_filled_size}')
            return 'limit stop loss order filled partially'





    def __cancel_limit_sl_order(self):
        if self.stop_loss_limit_order_id == None:
            return 'order canceled'

        while super_globals.running:
            bybit_usdt_perp_client.cancel_order(self.stop_loss_limit_order_id)
            if bybit_usdt_perp_client.is_order_open(self.stop_loss_limit_order_id) == False:
                break

        self.stop_loss_filled_size = bybit_usdt_perp_client.get_filled_size(self.stop_loss_limit_order_id, False)

        if self.stop_loss_filled_size == self.stop_loss_remaining_size:
            file_writer.save_stop_loss_fill(self.filling_process_id, self.stop_loss_side, 'limit', self.stop_loss_price, self.current_sl_price, self.stop_loss_filled_size, self.risk_value_size, 'OnlyRapidWithTakerBoundary', str(Decistr(time.time())-self.stop_loss_filling_start))
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} limit stop loss order at {self.current_sl_price} with size {self.stop_loss_remaining_size} filled completely')
            return 'limit stop loss order filled completely'
        elif self.stop_loss_filled_size > 0:
            self.stop_loss_remaining_size = float(Decistr(self.stop_loss_remaining_size)-Decistr(self.stop_loss_filled_size))
            file_writer.save_stop_loss_fill(self.filling_process_id, self.stop_loss_side, 'limit', self.stop_loss_price, self.current_sl_price, self.stop_loss_filled_size, self.risk_value_size, 'OnlyRapidWithTakerBoundary', str(Decistr(time.time())-self.stop_loss_filling_start))
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} limit stop loss order at {self.current_sl_price} filled partially size {self.stop_loss_filled_size}')
            return 'limit stop loss order filled partially'
        else:
            file_writer.append_to_log_position_manager(f'{self.stop_loss_side} stop loss order at {self.current_sl_price} with size {self.stop_loss_remaining_size} canceled')
            return 'order canceled'










    def begin(self, filling_start = None):



        def __exit_with_market_order():
            # sl_remaining_size calculation hat schon vorher stattgefunden
            market_order_id = bybit_usdt_perp_client.place_market_order(self.stop_loss_side, self.stop_loss_remaining_size)
            while True:
                self.stop_loss_filled_size = bybit_usdt_perp_client.get_filled_size(market_order_id)
                if self.stop_loss_filled_size == self.stop_loss_remaining_size:
                    break
            avg_fill_price = bybit_usdt_perp_client.get_avg_filled_price(market_order_id)
            file_writer.save_stop_loss_fill(self.filling_process_id, self.stop_loss_side, 'market', self.stop_loss_price, avg_fill_price, self.stop_loss_filled_size, self.risk_value_size, 'OnlyRapidWithTakerBoundary', str(Decistr(time.time())-self.stop_loss_filling_start))
            return 'stop loss market order exit'




        def __do_rapid_limit_exit():

            def __check_rapid_stop_loss_order_fill():
                self.stop_loss_filled_size = bybit_usdt_perp_client.get_filled_size(self.stop_loss_limit_order_id)

                # wichtig in dieser Reihenfolge zu überprüfen
                if self.stop_loss_filled_size == self.stop_loss_remaining_size:
                    return 'limit stop loss order filled completely'

                elif self.__abort_stop_loss_filling() == True:
                    return 'abort stop loss filling'

                elif self.__should_do_market_order_exit() == True:
                    return 'stop loss market order exit'

                elif self.__does_current_price_differ_from_order_price() == True:
                    return 'place new limit order'



            # wenn in loop ist und keine order setzen kann soll checken was ab geht

            if self.__abort_stop_loss_filling() == True:
                return 'abort stop loss filling'

            elif self.__should_do_market_order_exit() == True:
                return 'stop loss market order exit'

            limit_sl_order = self.__place_limit_sl_order()
            if limit_sl_order != 'limit stop loss order placed':
                return limit_sl_order


            while super_globals.running:
                check_fill = __check_rapid_stop_loss_order_fill()
                if check_fill != None:
                    return check_fill
                else:
                    time.sleep(0.125)



        if filling_start == None:
            self.stop_loss_filling_start = Decistr(time.time())
        else:
            self.stop_loss_filling_start = filling_start

        while super_globals.running:
            rapid_limit_exit = __do_rapid_limit_exit()

            file_writer.append_to_log_position_manager(rapid_limit_exit + ' (stop_loss_filling.py)')

            if rapid_limit_exit == 'limit stop loss order filled completely':
                file_writer.save_stop_loss_fill(self.filling_process_id, self.stop_loss_side, 'limit', self.stop_loss_price, self.current_sl_price, self.stop_loss_filled_size, self.risk_value_size, 'OnlyRapidWithTakerBoundary', str(Decistr(time.time())-self.stop_loss_filling_start))
                return rapid_limit_exit

            elif rapid_limit_exit == 'abort stop loss filling':
                # fill wurde schon gespeichert
                cancel_order = self.__cancel_limit_sl_order()
                if cancel_order == 'limit stop loss order filled completely':
                    return cancel_order
                elif cancel_order == 'limit stop loss order filled partially':
                    continue # soll weitermachen
                else:
                    return rapid_limit_exit

            elif rapid_limit_exit == 'stop loss market order exit':
                cancel_order = self.__cancel_limit_sl_order()
                if cancel_order == 'limit stop loss order filled completely':
                    return cancel_order
                # partial fill oder cancel soll market order setzen
                # fill wurde schon gespeichert
                return __exit_with_market_order()

            elif rapid_limit_exit == 'place new limit order':
                # fill wurde schon gespeichert
                cancel_order = self.__cancel_limit_sl_order()
                if cancel_order == 'limit stop loss order filled completely':
                    return cancel_order
                else: # partial fill oder cancel
                    continue # soll weitermachen da neue order

            # bei restlichen weitermachen:
            # 'placing limit stop loss order not possible', 'limit stop loss order filled partially'





















class StopLossLimitOrder:


    def __init__(self,
                 side: str, price: float, size: float,
                 filling_process_id: str, stop_loss_price: str, risk_value_ticks: str,
                 filling_type: str, filling_start: str
                 ) -> None:
        
        
        
        self.order_side = side
        self.order_price = price
        self.order_remaining_size = size
        self.filling_process_id = filling_process_id
        self.stop_loss_price = stop_loss_price
        self.risk_value_ticks = risk_value_ticks
        self.filling_type = filling_type
        self.filling_start = Decistr(filling_start)

        self.order_filled_size = None
        self.order_id = None

        self.order_placement_thread = Thread()
        self.update_status_thread = Thread()
        self.order_cancel_thread = Thread()
        self.get_status_thread = Thread()

        self.order_open = False
        self.delete_this = False
        self.status = None


    def set_price(self, price: float):
        if self.order_open == False:
            self.order_price = price


    def place_order(self):

        def __for_thread():
            self.order_id = bybit_usdt_perp_client.place_limit_order(self.order_side, self.order_price, self.order_remaining_size)
            file_writer.append_to_log_position_manager(f'{self.order_side} limit stop loss order placed at {self.order_price} with size {self.order_remaining_size}')

        if self.order_open == False: # objekt bleibt in der list daher if Abfrage notwendig, ansonsten setzt order ungewollt
            self.order_placement_thread = Thread(target=__for_thread)
            self.order_placement_thread.start()


    def close_order(self):
        '''
        gibt 'placing limit order not possible' nicht zurück, wie von vscode behauptet
        '''

        def __for_thread():
            if self.order_placement_thread.is_alive() == True: # sonst exception wenn thread nicht läuft
                self.order_placement_thread.join()
            if self.order_id == None: # close_order() called before any order was placed, happens on 'rapid'
                return
            bybit_usdt_perp_client.cancel_order(self.order_id)

        self.order_cancel_thread = Thread(target=__for_thread)
        self.order_cancel_thread.start()


    def update_status(self):

        def __handle_status_check(status_check: str):
            if status_check == 'placing limit order not possible':
                file_writer.append_to_log_position_manager(f'placing {self.order_side} limit stop loss order at {self.order_price} not possible, bid: {bybit_usdt_perp_client.get_bid_price()} ask: {bybit_usdt_perp_client.get_ask_price()}')
                self.order_open = False
                return status_check

            elif status_check == 'order open':
                self.order_open = True
                return status_check

            elif status_check == self.order_remaining_size:
                self.order_filled_size = status_check
                file_writer.save_stop_loss_fill(self.filling_process_id, self.order_side, 'limit', self.stop_loss_price, self.order_price, self.order_filled_size, self.risk_value_ticks, self.filling_type, str(Decistr(time.time())-self.filling_start))
                file_writer.append_to_log_position_manager(f'{self.order_side} limit stop loss order at {self.order_price} with size {self.order_remaining_size} filled completely')
                self.order_open = False
                self.delete_this = True
                return 'limit stop loss order filled completely'
            
            else: # closed order partial fill
                self.order_filled_size = status_check
                self.order_remaining_size = float(Decistr(self.order_remaining_size)-Decistr(self.order_filled_size))
                file_writer.save_stop_loss_fill(self.filling_process_id, self.order_side, 'limit', self.stop_loss_price, self.order_price, self.order_filled_size, self.risk_value_ticks, self.filling_type, str(Decistr(time.time())-self.filling_start))
                file_writer.append_to_log_position_manager(f'{self.order_side} limit stop loss order at {self.order_price} filled partially size {self.order_filled_size}')
                self.order_open = False
                return 'limit stop loss order filled partially'

        def __for_thread():
            if self.order_placement_thread.is_alive() == True: # sonst exception wenn thread nicht läuft
                self.order_placement_thread.join()
            if self.order_cancel_thread.is_alive() == True: # sonst exception wenn thread nicht läuft
                self.order_cancel_thread.join()
            if self.order_id == None:
                return
            status_check = filling_and_orders_manager.limit_order_status_check(self.order_id)
            self.status = __handle_status_check(status_check)

        self.update_status_thread = Thread(target=__for_thread)
        self.update_status_thread.start()


    def get_status(self):

        def __for_thread():
            if self.update_status_thread.is_alive() == True: # sonst exception wenn thread nicht läuft
                self.update_status_thread.join()
            if self.order_filled_size != None:
                filled_quantities_queue.put(self.order_filled_size)

        self.get_status_thread = Thread(target=__for_thread)
        self.get_status_thread.start()


    def wait_for_status_to_finish(self):
        if self.get_status_thread.is_alive() == True: # sonst exception wenn thread nicht läuft
            self.get_status_thread.join()


    def is_up_for_deletion(self):
        return self.delete_this


    def is_order_open(self):
        return self.order_open
















class SplitFillingAndRapid:
    '''
    bei downsettling mit 1m time frame bleibt max 1m Zeit für stop loss filling
    daher:

    wenn genug Zeit ist teil position size auf in viele orders um den stop loss preis herum
    in positive & negative slippage
    
    wenn nicht genug Zeit ist dann geht in rapid über
    '''

    seconds_left_start_rapid = 10 # oder weniger
    split_number_orders: int = 9 # position size auf wie viele orders aufteilen


    def __init__(self, filling_process_id: str, stop_loss_side: str, stop_loss_price: str, position_size: str, risk_value_ticks: str) -> None:
        self.filling_process_id: str = filling_process_id
        self.stop_loss_side: str = stop_loss_side
        self.stop_loss_price = Decistr(stop_loss_price)
        self.risk_value_ticks = Decistr(risk_value_ticks)

        self.stop_loss_remaining_size = Decistr(position_size)

        self.stop_loss_filling_start: float = None
        self.all_limit_orders: list[StopLossLimitOrder] = []

        self.number_remaining_to_fill = self.split_number_orders




    def __check_what_type_of_filling(self):
        seconds_left = int(time.time())
        while seconds_left % (time_frame*60) != 0:
            seconds_left += 1
        seconds_left -= int(time.time())

        if seconds_left <= self.seconds_left_start_rapid:
            return 'rapid'
        else:
            return 'split'



    def __get_splitted_order_sizes(self):
        rem_size = self.stop_loss_remaining_size
        rem_size *= 10**number_decimals_calc_position_size
        
        rest = rem_size % self.number_remaining_to_fill
        size = (rem_size-rest)/self.number_remaining_to_fill

        rest /= 10**number_decimals_calc_position_size
        size /= 10**number_decimals_calc_position_size
        
        split_position_sizes = [size for _ in range(self.number_remaining_to_fill)]

        for i in range(len(split_position_sizes)):
            if rest == 0:
                break
            split_position_sizes[i] += smallest_position_size
            rest -= smallest_position_size

        split_position_sizes = [float(s) for s in split_position_sizes if s != 0]
        self.number_remaining_to_fill = len(split_position_sizes)
        return split_position_sizes



    def __get_prices(self):
        '''
        bei stop loss anfangen & postive, negative slippage abwechselnd bis remaining_orders erreicht ist

        die zurückgegebene preise sind solche auf denen genau in diesem moment exit orders gesetzt werden können
        dort soll versucht werden order zu setzen
        daraufhin erneut preise abfragen, orders checken, orders canceln etc
        '''
        if self.stop_loss_side == 'Buy':
            limit_of_placing = Decistr(bybit_usdt_perp_client.get_ask_price())-tick_value
        else:
            limit_of_placing = Decistr(bybit_usdt_perp_client.get_bid_price())+tick_value

        # all_prices = [self.stop_loss_price] # wenn stop loss hit zB für Buy durch ask entsteht kann auf ask keine order gesetzt werden
        all_prices = []
        positive_multiplier = 1
        negative_multiplier = 1
        additional_positive = 0

        # for i in range(1, self.remaining_orders): # 1 da self.stop_loss_price bereits enthalten
        for i in range(1, self.number_remaining_to_fill+1):
            
            if i % 2 == 1: # positive slippage ist dran
                if self.stop_loss_side == 'Buy':
                    all_prices.append(self.stop_loss_price-(positive_multiplier*tick_value))
                else:
                    all_prices.append(self.stop_loss_price+(positive_multiplier*tick_value))
                positive_multiplier += 1
            else: # negative slippage ist dran
                if self.stop_loss_side == 'Buy':
                    price = self.stop_loss_price+(negative_multiplier*tick_value)
                    if price <= limit_of_placing:
                        all_prices.append(price)
                    else:
                        additional_positive += 1
                else:
                    price = self.stop_loss_price-(negative_multiplier*tick_value)
                    if price >= limit_of_placing:
                        all_prices.append(price)
                    else:
                        additional_positive += 1
                negative_multiplier += 1

        for _ in range(additional_positive):
            if self.stop_loss_side == 'Buy':
                all_prices.append(self.stop_loss_price-(positive_multiplier*tick_value))
            else:
                all_prices.append(self.stop_loss_price+(positive_multiplier*tick_value))
            positive_multiplier += 1

        return [float(p) for p in all_prices]



    def begin(self):
        '''
        returned tuple ist (stop_loss_remaining_size, stop_loss_filling_start)
        '''

        self.stop_loss_filling_start = Decistr(time.time())

        filling_type = self.__check_what_type_of_filling()

        if filling_type == 'split':
            # in dieser Reihenfolge wegen number_remaining_to_fill
            order_sizes = self.__get_splitted_order_sizes()
            order_prices = self.__get_prices()

            # objekte kreieren
            for i in range(len(order_sizes)):
                self.all_limit_orders.append(
                    StopLossLimitOrder(
                        self.stop_loss_side, order_prices[i], order_sizes[i],
                        self.filling_process_id, self.stop_loss_price, self.risk_value_ticks,
                        self.__class__.__name__, self.stop_loss_filling_start
                    )
                )


        while super_globals.running:
            # threads hängen aneinander & warten, erst wenn alle fertig sind wird Schleife wiederholt

            if filling_type == 'rapid':
                # orders canceln, ist parallel
                for order in self.all_limit_orders:
                    order.close_order()
                
                # orders prüfen, ist parallel
                for order in self.all_limit_orders:
                    order.update_status()

                # ist parallel
                for order in self.all_limit_orders:
                    order.get_status()

                # ist sequenziell damit code wartet
                for order in self.all_limit_orders:
                    order.wait_for_status_to_finish()

                while filled_quantities_queue.empty() == False:
                    self.stop_loss_remaining_size -= Decistr(filled_quantities_queue.get())

                if self.stop_loss_remaining_size == 0:
                    return 'limit stop loss order filled completely'

                return self.stop_loss_remaining_size, self.stop_loss_filling_start            

            else:
                # in meheren schleifen wegen join()

                # orders setzen, ist parallel
                for order in self.all_limit_orders:
                    order.place_order()

                # orders prüfen, ist parallel
                for order in self.all_limit_orders:
                    order.update_status()

                # mit status arbeiten, ist parallel
                for order in self.all_limit_orders:
                    order.get_status()

                # ist sequenziell damit code wartet
                for order in self.all_limit_orders:
                    order.wait_for_status_to_finish()

                while filled_quantities_queue.empty() == False:
                    self.stop_loss_remaining_size -= Decistr(filled_quantities_queue.get())

                if self.stop_loss_remaining_size == 0:
                    return 'limit stop loss order filled completely'


                number_orders_not_open = 0
                # nur diese orders (objekte) die nicht gesetzt werden konnten, teilweise gefüllt (closed) oder offen sind bleiben in der liste
                for i in range(len(self.all_limit_orders)-1, -1, -1):
                    order = self.all_limit_orders[i]
                    if order.is_up_for_deletion() == True:
                        del self.all_limit_orders[i]
                    elif order.is_order_open() == False:
                        number_orders_not_open += 1

                # neue preise für solche die nicht gesetzt werden konnten oder teilweise gefüllt (closed) sind
                self.number_remaining_to_fill = number_orders_not_open
                order_prices = self.__get_prices()

                where_start = 0
                for price in order_prices:
                    for x in range(where_start, len(self.all_limit_orders)):
                        order = self.all_limit_orders[x]
                        if order.is_order_open() == False:
                            order.set_price(price)
                            where_start = x+1
                            break

                time.sleep(0.5)
                filling_type = self.__check_what_type_of_filling()


