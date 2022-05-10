# -*- coding: utf-8 -*- 
# @Time : 2019/7/18 17:04 
# @Author :  
# @Site :  
# @File : services_log.py 
# @Software: PyCharm

# -*- coding: utf-8 -*-
import logging

import os

import sys

base_dir = os.path.dirname(os.path.abspath(__name__))
log_dir = os.path.join(base_dir, 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

print(log_dir)

LOGGING_CONFIG_LOCAL = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'root': {
            'qualname': 'root',
            'level': 'DEBUG',
            'handlers': ['debugs_console', 'debugs_file', ],
        },
        'info_log': {
            'qualname': 'info_log',
            'level': 'INFO',
            'handlers': ['info_log_console', 'info_log_file', ],
            "propagate": True,
        },
        'error_log': {
            'qualname': 'error_log',
            'level': 'ERROR',
            'handlers': ['error_log_console', 'error_log_file', ],
            "propagate": True,
        },
    },
    'handlers': {
        'debugs_console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',
            'formatter': 'debug_form',
            'stream': sys.stdout,
        },
        'debugs_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'debug_form',
            'filename': os.path.join(log_dir, 'pd_log_debug.log'),
            'mode': 'a',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 7,
            'encoding': 'utf8',
        },
        'info_log_console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'generic',
            'stream': sys.stdout,
        },
        'info_log_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'formatter': 'generic',
            'filename': os.path.join(log_dir,'pd_log_info.log'),
            'when': 'h',
            'interval': 10,
            'backupCount': 7,
            'encoding': 'utf8',
        },
        'error_log_console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'debug_form',
            'stream': sys.stderr,
        },
        'error_log_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'debug_form',
            'filename': os.path.join(log_dir,'pd_log_error.log'),
            'when': 'D',
            'interval': 30,
            'backupCount': 7,
            'encoding': 'utf8',
        },
    },
    'formatters': {
        'debug_form': {
            'format': '%(asctime)s %(name)s [%(filename)s %(module)s %(funcName)s line:%(lineno)d] [%(process)d-%(threadName)s-%(thread)d] [%(levelname)s] %(message)s',
            'datefmt': '[%Y-%m-%d %H:%M:%S %z]',
            'class': 'logging.Formatter',
        },
        'generic': {
            'format': '%(asctime)s %(relativeCreated)d %(name)s [%(process)d-%(threadName)s-%(thread)d] [%(levelname)s] %(message)s',
            'datefmt': '[%Y-%m-%d %H:%M:%S %z]',
            'class': 'logging.Formatter',
        },
    },
}

# 获取日志对象
root_log = logging.getLogger('root')
info_log = logging.getLogger('info_log')
error_log = logging.getLogger('error_log')
