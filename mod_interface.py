#coding=utf-8
import asyncore,asynchat,socket
import logging
import marshal
import struct
from time import sleep

# socket接口，ESL模块调用其xxx方法发送数据给httpclient进程，根据该进程返回数据执行后续操作
class SocketClient(asynchat.async_chat):
    # 默认值4096，下列值是随便定的
    ac_in_buffer_size = 65535
    ac_out_buffer_size = 65535
    
    def __init__(self, address):
        asynchat.async_chat.__init__(self)
        self._logger = logging.getLogger('SocketClient')
        self._address = address
        self._len_header = 8
        #self._received_data = []
        self.connect_socketserver()
        
    def handle_connect(self):
        self._logger.info('handle_connect()')
        self._received_data = []
        # so set a length-based terminator
        self.set_terminator(self._len_header)
        self._process_data = self._process_header
        
    def collect_incoming_data(self, data):
        """Read an incoming message from the client
        and add it to the outgoing queue.
        """
        self._logger.debug('collect_incoming_data() -> (%d) %r',len(data), data)
        self._received_data.append(data)
        
    def found_terminator(self):
        """The end of a head or body has been seen."""
        self._logger.debug('found_terminator()')
        self._process_data()
    
    def handle_close(self):
        self._logger.info('handle_close()')
        self.close()
        self.connect_socketserver()
    
    ''' 未调试好如何使用，先自行在需要的地方用try方式捕获错误
    def handle_error(self):
        self._logger.info('handle_error()')
    '''
        
    def start(self):
        asyncore.loop()
    
    def connect_socketserver(self):
        if len(self._address) == 2:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while True:
            self._logger.info('connecting to %s', self._address)
            try:
                self.connect(self._address)
                return
            except Exception,e:
                self._logger.error("connect_socketserver() error. %r%r", Exception, e)
                sleep(1)
        
    def send_pack(self,params):
        try:
            s = marshal.dumps(params)
            self.push(struct.pack('!LLB', len(s), 0, 1) + s)
        except Exception,e:
            self._logger.error("send_pack() error. %r%r", Exception, e)
            # 尝试断开重连，可能需要根据异常情况修改处理方式
            self.close()
            self.connect_socketserver()
        
    def _process_header(self):
        msg_header = ''.join(self._received_data)
        self._logger.debug('_process_header() %r', msg_header)
        expected_data_len, seqno = struct.unpack('!LL',msg_header)
        if expected_data_len > 0 :
            #self.set_terminator(0) # set_terminator(0)估计是等字符串结束符\0
            self.set_terminator(expected_data_len)
            self._process_data = self._process_body
            self._received_data = []
        else:
            # 包头中包体长度非法，应该断开重连
            self._logger.error('_process_header() package len(%s) error.', expected_data_len)
            self.close()
            self.connect_socketserver()
            
    def _process_body(self):
        msg_body = ''.join(self._received_data)
        self._logger.debug('_process_body() %r',msg_body)
        self._process_response(marshal.loads(msg_body))
        self.set_terminator(self._len_header)
        self._process_data = self._process_header
        self._received_data = []
        
    def _process_response(self,pack):
        #self._logger.debug('_process_response() %r',pack)
        from FSasPaaS  import client_esl
        client_esl.process_request(pack)
        pass