#coding=utf-8
'''
监视线程
监视ESLconnection是否正常连接
'''
import threading
import logging
import time

class Monitor(threading.Thread):
    def __init__(self, client_esl,client_socket):  
        threading.Thread.__init__(self)
        self._client_esl = client_esl
        self._client_socket = client_socket
        self._logger = logging.getLogger('Monitor')
        
    def run(self):
        # 每间隔一段时间检查self._client_esl的状态
        while True:
            self._logger.debug("run() enter wait")
            ret = self._client_esl.event_disconnected.wait(timeout=10) # ESL的HEARTBEAT间隔是20s
            self._logger.debug("run() exit wait")
            if ret == False:
                interval = time.time() - self._client_esl.last_msg_time
                if interval < 25: # ESL的HEARTBEAT间隔是20s
                    self._logger.info('Monitor check ESLconnection: still alive.')
                else:
                    self._client_esl.event_connected.clear()
                    self._client_esl.event_disconnected.set()
            else:
                self._logger.error('Monitor check ESLconnection: disconnected.')
                self._client_esl.event_connected.clear()
                self._client_esl.connect_eslserver("both")