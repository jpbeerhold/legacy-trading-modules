
from typing import Dict
import socket, os, time, pickle, sys
from threading import Thread, Lock
from datetime import datetime

sys.path.append('/home/Bybit') # für pybit ordner

from pybit.unified_trading import WebSocket



available_sockets = ['kline_socket', 'orderbook_socket', 'trade_socket']

running = True

category = 'linear'
symbol = 'BTCUSDT'




def _handle_received_orderbook(orderbook_data: Dict):
    orderbook_data = orderbook_data['data']
    orderbook_data = {
        'ask_price': orderbook_data['a'][0][0],
        'bid_price': orderbook_data['b'][0][0]
    }
    
    for socket in available_sockets:
        if socket['address'] == 'orderbook_socket':
            socket['object'].send_to_all_clients('orderbook', orderbook_data)
            return




def _handle_received_candle(candle_data: Dict):
    # confirm candle erreicht nach ca 330ms
    candle_data = candle_data['data'][0]
    if candle_data['confirm'] == True:
        candle_data = {
            'timestamp': str(int(candle_data['start']/1000)),
            'open': str(candle_data['open']),
            'high': str(candle_data['high']),
            'low': str(candle_data['low']),
            'close': str(candle_data['close']),
            'volume': str(candle_data['volume']),
            'turnover': str(candle_data['turnover'])
        }

        for socket in available_sockets:
            if socket['address'] == 'kline_socket':
                socket['object'].send_to_all_clients('kline', candle_data)
                return




def _handle_received_trades(trades_data: Dict):
    # trades data kann mehrere trades enthalten
    all_trades = []
    trades_data = trades_data['data'] # list[dict]
    for trade in trades_data:
        all_trades.append({
            'timestamp': str(trade['T']/1000),
            'price': str(trade['p']),
            'size': str(trade['v'])
        })
    
    for socket in available_sockets:
        if socket['address'] == 'trade_socket':
            socket['object'].send_to_all_clients('trade', all_trades)
            return








def start_websocket_client():

    usdt_perp_ws_client = WebSocket(
        testnet=False, # if should use testnet
        channel_type=category,
        ping_interval=0.5,
        ping_timeout=0.25,
        retries=0 # bei 0 versucht unendlich wiederzuverbinden
    )

    usdt_perp_ws_client.orderbook_stream(depth=1, symbol=symbol, callback=_handle_received_orderbook)
    usdt_perp_ws_client.kline_stream(interval=1, symbol=symbol, callback=_handle_received_candle)
    usdt_perp_ws_client.trade_stream(symbol=symbol, callback=_handle_received_trades)











class Server:
    '''
    jedes socket hat eine Server Klasse, die sich um alle Clients an diesem Socket kümmert
    pro socket wird nur eine Art von Daten übertragen
    '''

    buffer_size = 1024
    timeout = 0.1
    bytes_encoding = 'utf-8'


    def __init__(self, socket_address: str) -> None:
        if os.path.exists(socket_address):
            os.remove(socket_address)
        self.all_clients = []
        self.thread_lock = Lock()
        self.socket_address = socket_address
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.bind(socket_address)
        self.s.listen()

    def _append_to_log(self, text: str):
        with open(f'server_{self.socket_address}.log', 'a') as f:
            current_datetime = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')
            f.write('@ ' + current_datetime + ' -> ' + text + '\n')


    def begin(self):
        server_thread = Thread(target=self._accept_new_clients)
        server_thread.start()


    def _accept_new_clients(self):
        self._append_to_log('server started')
        while running:
            clientsocket, address = self.s.accept()
            handle_thread = Thread(target=self._handle_new_client, args=(clientsocket,))
            handle_thread.start()


    def _handle_new_client(self, clientsocket):
        self._append_to_log(f'new client at {self.socket_address}')
        clientsocket.settimeout(self.timeout)
        
        try:
            clientsocket.sendall(bytes('who are you', self.bytes_encoding))
            client_name = clientsocket.recv(self.buffer_size).decode(self.bytes_encoding)
        except TimeoutError:
            self._append_to_log('new client timed out')
            return

        self._append_to_log(f'connection to {client_name} established')
        clientsocket.settimeout(None)
        while self.thread_lock.locked():
            continue
        self.all_clients.append( {'clientname': client_name, 'clientsocket': clientsocket} )


    def send_to_all_clients(self, topic: str, python_dict: Dict):
        python_dict = {'topic': topic, 'data': python_dict}
        for i in range(len(self.all_clients)-1, -1, -1):
            try:
                current_clientname = self.all_clients[i]['clientname']
                current_clientsocket = self.all_clients[i]['clientsocket']
                current_clientsocket.sendall(pickle.dumps(python_dict))
                msg = current_clientsocket.recv(self.buffer_size).decode(self.bytes_encoding)
                if msg != 'data received':
                    raise OSError

            except OSError:
                self._append_to_log(f'client {current_clientname} offline')
                current_clientsocket.close()
                with self.thread_lock:
                    del self.all_clients[i]








def main():
    for i in range(len(available_sockets)):
        new_server = Server(available_sockets[i])
        available_sockets[i] = {'address': available_sockets[i], 'object': new_server}

    for socket in available_sockets:
        socket['object'].begin()

    start_websocket_client()








if __name__ == '__main__':
    main()












'''

fehlt noch / unterstützt nicht:

wenn in gleichem socket daten gerade gesendet werden und neue daten reinkommen soll warten bis fertig ist

exception aus thread

verschiedene märkte
-> bei verbindungsaufbau mit client soll markt abgefragt werden

'''




