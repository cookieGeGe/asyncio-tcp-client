# -*- coding: utf-8 -*- 
# @Time : 2019/6/3 14:50 
# @Author :  
# @Site :  
# @File : __init__.py.py 
# @Software: PyCharm


async def init_db_pool(loop):
    from .Config import MysqlInfo, RedisInfo
    from .mysqlpool import AioMysqlOP
    from .redispool import AioRedisOP
    MysqlInfo.set_loop(loop)
    RedisInfo.set_loop(loop)
    await AioRedisOP().create_pool(RedisInfo)
    await AioMysqlOP().create_pool(MysqlInfo)


__all__ = ['init_db_pool', ]
