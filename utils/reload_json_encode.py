# -*- coding: utf-8 -*- 
# @Time : 2019/7/3 10:38 
# @Author :  
# @Site :  
# @File : reload_json_encode.py 
# @Software: PyCharm
import datetime
import json


class ReloadJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        super(ReloadJSONEncoder, self).default(obj)
