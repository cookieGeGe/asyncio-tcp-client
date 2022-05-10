# -*- coding: utf-8 -*- 
# @Time : 2019/6/3 14:52 
# @Author :  
# @Site :  
# @File : Config.py 
# @Software: PyCharm
import aiomysql


class MysqlInfo:
    host = '127.0.0.1'
    # host = '192.168.230.128'
    port = 3306
    user = 'root'
    password = 'admin123'
    minsize = 5
    maxsize = 30
    db = 'pdms'
    charset = 'utf8'
    cursorclass = aiomysql.DictCursor
    loop = None

    @classmethod
    def set_loop(cls, loop):
        cls.loop = loop


class RedisInfo:
    host = '127.0.0.1'
    # host = '192.168.230.128'
    password = 'admin123'
    port = 6379
    db = 0
    encode = 'utf8'
    minsize = 5
    maxsize = 30
    encoding = 'utf8'
    loop = None

    @classmethod
    def set_loop(cls, loop):
        cls.loop = loop
