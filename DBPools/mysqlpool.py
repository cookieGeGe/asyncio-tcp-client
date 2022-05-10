# -*- coding: utf-8 -*- 
# @Time : 2019/6/3 14:51 
# @Author :  
# @Site :  
# @File : mysqlpool.py 
# @Software: PyCharm
from threading import Lock

import aiomysql


class AioMysqlOP(object):
    """
    mysql数据库连接池
    """
    _instance_lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(AioMysqlOP, "_instance"):
            with AioMysqlOP._instance_lock:
                if not hasattr(AioMysqlOP, "_instance"):
                    AioMysqlOP._instance = object.__new__(cls)
        return AioMysqlOP._instance

    def __init__(self):
        if hasattr(self, '_db_pool'):
            return
        self._db_pool = None

    async def create_pool(self, config=None):
        """
        初始化
        :param config:
        """
        if not config or not getattr(config, 'loop'):
            raise Exception('MySql连接池初始化失败')
        self._db_pool = await aiomysql.create_pool(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            minsize=config.minsize,
            maxsize=config.maxsize,
            db=config.db,
            loop=config.loop,
            charset=config.charset,
            cursorclass=config.cursorclass)

    def _get_pool(self):
        """
        获取连接池
        :return:
        """
        if not self._db_pool:
            raise Exception('MySql连接池未初始化')
        return self._db_pool

    async def query(self, sql_str, *args):
        """
        查询操作
        :param sql_str: sql语句
        :param args: 参数列表
        :return: 执行结果
        """
        with await self._get_pool() as conn:
            try:
                cur = await conn.cursor()
                await cur.execute(sql_str, *args)
                cur_fetchall = await cur.fetchall()
                await cur.close()
                conn.close()
                return cur_fetchall
            except Exception as e:
                print(e)

    async def insert(self, sql_str, *args):
        """
        插入操作
        :param sql_str: sql语句
        :param args: 参数列表
        :return: 执行结果
        """
        with await self._get_pool() as conn:
            try:
                cur = await conn.cursor()
                result = await cur.execute(sql_str, *args)
                await conn.commit()
                await cur.close()
                conn.close()
                return result
            except Exception as e:
                print(e)
