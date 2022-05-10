# -*- coding: utf-8 -*- 
# @Time : 2019/7/18 9:15 
# @Author :  
# @Site :  
# @File : DataProcessing.py 
# @Software: PyCharm

class StationDataPro(object):

    def __init__(self):
        self.protocol = {'header': b'\xe0\xe9\xe0\xe9', 'tail': b'', 'length': 3271}

    def is_legal(self, data):
        """
        判断数据是否符合协议要求
        :param data:读取的缓存数据
        :return:    -1 表示没有找到包头
                    -2 表示存在包头，但是长度小于3271
        """
        header_index = data.find(self.protocol.get('header'))
        if header_index == -1:
            return -1
        if len(data[header_index:]) < self.protocol.get('length'):
            return -2
        return 1

    def data_split(self, data):
        """
        切片一包数据和缓存数据
        :param data:
        :return:
        """
        header_index = data.find(self.protocol.get('header'))
        return data[header_index:header_index + 3271], data[header_index + 3271:]
