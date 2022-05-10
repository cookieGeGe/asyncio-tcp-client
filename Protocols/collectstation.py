# -*- coding: utf-8 -*- 
# @Time : 2019/7/17 15:12 
# @Author :  
# @Site :  
# @File : collectstation.py 
# @Software: PyCharm
import asyncio
import datetime
from json import loads, dumps

from struct import unpack, pack

import gc

from Connections.ConnectionBase import DataAnaClient
from DBPools.Model import Model_OP
from DBPools.redispool import AioRedisOP
from Protocols.DataProcessing import StationDataPro
from Protocols.ProtocolBase import AnalysisBase
from utils.feature_calc import discharge_type
from utils.dataana_util import bytes_to_data, time_to_datetime
from utils.services_log import info_log


class CollectionStation(AnalysisBase):
    """
    采集站点数据解析
    """

    def __init__(self, loop, socket, station_id, hander):
        super(CollectionStation, self).__init__(loop)
        self.loop = loop
        self.socket = socket
        self.station_id = station_id
        self.host = socket[0]
        self.port = socket[1]
        self.socket_obj = None
        self.save_time_list = {}
        self.save_15_one_time = {}
        self.max_pd_15 = {}
        self.is_select_sensor = {}
        self.warningvalue_dict = {}
        self.main_obj = hander
        self.save_time = 15

    async def init_socket(self):
        """
        初始化 socket 连接对象
        :return:
        """
        if self.socket_obj == None:
            self.socket_obj = DataAnaClient(self.loop, self)

    async def connect(self):
        """
        开始连接 socket
        断线重连重新调用，连接失败后每两秒重连一次
        :return:
        """
        try:
            await self.loop.create_connection(lambda: self.socket_obj, self.host, self.port)
            info_log.info('Connected station {} successful'.format(self.station_id))
        except Exception as e:
            info_log.error('Connected station {} failed, Waiting for reconnection!'.format(self.station_id))
            await asyncio.sleep(2)
            gc.collect()
            asyncio.run_coroutine_threadsafe(self.connect(), self.loop)

    async def reconnect(self):
        """
        断线重连，手动进行垃圾回收，
        :return:
        """
        if self.socket_obj.transport.is_closing():
            # print('开始重连')
            info_log.info('Reconnected station {} !'.format(self.station_id))
            new_collect = CollectionStation(self.loop, self.socket, self.station_id, self.main_obj)
            self.main_obj.station_dict[str(self.station_id)] = new_collect
            del self
            gc.collect()
            await new_collect.start()
        else:
            # print('reconnect success')
            info_log.error('Connect station {} successful!'.format(self.station_id))

    async def init_data(self):
        """
        初始化解析基础数据
        :return:
        """
        Device_list = await Model_OP().get_all_device(self.station_id)
        save_time_list = await Model_OP().get_savetime()
        if save_time_list:
            self.save_time = int(save_time_list[0]['argdata'])
        for i in Device_list:
            self.save_time_list[str(i['equipmentid'])] = []
            self.is_select_sensor[str(i['equipmentid'])] = [0] * 10
            self.warningvalue_dict[str(i['equipmentid'])] = [0] * 10
            for _ in range(10):
                sensor_type_list = [{'last_pd_time': datetime.datetime(2018, 1, 1, 0, 0, 0), 'now_times': 0} for i in
                                    range(9)]
                self.save_time_list[str(i['equipmentid'])].append(sensor_type_list)
                status = await Model_OP().get_is_select(i['equipmentid'], _ + 1)
                self.is_select_sensor[str(i['equipmentid'])][_] = int(status[0]['isselect'])
                self.warningvalue_dict[str(i['equipmentid'])][_] = int(status[0]['warningvalue'])
                self.max_pd_15[str(i['equipmentid'])] = [0] * 10
            now_time = datetime.datetime.now() - datetime.timedelta(minutes=int(self.save_time))
            self.save_15_one_time[str(i['equipmentid'])] = [
                {'save_time_interval': now_time.minute // int(self.save_time)} for _ in range(10)
            ]

    async def get_id_sensorid_dschtype(self, BoardCardNo, ChannelNo, pd_data):
        """
        获取通道ID，计算放电类型
        :param BoardCardNo: 板卡 ID
        :param ChannelNo: 通道编号
        :param pd_data: 实时告警PD数据
        :return:
        """
        sensor = await Model_OP().get_sensorid(BoardCardNo, ChannelNo)
        sensorid = sensor[0]['SensorID']
        WarningValue = sensor[0]['WarningValue']
        dschtype = await discharge_type(bytes_to_data(pd_data), WarningValue)
        return sensorid, dschtype
        # return sensorid, 1

    async def insert_pdalert(self, BoardCardNo, sensorid, real_time, pd_data, dschtype, warning):
        """
        mysql 中插入 PD 事件数据库
        :param BoardCardNo: 板卡 ID
        :param sensorid: 通道 ID
        :param real_time: 当前告警时间
        :param pd_data: pd 数据
        :param dschtype: 放电类型
        :return:
        """
        await Model_OP().insert_pdalert(
            [BoardCardNo, sensorid, real_time, 1, int(dschtype), 0, 0, 0, max(list(pd_data)), 0, 0, 0, 0, pd_data,
             warning])

    async def insert_alarm_info(self, BoardCardNo, sensorid, real_time, info):
        await Model_OP().insert_alarm_info([BoardCardNo, sensorid, real_time, 1004, 0, info])

    async def unpack_data(self, data):
        """
        解析数据
        计算峰值存 redis
        PD 数据立即存数据库15分钟同种放电类型存前 9 次
        :param data:
        :return:
        """
        pd_header = unpack('<4s2sbhibbbib', data[:21])
        if not data[6]:
            BoardCardNo = pd_header[4]
            ChannelNo = pd_header[5]
            PDFlag = pd_header[6]
            DataTime = pd_header[8]
            real_time = datetime.datetime.now()
            pd_data = data[21:]
            # print('package time:', real_time)
            try:
                await AioRedisOP().set('{}-{}'.format(BoardCardNo, ChannelNo), pd_data, 20)
                try:
                    self.max_pd_15[str(BoardCardNo)][ChannelNo - 1] = max(list(pd_data))
                except Exception as e:
                    # print(e)
                    info_log.error(
                        'BoardCard:{}, Sensor:{} Setting PD peak failure! error:{}'.format(BoardCardNo, ChannelNo - 1,
                                                                                           e))
                temp_max_pd_15 = await AioRedisOP().get('max_pd_15')
                if temp_max_pd_15 is not None:
                    temp = loads(temp_max_pd_15)
                    # print(self.max_pd_15)
                    temp.update(self.max_pd_15)
                else:
                    temp = self.max_pd_15
                await AioRedisOP().set('max_pd_15', dumps(temp))
                get_max_pd = max(pd_data)
                warningvalue = self.warningvalue_dict[str(BoardCardNo)][ChannelNo - 1]
                PDFlag = 1 if get_max_pd > warningvalue else 0
                print(PDFlag, warningvalue, BoardCardNo, ChannelNo - 1)
                if PDFlag:
                    if 0 <= ChannelNo <= 4:
                        print(BoardCardNo, ChannelNo)
                    if self.is_select_sensor[str(BoardCardNo)][ChannelNo - 1]:
                        print('push real_time_pd {}_{}'.format(BoardCardNo, ChannelNo))
                        await AioRedisOP().rpush('real_time_pd', '{}-{}'.format(BoardCardNo, ChannelNo))
                    sensorid, dschtype = await self.get_id_sensorid_dschtype(BoardCardNo, ChannelNo, pd_data)
                    save_pd = self.save_time_list[str(BoardCardNo)][ChannelNo - 1][int(dschtype)]
                    cha_time = real_time - save_pd['last_pd_time']
                    if cha_time.days > 0 or (cha_time.days == 0 and cha_time.seconds > 900):
                        if self.is_select_sensor[str(BoardCardNo)][ChannelNo - 1]:
                            # warningvalue = self.warningvalue_dict[str(BoardCardNo)][ChannelNo - 1]
                            # print('板卡:{} 通道：{} 阈值：{}'.format(BoardCardNo, ChannelNo - 1, warningvalue))
                            await self.insert_pdalert(BoardCardNo, sensorid, real_time, pd_data, dschtype, warningvalue)
                            await Model_OP().insert_raw([BoardCardNo, ChannelNo, real_time, pd_data, warningvalue])
                            sensor_name = await Model_OP().get_sensor_name(sensorid)
                            if sensor_name:
                                await self.insert_alarm_info(BoardCardNo, sensorid, real_time,
                                                             '{} 监测到疑似告警！'.format(sensor_name[0]['sn']))
                            save_pd['now_times'] = 1
                            save_pd['last_pd_time'] = real_time
                    elif cha_time.days < 0:
                        pass
                    else:
                        if save_pd['now_times'] < 9:
                            if self.is_select_sensor[str(BoardCardNo)][ChannelNo - 1]:
                                # warningvalue = self.warningvalue_dict[str(BoardCardNo)][ChannelNo - 1]
                                # print('板卡:{} 通道：{} 阈值：{}'.format(BoardCardNo, ChannelNo - 1, warningvalue))
                                await self.insert_pdalert(BoardCardNo, sensorid, real_time, pd_data, dschtype,
                                                          warningvalue)
                                await Model_OP().insert_raw([BoardCardNo, ChannelNo, real_time, pd_data, warningvalue])
                                sensor_name = await Model_OP().get_sensor_name(sensorid)
                                if sensor_name:
                                    await self.insert_alarm_info(BoardCardNo, sensorid, real_time,
                                                                 '{} 监测到疑似告警！'.format(sensor_name[0]['sn']))
                                save_pd['now_times'] += 1
                await AioRedisOP().set('AS_{}_{}'.format(BoardCardNo, ChannelNo - 1), PDFlag, 10)
                save_15_data_interval = self.save_15_one_time[str(BoardCardNo)][ChannelNo - 1]
                # print(self.save_15_one_time)
                if real_time.minute // self.save_time != save_15_data_interval['save_time_interval']:
                    warningvalue = self.warningvalue_dict[str(BoardCardNo)][ChannelNo - 1]
                    await Model_OP().insert_raw([BoardCardNo, ChannelNo, real_time, pd_data, warningvalue])
                    print('insert raw data succes!')
                    self.save_15_one_time[str(BoardCardNo)][ChannelNo - 1][
                        'save_time_interval'] = real_time.minute // int(self.save_time)
                    # print('当前：',save_15_data_interval['save_time_interval'])
                    # print('修改过后', self.save_15_one_time[str(BoardCardNo)][ChannelNo - 1]['save_time_interval'])
            except Exception as e:
                # print(e)
                info_log.error(
                    'BoardCard:{}, Sensor:{} Data parsing failed! error: {}'.format(BoardCardNo, ChannelNo - 1, e))

    async def send_cmd(self, change_dict):
        """
        发送修改 PD 阈值
        :param change_dict:
        :return:
        """
        ChannelNo = change_dict['ChannelNo']
        BoardCardNo = change_dict['BoardCardNo']
        PDThreshold = change_dict['PDThreshold']
        Head = b'\xe0\xe9\xe0\xe9'
        Cmd = b'\x00\x03'
        Other = b'\x00\x00\x00'
        BoardToPDThreshold = pack('<i20s20s20s20siBBB',
                                  BoardCardNo,  # 板卡号
                                  '255.255.255.255'.encode('utf-8'),  # IP
                                  '255.255.255.255'.encode('utf-8'),  # GateWay
                                  '255.255.255.255'.encode('utf-8'),  # Mask
                                  '255.255.255.255'.encode('utf-8'),  # ServerIP
                                  0,  # port
                                  1,  # 通道数
                                  ChannelNo,  # 通道号
                                  PDThreshold)  # PD阀值
        ChangeBuffer = Head + Cmd + Other + BoardToPDThreshold
        try_time = 1
        while try_time <= 3:
            try:
                self.socket_obj.transport.write(ChangeBuffer)
                if str(BoardCardNo) in self.warningvalue_dict.keys():
                    # print('修改板卡：{} 通道：{} 阈值：{}'.format(BoardCardNo, ChannelNo - 1, PDThreshold))
                    self.warningvalue_dict[str(BoardCardNo)][int(ChannelNo) - 1] = int(PDThreshold)
                print(ChangeBuffer)
                info_log.log('BoardCard:{}, Sensor:{} The threshold is modified to: {}'.format(BoardCardNo, ChannelNo,
                                                                                               PDThreshold))
                break
            except:
                try_time += 1
                await asyncio.sleep(0.5)

    async def start(self):
        """
        主程序连接对象初始化
        :return:
        """
        await self.init_data()
        await self.init_socket()
        await self.connect()

    async def read(self, rawdata):
        """
        从缓存读取数据，判断是否符合要求，符合要求就解析，不符合要求继续等待
        :param rawdata:
        :return:
        """
        legal_status = StationDataPro().is_legal(rawdata)
        while legal_status != 1:
            # print('开始准备处理接收数据')
            block = await self._read()
            # print('读取的长度：', len(block))
            if self._eof:
                break
            if block == b'':
                break
            rawdata += block
            legal_status = StationDataPro().is_legal(rawdata)
            if legal_status == -1:
                rawdata = b''
            if legal_status == -2:
                header_index = rawdata.find(StationDataPro().protocol.get('header'))
                rawdata = rawdata[header_index:]
            # await asyncio.sleep(0.1)
        else:
            # info_log.info('开始解析数据--------------')
            real_data, rawdata = StationDataPro().data_split(rawdata)
            # print(len(rawdata))
            self.socket_obj.unpack_data_task = self.unpack_data(real_data)
            asyncio.run_coroutine_threadsafe(self.socket_obj.unpack_data_task, self.loop)
            # await asyncio.sleep(0.1)
            self.socket_obj.read_task = self.read(rawdata)
            gc.collect()
            asyncio.run_coroutine_threadsafe(self.socket_obj.read_task, self.loop)
