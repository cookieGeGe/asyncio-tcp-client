# -*- coding: utf-8 -*- 
# @Time : 2019/5/30 17:02 
# @Author :  
# @Site :  
# @File : ProtocolBase.py 
# @Software: PyCharm

import asyncio
import datetime
import random
import struct
from json import dumps, loads

from DBPools.Model import Model_OP
from DBPools.redispool import AioRedisOP
from utils.reload_json_encode import ReloadJSONEncoder


class AnalysisBase(object):

    def __init__(self, loop):
        self._loop = loop
        self._buffer = bytearray()  # 缓存
        self._eof = False
        self._waiter = None
        self.instence_id = None

    def feed(self, data):
        """
        接收数据处理，解析
        :param data:
        :return:
        """
        self._buffer.extend(data)
        self._wakeup_waiter()

    def feed_eof(self):
        self._eof = True
        self._wakeup_waiter()

    async def read(self):
        pass

    async def _read(self):
        if not self._buffer and not self._eof:
            await self._wait_for_data()

        data = bytes(self._buffer)
        del self._buffer[:]
        return data

    async def _wait_for_data(self):
        assert not self._eof
        assert not self._waiter

        self._waiter = self._loop.create_future()
        await self._waiter
        self._waiter = None

    def _wakeup_waiter(self):
        waiter = self._waiter
        if waiter:
            self._waiter = None
            waiter.set_result(None)
