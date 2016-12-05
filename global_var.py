#coding=utf-8

from config import * 

import mod_log

'''接口实例初始化'''
from mod_interface import SocketClient
client_socket = SocketClient(server_interface)

'''ESL实例初始化'''
#创建ESLClient
from mod_esl import ESLClient
client_esl = ESLClient(server_esl, service_key)

'''监视线程初始化'''
#创建ESL接收数据线程
from mod_monitor import Monitor
monitor = Monitor(client_esl, client_socket)
