# -*- coding: utf-8 -*- 
# @Time : 2019/6/10 10:26 
# @Author :  
# @Site :  
# @File : Model.py 
# @Software: PyCharm
from enum import Enum

from DBPools.mysqlpool import AioMysqlOP


class UseSQL(Enum):
    insert_raw = r"""insert into tb_rawdata (EquipmentID,SensorID,Datatime,Content, warningvalue) value (%s,%s,%s,%s, %s);"""
    insert_alarm = '''insert into tb_pdalert(
                        EquipmentID,
                        SensorID,
                        Datatime,
                        AlmLev,
                        DschType,
                        AppPaDsch,
                        AcuPaDsch,
                        AvDsch,
                        MaxDsch,
                        DschCnt,
                        PriHarRte,
                        SecHarRte,
                        SmpProd,
                        Content,
                        warningvalue) value 
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                        '''
    insert_alarm_mes = r"""insert into tb_alarm (equipmentid, sensorid, alarmtime, alarmtype, comfirm, alarmdiscription)
                          value (%s,%s,%s,%s,%s,%s);"""
    select_device = r"""select stationid, ip, port from tb_station;"""
    select_sensorid_sql = r"""select SensorID,EquipmentID,Sensornumber,WarningValue from tb_sensor where EquipmentID='{}' and Sensornumber='{}';"""
    select_board = r"""select equipmentid from tb_device where stationid='{}';"""
    is_select = r"""select isselect, warningvalue from tb_sensor where equipmentid={} and sensornumber = {};"""
    get_savetime = r"""select argdata from tb_arg where equipmentid='-1' and sensorid ='-1' and argname='savetime';"""
    get_sensor_name = r"""select sn from tb_sensor where sensorid = {};"""


class Model_OP(object):

    async def get_savetime(self):
        return await AioMysqlOP().query(UseSQL.get_savetime.value)

    async def get_is_select(self, deviceid, sensornumber):
        return await AioMysqlOP().query(UseSQL.is_select.value.format(deviceid, sensornumber))

    async def get_all_station(self):
        """
        ????????????????????????
        """
        return await AioMysqlOP().query(UseSQL.select_device.value)

    async def get_sensor_name(self, sensorid):
        return await AioMysqlOP().query(UseSQL.get_sensor_name.value.format(sensorid))

    async def get_all_device(self, station_id):
        """
        ??????????????????????????????????????????
        :param station_id: ??????????????????
        :return:
        """
        return await AioMysqlOP().query(UseSQL.select_board.value.format(station_id))

    async def get_sensorid(self, device_id, number):
        """
        ???????????? ID
        :param device_id: ??????ID
        :param number: ????????????
        :return:
        """
        return await AioMysqlOP().query(UseSQL.select_sensorid_sql.value.format(device_id, number))

    async def insert_raw(self, data_list):
        """
        ??????????????????
        :param data_list:????????????????????????????????????
        :return:
        """
        if data_list:
            insert_sql = UseSQL.insert_raw.value
            await AioMysqlOP().insert(insert_sql, data_list)
            # print('insert raw success')

    async def insert_pdalert(self, data_list):
        """
        ??????????????????
        :param data_list: ????????????????????????????????????
        :return:
        """
        if data_list:
            insert_sql = UseSQL.insert_alarm.value
            await AioMysqlOP().insert(insert_sql, data_list)
            print('insert alarm success')

    async def insert_alarm_info(self, info_list):
        if info_list:
            info_sql = UseSQL.insert_alarm_mes.value
            await AioMysqlOP().insert(info_sql, info_list)
