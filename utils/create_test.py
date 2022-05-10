import asyncio
import random

import time

from struct import pack


class EchoServerClientProtocol(asyncio.Protocol):

    def __init__(self):
        self.times = 0
        self.time = None
        self.transport = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        while True:
            for i in range(1, 11):
                send_data = self.pack_data(i) + self.create_random_data()
                transport.write(send_data)
#                print('send:success!')
                time.sleep(0.1)
            time.sleep(1)

    def data_received(self, data):
        pass

    def connection_lost(self, exc):
        print('Connect lost: {}'.format(self.transport.get_extra_info('peername')))

    def pack_data(self, ChannelNo):
        data_header = b'\xe0\xe9\xe0\xe9\x00\x01'
        other_heard = pack('<bhibbBib',
                           0,
                           3271,
                           2,
                           ChannelNo,
                           int(random.randint(0, 1)),
                           random.randint(0, 255),
                           int(time.time()),
                           50)
        return data_header + other_heard

    def create_random_data(self):
        pd_data = []
        for i in range(50):
            pd_data.append(random.randint(0, 1))
            for x in range(64):
                pd_data.append(int(random.randint(0, 255000) / 1000))
        bytes_data = pack('B' * 50 * 65, *pd_data)
        return bytes_data


loop = asyncio.new_event_loop()
coro = loop.create_server(EchoServerClientProtocol, '127.0.0.1', 8001)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
    pass
except KeyboardInterrupt:
    pass
