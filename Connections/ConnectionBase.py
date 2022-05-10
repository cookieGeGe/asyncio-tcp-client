# -*- coding: utf-8 -*- 
# @Time : 2019/6/3 9:35 
# @Author :  
# @Site :  
# @File : ConnectionBase.py 
# @Software: PyCharm
import asyncio

import gc

from utils.services_log import info_log


class DataAnaClient(asyncio.Protocol):
    """
    异步 socket 连接对象
    """

    def __init__(self, loop, reader):
        self.loop = loop
        self.reader = reader
        self.transport = None
        self.protocol = None
        self.host = reader.host
        self.port = reader.port
        self.read_task = None
        self.unpack_data_task = None

    def connection_made(self, transport):
        """
        连接成功后回调操作
        :param transport:
        :return:
        """
        self.transport = transport
        # print('connect success')
        self.read_data = self.reader.read(b'')
        asyncio.run_coroutine_threadsafe(self.read_data, self.loop)

    def data_received(self, data):
        """
        将收到的数据添加到缓存
        :param data:
        :return:
        """
        # print('从网络获取到数据包长度：', len(data))
        self.reader.feed(data)

    def eof_received(self):
        self.reader.feed_eof()

    def connection_lost(self, exc):
        """
        断开连接回调，销毁已有任务，垃圾回收， 开始重连
        :param exc:
        :return:
        """
        # print('客户端断开连接!')
        # print(len(asyncio.Task.all_tasks()))
        info_log.error('Site:{} Disconnect! Start canceling unfinished tasks.'.format(self.reader.station_id))
        for task in asyncio.Task.all_tasks():
            if task == self.read_task or task == self.unpack_data_task:
                task.cancel()
        gc.collect()
        # print(len(asyncio.Task.all_tasks()))
        asyncio.run_coroutine_threadsafe(self.reader.reconnect(), self.loop)

    async def stop(self):
        self.loop.stop()
