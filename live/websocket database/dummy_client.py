
from typing import Dict
import socket, time, pickle
from threading import Thread


strategy_name = 'strategyXYZ'

running = True


tp_before = 0
from decimal import Decimal
def unpack_data(topic: str, data: Dict):
    global tp_before
    # change variables etc in strategy by using this function
    print(topic)
    # print(data)
    t1 = Decimal(str(time.time()))
    t2 = t1 - Decimal(str(tp_before))
    print(t2)
    tp_before = t1






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
        while running:
            data = self.s.recv(self.buffer_size)
            python_dict = pickle.loads(data)
            unpack_data(python_dict['topic'], python_dict['data'])
            
            self.s.sendall(bytes('data received', self.bytes_encoding))






KLINE_ADDRESS = 'kline_socket'
TICKER_ADDRESS = 'ticker_socket'





client = Client(KLINE_ADDRESS)

client = Client(TICKER_ADDRESS)

while True:
    time.sleep(1)





