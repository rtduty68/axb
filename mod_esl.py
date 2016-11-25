#coding=utf-8

import logging
import threading
import ESL
import mod_esl_event
from time import sleep

class ESLClient(threading.Thread):  
    def __init__(self, server_esl,service_key):  
        threading.Thread.__init__(self)
        self._host = server_esl[0]
        self._port = server_esl[1]
        self._password = server_esl[2]
        self._service_key = service_key
        self._logger = logging.getLogger('ESLClient')
        self.connect_eslserver("both")
        
    def connect_eslserver(self, mode):
        ''' 因recvEvent是阻塞的，此时若在同一个ESLconnection进行其他操作（如execute），
        会被在阻塞在recvEvent后执行，可以采用recvEventTimed代替或建立多个ESLconnection
        本项目采用建立两个连接的方式'''
        #建立recv连接
        if mode == "both" or mode == "recv":
            self._logger.info('esl(recv) connecting to %s:%s', self._host,self._port)
            self._con_recv = None   # 不知这中方法Python中是什么效果，观察下
            self._con_recv = ESL.ESLconnection(self._host,self._port,self._password)
            while True:
                if self._con_recv.connected():
                    self._logger.info('esl(recv) connected to %s:%s', self._host,self._port)
                    self._con_recv.filter("variable_servicekey", self._service_key)
                    self._con_recv.filter("Event-Name","SHUTDOWN")
                    self._con_recv.filter("Event-Name","HEARTBEAT")
                    self._con_recv.events("plain", "SHUTDOWN HEARTBEAT CHANNEL_PARK") # SERVER_DISCONNECTED事件不用设置也能收到
                    break
                else:
                    self._logger.warning('esl(recv) connect to %s:%s error.', self._host,self._port)
                    sleep(1)
                    self._logger.info('esl(recv) connecting to %s:%s', self._host,self._port)
                    self._con_recv = ESL.ESLconnection(self._host,self._port,self._password)
        #建立send连接
        if mode == "both" or mode == "send":
            self._logger.info('esl(send) connecting to %s:%s', self._host,self._port)
            self._con_send = None   # 不知这中方法Python中是什么效果，观察下
            self._con_send = ESL.ESLconnection(self._host,self._port,self._password)
            while True:
                if self._con_send.connected():
                    self._logger.info('esl(send) connected to %s:%s', self._host,self._port)
                    #self._con_send.events("plain", "") # 默认不接收任何事件，除了SERVER_DISCONNECTED
                    #self._con_send.setAsyncExecute("1")  # 注：对inbound socket 无效
                    break
                else:
                    self._logger.warning('esl(send) connect to %s:%s error.', self._host,self._port)
                    sleep(1)
                    self._logger.info('esl(send) connecting to %s:%s', self._host,self._port)
                    self._con_send = ESL.ESLconnection(self._host,self._port,self._password)

    def run(self):
        while True:
            while self._con_recv.connected():
                #eventRecv = self._con_recv.recvEventTimed(100);
                eventRecv = self._con_recv.recvEvent()
                if eventRecv:
                    ret = mod_esl_event.process(self._con_recv,  eventRecv)
                    if ret == "HEARTBEAT":
                        pass
            #从while退出说明_con_recv已经断开，因此_con_send也已断开，所以对_con_send一并重连
            '''注意，观察发现，如果不对_con_send执行一次recvEvent或send等读写操作的话
            此时_con_send.connected()仍返回1（连接状态）'''
            self._logger.error('esl disconnect to %s:%s error.', self._host,self._port)
            self.connect_eslserver("both")
            #self.connect_eslserver("recv")
            #self._con_send.disconnect()
            #self.connect_eslserver("send")

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
        ''' 关于ESL发送命令的总结（参见：https://freeswitch.org/confluence/display/FREESWITCH/Event+Socket+Library）
        1.execute("answer", None, self._uuid)等同与sendRecv("api uuid_answer " + self._uuid)，在socket通信层面是阻塞的，但并不等到所执行的api或application完成
        execute和sendRecv均直接返回event对象
        2.send方法是异步的，立即返回一个整数结果表示发送是否执行，具体结果要通过recvEvent获取socket返回的event对象
        3.上述方法返回的event对象中，"Event-Name":    "SOCKET_DATA","Content-Type":    "command/reply"，
        且返回的event只能通过调用execute或send方法的同一个ESLconnection来获取，其他ESLESLconnection无法接收到该消息
        4.关于API和Application关系，参见杜金房《FreeSWITCH权威指南》，举例来讲，answer是App，uuid_answer是API
        5.代码举例
        ret = self._con_send.send("api uuid_answer " + self._uuid)
        retEvent = self._con_send.recvEvent()
        retEvent = self._con_send.execute("answer", None, uuid)
        print retEvent.serialize("json")
        '''
        
        # 设置呼叫相关参数
        
        #设置是否路由媒体，bypass时无法用FS录音
        # self._con_send.execute("set", "bypass_media=true", uuid)
        
        # 设置自动挂断主叫。当channel被park后，需设置此参数才可实现leg b挂断时自动挂断leg a
        self._con_send.execute("set", "hangup_after_bridge=true", uuid)     #放在leg b的dialstring无效
        
        # 设置主叫侧在接续时的回铃，可以设置成特定频率，也可用音频文件
        #self._con_send.execute("set", "ringback=%(2000, 4000, 440.0, 480.0)", uuid)     #放在leg b的dialstring无效
        self._con_send.execute("set", "ringback=/usr/local/freeswitch/sounds/CONTINUE185.wav", uuid)    #放在leg b的dialstring无效
        
        # 设置是否立即播放ringback设定的音频
        '''请参见https://freeswitch.org/confluence/display/FREESWITCH/180+vs+183+vs+Early+Media'''
        #self._con_send.execute("set", "instant_ringback=true", uuid) #可以放在leg b的dial string中
        
        # 设置ignore_early_media：是否忽略leg b的early media
        '''当为false时，leg a一直听ringback直到leg b回180或183
        当为ring_ready时，忽略leg b的180，leg a一直听ringback直到leg b回183
        当为true时，忽略leg b的180和183，leg a一直听ringback直到leg b回200ok'''
        #self._con_send.execute("set", "ignore_early_media=ring_ready", uuid) #可以放在leg b的dial string中，默认值是false。 
        
        ''' 下面是hold和transfer_ringback的测试，可忽略
        #self._con_send.execute("set", "transfer_ringback=local_stream://moh", uuid)
        #self._con_send.execute("hold", "", uuid)
        '''
        
        # 启动录音
        if record == 'true' :#or 'false':
            self._con_send.execute("record_session", "/tmp/"+uuid+".wav", uuid)
        
        # 发pre_answer
        #self._con_send.execute("pre_answer", "", uuid) #测试不发也可以,只要设置了ringback，就会向主叫发183
        
        # 启动呼叫
        # 呼叫可以用originate，但相比bridge，在目前场景偏麻烦。用在双向呼中比较合适
        #self._con_send.execute("originate", "sofia/gateway/gw1/13811334545", uuid)
        self._con_send.execute("bridge", "{instant_ringback=true}sofia/gateway/gw1/"+call_in_no, uuid)
        #self._con_send.execute("bridge", "{instant_ringback=true}sofia/gateway/gw2/"+"8613811685434", uuid)
