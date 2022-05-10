# -*- coding: utf-8 -*- 
# @Time : 2019/6/10 9:31 
# @Author :  
# @Site :  
# @File : data_services.py 
# @Software: PyCharm
import asyncio
import logging.config
from json import loads

from DBPools import init_db_pool
from DBPools.Model import Model_OP
from DBPools.redispool import AioRedisOP
from Protocols.collectstation import CollectionStation
from utils.services_log import LOGGING_CONFIG_LOCAL, info_log


class MainDataService(object):
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式，程序唯一
        :param args:
        :param kwargs:
        :return:
        """
        if not cls.__instance:
            cls.__instance = super(MainDataService, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        # self.loop.set_debug(True)
        asyncio.set_event_loop(self.loop)
        self.station_dict = {}

    async def init_station(self):
        """
        从数据库获取站点数据，初始化生成站点对应对象
        :return:
        """
        all_station = await Model_OP().get_all_station()
        for station in all_station:
            # print(station)
            self.station_dict.update({
                str(station['stationid']): CollectionStation(self.loop, (station['ip'], station['port']),
                                                             station['stationid'], self)
            })
            info_log.info('init station: {} -- success!'.format(station['stationid']))

    def station_start(self):
        for station in self.station_dict.values():
            # print(station)
            asyncio.run_coroutine_threadsafe(station.start(), self.loop)
            info_log.info('station data preprocessing: {} -- started!'.format(station.station_id))

    async def init(self):
        """
        初始化函数，包括数据库对象，初始化站点，初始化阈值监听
        :return:
        """
        await init_db_pool(self.loop)
        await self.init_station()
        asyncio.run_coroutine_threadsafe(self.listen_change_pd(), self.loop)
        self.station_start()

    async def listen_change_pd(self):
        """
        阈值监听修改
        :return:
        """
        # 监听通道
        info_log.info('Start listen pd cmd')
        msg = await AioRedisOP().subscribe('change_pd_warnningvalue')
        await msg.wait_message()
        try:
            async for item in msg.iter():
                cmd_data = loads(item)
                for station in self.station_dict.values():
                    # 等待所有站点响应数据
                    asyncio.run_coroutine_threadsafe(station.send_cmd(cmd_data), self.loop)
                    # await station.send_cmd(cmd_data)
                info_log.info('change pd successful')
        except Exception as e:
            # print(e)
            info_log.error('Send change PD cmd failed, error：{}'.format(e))

    async def stop_main_loop(self):
        """
        停止主循环，回调函数
        :return:
        """
        await asyncio.sleep(5)
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.stop()

    def run(self):
        """
        主运行函数
        :return:
        """
        logging.config.dictConfig(LOGGING_CONFIG_LOCAL)
        try:
            self.loop.run_until_complete(self.init())
            self.loop.run_forever()
        except KeyboardInterrupt:
            # 5s后停止主线程loop
            asyncio.run_coroutine_threadsafe(self.stop_main_loop(), self.loop)
            # self._loop.run_forever()
        # 关闭主循环
        self.loop.close()
