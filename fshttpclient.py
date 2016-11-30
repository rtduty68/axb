# -*- coding: utf-8 -*-
#from __future__ import print_function
import os, marshal
from gevent.server import StreamServer
from gevent import socket as gsocket
import gevent.pool
import gevent, traceback, struct
#from config import gserver as config
from geventhttpclient import HTTPClient
from geventhttpclient.url import URL
from geventhttpclient import connectionpool
#connectionpool. DEFAULT_CONNECTION_TIMEOUT = 10.0
#connectionpool.DEFAULT_NETWORK_TIMEOUT = 10.0
import logging, logging.handlers
import json, socket, hashlib, time
from ssl import _DEFAULT_CIPHERS
g_appkey, g_secret = '1023442457', 'sandbox750a140e5a971bcb193efa0ee'
#g_appkey, g_secret = '23442457', 'cb98691750a140e5a971bcb193efa0ee'
'''
定义一些系统变量
'''

SYSTEM_GENERATE_VERSION = "taobao-sdk-python-20160826"

P_APPKEY = "app_key"
P_API = "method"
P_SESSION = "session"
P_ACCESS_TOKEN = "access_token"
P_VERSION = "v"
P_FORMAT = "format"
P_TIMESTAMP = "timestamp"
P_SIGN = "sign"
P_SIGN_METHOD = "sign_method"
P_PARTNER_ID = "partner_id"

P_CODE = 'code'
P_SUB_CODE = 'sub_code'
P_MSG = 'msg'
P_SUB_MSG = 'sub_msg'
N_REST = '/router/rest'

def sign(secret, parameters):
    #===========================================================================
    # '''签名方法
    # @param secret: 签名需要的密钥
    # @param parameters: 支持字典和string两种
    # '''
    #===========================================================================
    # 如果parameters 是字典类的话
    if hasattr(parameters, "items"):
        keys = parameters.keys()
        keys.sort()

        parameters = "%s%s%s" % (secret,
            str().join('%s%s' % (key, parameters[key]) for key in keys),
            secret)
    sign = hashlib.md5(parameters).hexdigest().upper()
    return sign
LOGFILE = None #'crhttpclient.log'
thandler = (logging.StreamHandler() if not LOGFILE else
    logging.handlers.TimedRotatingFileHandler(LOGFILE))
fmt = logging.Formatter("%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s")
logger = logging.getLogger('MAIN')
logger.setLevel(logging.DEBUG)
logger.addHandler(thandler)
thandler.setFormatter(fmt)
# go to http://developers.facebook.com/tools/explorer and copy the access token
#TOKEN = '<go to http://developers.facebook.com/tools/explorer and copy the access token>'
# this handler will be run for each incoming connection in a dedicated greenlet
LENGTH_STATE =1
CONTENT_STATE=2
HEADER_LENGTH=9
#url = URL("http://192.168.107.163:8001/")
#url = URL("http://gw.api.tbsandbox.com:80/")
ssl_options={'ciphers': _DEFAULT_CIPHERS,'ca_certs': None, 'cert_reqs': gevent.ssl.CERT_NONE,}
url = URL("http://webrtcdemo-lubin.c9users.io")
http = HTTPClient.from_url(url, concurrency=60, network_timeout=5,
                connection_timeout=5,insecure=True, ssl_options=ssl_options)
conn_list = []

def process_input(client, inbuf, length, seqno, method):
    logger.debug("receive msg %r, len=%s, length=%s", inbuf, len(inbuf), length)
    """hash1 = {
        'v':'1.0', 'method':'add_call_record',
        'timestamp':'2014-08-18 2016:59:11', #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'app_key':'abc',
        #sign=BA9854BED1A2986B061E2713F403C752
        'phone_no':'18600000000', 'secret_no':'17000000000',
        'call_type':'1', 'peer_no':'13900000000','call_id':'1919',
        'call_time':'2014-08-18 2016:59:11',
    }"""
    global total
    total+=1
    req = marshal.loads(inbuf)
    logger.info('req=%s', req)
    pool.spawn(process_response, client, req, seqno, method)
    #client.sendall(struct.pack('!L', len(inbuf))+inbuf)

total,total_ack,stat_count, err=0,0,0,0
def echo(client, address):
    #print type(address), dir(address)
    logger.info('New connection from %s', address)
    #---------- client.sendall(struct.pack("!LL", 0, 1))
    #socket.sendall(b'Welcome to the echo server! Type quit to exit.\r\n')
    # using a makefile because we want to use readline()
    #rfileobj = client.makefile(mode='rb', bufsize=1)
    recvstate = LENGTH_STATE
    current_length = HEADER_LENGTH
    in_buffer = ''
    conn_list.append(client)
    #client.timeout = 0.1
    #client.setblocking(0)
    #print 'client:', dir(client)
    #print 'makefile:', dir(rfileobj)
    while True:
        #wait_read(rfileobj.fileno(), timeout=0.0)
        data = client.recv(16384)
        #print 'data=%r'% data
        if not data:
            logger.info("client no data")
            #rfileobj.close()
            #client.close()
            try:
                conn_list.remove(client)
            except:
                logger.info(traceback.format_exc())
            break
        in_buffer += data
        #logger.debug("msg= %r", data)
        while 1:
            if len(in_buffer)< current_length: break
            #if line.strip().lower() == b'quit':
            #    print("client quit")
            #socket.sendall(line)
            if recvstate == LENGTH_STATE:
                length, seqno, method = struct.unpack('!LLB',in_buffer[:current_length])
                if length == 0 and seqno == 1:
                    logger.info('cid %s register', method)
                    conn_list.append(client)
                    client.sendall(struct.pack("!LL",0,1))
                    in_buffer = in_buffer[current_length:]
                    recvstate = LENGTH_STATE
                    current_length = HEADER_LENGTH
                    continue
                if length > 10240:
                    logger.critical('packet length %d exceed limit',length)
                    try:
                        conn_list.remove(client)
                    except:
                        logger.info(traceback.format_exc())
                    client.close()
                    return
                in_buffer = in_buffer[current_length:]
                current_length = length
                recvstate = CONTENT_STATE
                #logger.debug('data length=%d',self.current_length)
                continue
            #process_input(client, in_buffer[:current_length], current_length)
            process_input(client, in_buffer[:current_length], current_length, seqno, method)
            in_buffer = in_buffer[current_length:]
            recvstate = LENGTH_STATE
            current_length = HEADER_LENGTH
    client.close()

def stat():
    global stat_count
    if stat_count>=1:
        logger.info('total,total_ack,stat_count,err=%d,%d,%d,%d', total,total_ack,stat_count,err)
        stat_count = 0
    gevent.sleep(10)
    gevent.spawn(stat)
    #if total_ack+err<TOTAL:
    #    p = gevent.spawn(stat)
    #else:
    #    logger.info('total,total_ack,stat_count,err=%d,%d,%d,%d', total,total_ack,stat_count,err)
gevent.spawn(stat)
pool = gevent.pool.Pool(120)
REQ_SEQNO = 2
# this handler will be run for each incoming connection in a dedicated greenlet
method_hash = {1: 'alibaba.aliqin.secret.call.control',
               2: 'alibaba.aliqin.secret.call.release',}
def process_response(client, req, seqno, method):
    global total_ack,stat_count, err
    sign_parameters = {
            P_FORMAT: 'json',
            P_APPKEY: g_appkey,
            P_SIGN_METHOD: "md5",
            P_VERSION: '2.0',
            P_TIMESTAMP: str(long(time.time() * 1000)),
            P_PARTNER_ID: SYSTEM_GENERATE_VERSION,
            P_API: method_hash[method],
        }
    try:
        uuid = req['uuid']
        del req['uuid']
    except KeyError:
        uuid = None
    if method == 2:
        if req['start_time'] == '': req['start_time'] = req['release_time']
    sign_parameters.update(req)
    sign_parameters[P_SIGN] = sign(g_secret, sign_parameters)
    params_url = URL(N_REST)
    params_url.query = sign_parameters
    try:
        logger.info('http get %s', params_url.request_uri)
        response = http.get(params_url.request_uri)
        data = response.read()
        logger.info('response data=%s', data)
        total_ack+=1
        stat_count+=1
        assert response.status_code == 200
        hash1 = json.loads(data)
    except socket.timeout:
        logger.error('response timeout')
        hash1 = {'error_response':None}
        err+=1
    except: #timeout:
        logger.error(traceback.format_exc())
        #data = {'err', traceback.format_exc()}
        hash1 = {'error_response':None}
        err+=1
    #logger.debug('data=%s, client=%s, conn_list=%s', data, client, conn_list)
    #data = marshal.dumps(data)
    if method == 2: return
    if 'error_response' in hash1:
        data = {} #{'call_in_no':None}
    else:
        try:
            data = hash1['alibaba_aliqin_secret_call_control_response']
            try:
                play_code = data['play_code']
            except KeyError:
                play_code = None
            data['play_code'] = play_code
        except KeyError:
            logger.error(traceback.format_exc())
            data = {} #{'call_in_no': None}
    if uuid: data['uuid'] = uuid
    data = marshal.dumps(data)
    if client in conn_list:
        client.sendall(struct.pack('!LL', len(data), seqno) + data)
    elif conn_list:
        n = len(conn_list)
        conn_list[hash(seqno) % n].sendall(struct.pack('!LL', len(data), seqno) + data)
    else:
        logger.error("No client connection!")
if __name__ == '__main__':
    # to make the server use SSL, pass certfile and keyfile arguments to the constructor
    #server = StreamServer(('0.0.0.0', 16000), echo)
    # to start the server asynchronously, use its start() method;
    # we use blocking serve_forever() here because we have no other jobs
    listener = gsocket.socket(gsocket.AF_UNIX, gsocket.SOCK_STREAM)
    sockname = '/tmp/httpc_freeswitch' #+ os.path.basename(__file__) + '.sock'
    if os.path.exists(sockname):
        os.remove(sockname)
    listener.bind(sockname)
    listener.listen(1)
    #WSGIServer(listener, application).serve_forever()
    logger.info('Starting cr server on %s', sockname)
    #server = StreamServer('/tmp/gevent.sock', echo)
    server = StreamServer(listener, echo)
    server.serve_forever()
