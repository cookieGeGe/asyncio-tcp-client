# -*- coding: utf-8 -*- 
# @Time : 2019/6/3 14:50 
# @Author :  
# @Site :  
# @File : redispool.py 
# @Software: PyCharm
import aioredis


class AioRedisOP(object):
    __pool = None
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(AioRedisOP, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        if hasattr(self, 'pool'):
            return
        self.pool = None

    async def create_pool(self, config=None):
        if not config or not getattr(config, 'loop'):
            raise Exception('Redis连接池初始化失败')
        self.pool = await aioredis.create_pool(
            address=(config.host, config.port),
            db=config.db,
            password=config.password,
            minsize=config.minsize,
            maxsize=config.maxsize,
            encoding=config.encoding,
            loop=config.loop
        )
        print(self.pool)
        # return AioRedisOP.__pool

    def get_pool(self):
        # print(self.pool)
        if not self.pool:
            raise Exception('Redis连接池未初始化')

        return self.pool

    async def get_conn(self):
        try:
            with await self.get_pool() as conn:
                return aioredis.Redis(conn)
                # return conn
        except Exception as e:
            print(e)

    async def set(self, key, value, time=None):
        conn = await self.get_conn()
        conn = aioredis.Redis(conn)
        if time:
            await conn.setex(key, time, value)
        else:
            await conn.set(key, value)

    async def get(self, key):
        conn = await self.get_conn()
        return await conn.get(key)

    async def rpush(self, key, value):
        conn = await self.get_conn()
        return await conn.rpush(key, value)

    async def delete(self, key):
        conn = await self.get_conn()
        return await conn.delete(key)

    async def subscribe(self, channel):
        """
        订阅通道
        :param channel:
        :return:
        """
        conn = await self.get_pool().acquire()
        conn = aioredis.Redis(conn)
        one_channel = await conn.subscribe(channel)
        return one_channel[0]

    async def publish(self, channel, msg):
        """
        发布消息
        :param channel: 通道名
        :param msg: 消息
        :return:
        """
        conn = await self.get_conn()
        await conn.publish(channel, msg)
