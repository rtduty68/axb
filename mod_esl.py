#coding=utf-8

import time
import logging
import threading
import ESL
import mod_esl_event
import mod_esl_operate

class ESLClient(threading.Thread):  
    def __init__(self, server_esl,service_key):  
        threading.Thread.__init__(self)
        self._host = server_esl[0]
        self._port = server_esl[1]
        self._password = server_esl[2]
        self._service_key = service_key
        self._logger = logging.getLogger('ESLClient')
        self._con_recv = None
        self._con_send = None
        self.last_msg_time = time.time()                         # 最后收到消息时间
        self.event_connected = threading.Event()    # 连接建立事件
        self.event_disconnected = threading.Event()    # 连接断开事件
        self.connect_eslserver("both")
        
    def connect_eslserver(self, mode):
        ''' 因recvEvent是阻塞的，此时若在同一个ESLconnection进行其他操作（如execute），
        会被在阻塞在recvEvent后执行，可以采用recvEventTimed代替或建立多个ESLconnection
        本项目采用建立两个连接的方式'''
        #建立recv连接
        if mode == "both" or mode == "recv":
            self._logger.info('esl(recv) connecting to %s:%s', self._host,self._port)
            if self._con_recv != None:
                self._con_recv.disconnect()
            self._con_recv = ESL.ESLconnection(self._host,self._port,self._password)
            while True:
                if self._con_recv.connected():
                    self._logger.info('esl(recv) connected to %s:%s', self._host,self._port)
                    self.last_msg_time = time.time() 
                    self._con_recv.filter("variable_servicekey", self._service_key)
                    self._con_recv.filter("Event-Name","SHUTDOWN")
                    self._con_recv.filter("Event-Name","HEARTBEAT")
                    self._con_recv.events("plain", "SHUTDOWN HEARTBEAT CHANNEL_PARK CHANNEL_HANGUP_COMPLETE") # SERVER_DISCONNECTED事件不用设置也能收到
                    break
                else:
                    self._logger.warning('esl(recv) connect to %s:%s error.', self._host,self._port)
                    time.sleep(1)
                    self._logger.info('esl(recv) connecting to %s:%s', self._host,self._port)
                    self._con_recv = ESL.ESLconnection(self._host,self._port,self._password)
        #建立send连接
        if mode == "both" or mode == "send":
            self._logger.info('esl(send) connecting to %s:%s', self._host,self._port)
            if self._con_send != None:
                self._con_send.disconnect()
            self._con_send = ESL.ESLconnection(self._host,self._port,self._password)
            while True:
                if self._con_send.connected():
                    self._logger.info('esl(send) connected to %s:%s', self._host,self._port)
                    #self._con_send.events("plain", "") # 默认不接收任何事件，除了SERVER_DISCONNECTED
                    #self._con_send.setAsyncExecute("1")  # 注：对inbound socket 无效
                    break
                else:
                    self._logger.warning('esl(send) connect to %s:%s error.', self._host,self._port)
                    time.sleep(1)
                    self._logger.info('esl(send) connecting to %s:%s', self._host,self._port)
                    self._con_send = ESL.ESLconnection(self._host,self._port,self._password)
        self.event_disconnected.clear()
        self.event_connected.set()
        
    def run(self):
        while True:
            while self._con_recv.connected():
                #eventRecv = self._con_recv.recvEventTimed(100);
                self._logger.debug("run() enter recvEvent")
                eventRecv = self._con_recv.recvEvent()
                self._logger.debug("run() exit recvEvent")
                if eventRecv:
                    ret = mod_esl_event.process(self._con_recv,  eventRecv)
                    '''处理连接心跳，只要是收到消息均认为连接存在，包括SHUTDOWN，SERVER_DISCONNECTED
                    因为即使在SHUTDOWN，SERVER_DISCONNECTED时将连接的心跳时间更新，
                    在判断connected（）也返回断开，不影响重连处理'''
                    self.last_msg_time = time.time()
                    
            #从while退出说明_con_recv已经断开，因此_con_send也已断开，所以对_con_send一并重连
            '''注意，观察发现，如果不对_con_send执行一次recvEvent或send等读写操作的话
            此时_con_send.connected()仍返回1（连接状态）,所以也无法根据该返回值判读是否需要重连'''
            #self._logger.error('esl disconnect to %s:%s.', self._host,self._port)
            self.event_disconnected.set()
            self.event_connected.clear()
            self._logger.debug("run() enter wait")
            self.event_connected.wait()
            self._logger.debug("run() exit wait")
    
    #此方法未用        
    def notify_monitor(self):
        ''''3.2之前版本python，Condition.wait()始终返回None，无法直接根据其返回值直接判断
        是超时结束还是被notify唤醒，所以统一用last_msg_time来判断是否需重连'''
        self.last_msg_time = 0.0                    #如上所述，将last_msg_time置为0.0，方便监视线程判断是否重连
        self.condition_connect.acquire()
        self.condition_connect.notify()   #通知监视线程进行重连，此方式不可行，因wait的有3个线程，并不一定确保能通知到监视线程。
        '''注意，notify_monitor方法可能在run()和process_request()中被调用，
        在run()中调用时，等待基本没有问题，但在process_request()中被调用时，
        等待可能回导致mod_interface接收缓冲区满，不等待的话，可能会多次通知监视线程重连'''
        self.condition_connect.wait()       #等待监视线程重连结束
        self.condition_connect.release()

    def process_request(self,pack): # 注，暂未处理self._con_send.execute等操作的异常
        # 解析请求参数
        try :
            uuid = pack[u'uuid'].encode('utf8')
            display_code = pack[u'display_code'].encode('utf8')
            call_in_no = pack[u'call_in_no'].encode('utf8')
            play_code = pack[u'play_code']
            record = pack[u'record'].encode('utf8')
            op_type = pack[u'op_type']
            call_type = pack[u'call_type']
        except Exception,e:
            self._logger.error("process_request parse param error. %r%r",Exception,e)
            return
        
        # 通过_con_send向FS发送命令
        if self.event_connected.is_set():   # 未采用阻塞等待，防止mod_interface的接收缓冲区满
            # 外呼命令
            ret = mod_esl_operate.bridge(self._con_send, uuid, "", call_in_no, play_code, record)
            if ret == "disconnected":   # 发现连接断开，重连。未想清楚是否回引起其他问题，所以并没有重发刚才执行失败的操作，
                self.event_disconnected.set()
                self.event_connected.clear()
