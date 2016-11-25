# -*- coding: utf-8 -*-
import socket, struct, re
from twisted.internet import reactor, defer
from twisted.web import resource,static,server, http
from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory, ClientFactory, DatagramProtocol
from twisted.protocols import basic
import traceback, time,threading
import marshal,sys,base64
import logging, logging.handlers
import os, json, sign3
import sys
WORK_DIR = '/work/smsbill201104'
sys.path.insert(0, WORK_DIR)

from subprocess import Popen
os.environ["PATH"] = "/usr/kerberos/sbin:/usr/kerberos/bin:/usr/local/bin:/usr/local/sbin:/sbin:/bin:/usr/sbin:/usr/bin:/usr/X11R6/bin"
#os.environ["LD_LIBRARY_PATH"]="/usr/local/lib:/mnt2/oracle/instantclient_11_2:/usr/local/BerkeleyDB.5.1/lib"
os.environ["LD_LIBRARY_PATH"]="/usr/local/lib:/home/smsbill_install/instantclient_11_2:/usr/local/BerkeleyDB.5.1/lib"
main_directory = WORK_DIR
globalserver_directory =  os.path.join(WORK_DIR,"globalserver")
program_hash = {}
proc_hash = {}
python = "/usr/local/bin/python"
program_hash["gdisp"] = [globalserver_directory, python, "gdisp.py"]
program_hash["gaaa"] = [globalserver_directory, python, "gaaa.py"]
program_hash["disp"] = [main_directory, python, "dispatcher.py"]
program_hash["aaa"] = [main_directory, python, "aaaserver.py"]
program_hash["oradisp"] = [main_directory, python, "oradisp.py"]
program_hash["getuser"] = [main_directory, python, "dbgetuser.py"]
program_hash["syncbill"] = [main_directory, python, "dbsyncbill.py"]
program_hash["synclist"] = [main_directory, python, "dbsynclist.py"]
def start_processes():
    logger.info('start processes')
    for name in program_hash.keys():
        list1 = program_hash[name]
        if name not in proc_hash:
            proc_hash[name] = Popen(list1[1:], cwd = list1[0])
    reactor.callLater(3, check_processes)
def start_process(name):
    logger.info('start process %s', name)
    list1 = program_hash[name]
    proc_hash[name] = Popen(list1[1:], cwd = list1[0])
def check_processes():
    for name in proc_hash.keys():
        p = proc_hash[name]
        if p.poll() is not None:
            list1 = program_hash[name]
            proc_hash[name] = Popen(list1[1:], cwd = list1[0])
    reactor.callLater(3, check_processes)
adminobj_hash = {}
g_adminclient = None
def main():
    global thandler, logger,dblogger
    #thandler = logging.StreamHandler()
    thandler = logging.handlers.TimedRotatingFileHandler('webserver.log')
    fmt = logging.Formatter("%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s")
    logger = logging.getLogger('MAIN')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(thandler)
    thandler.setFormatter(fmt)
    #f = protocol.ServerFactory()
    #f.protocol = AdminProtocol
    #reactor.listenTCP(6600,f)
    reactor.listenTCP(8000+int(progname), MyHttpFactory())
    #reactor.listenUDP(6611, Echo())
    #reactor.connectTCP(AAA_SERVER[0], AAA_SERVER[1], ChatFactory(myapp))
    #reactor.connectUNIX(unix_file, AdminClientFactory(MyAdmin))
    #reactor.callLater(2, start_processes)
    reactor.run(installSignalHandlers=1)
    #app.MainLoop()
class Echo(DatagramProtocol):
    def datagramReceived(self, data, (host, port)):
        #print "received %r from %s:%d" % (data, host, port)
        logger.info("received %r from %s:%d", data, host, port)
        #self.transport.write(data, (host, port))
class AdminClientFactory(ClientFactory):
    def __init__(self, name):
        self.name = name
        self.protocol = PetProtocol

    def clientConnectionLost(self, transport, reason):
        logger.info("remote server connection lost, reason: %r" % reason)
        reactor.callLater(3, transport.connect)
        #reactor.stop()

    def clientConnectionFailed(self, transport, reason):
        logger.info("remote server connection failed, reason: %r" % reason)
        reactor.callLater(3, transport.connect)
class PetProtocol(protocol.Protocol):
    def __init__(self):
        pass
    LENGTH_STATE =1
    CONTENT_STATE=2
    HEADER_LENGTH=4
    in_buffer = ''
    def process_input(self, buf, length):
        logger.debug('%s response data length=%s',self.name, length)
        if g_adminclient:
            g_adminclient.push(struct.pack('!L16s',length+16,self.name)+buf)
    def dataReceived(self, data):
        if not data: return
        self.in_buffer+=data
        while 1:
            if len(self.in_buffer)<self.current_length: return
            if self.recvstate == self.LENGTH_STATE:
                length, = struct.unpack('!L',self.in_buffer[:self.current_length])
                self.in_buffer = self.in_buffer[self.current_length:]
                self.current_length = length
                self.recvstate = self.CONTENT_STATE
                logger.debug('data length=%d',self.current_length)
                continue
            #data = self.in_buffer[:self.current_length]
            self.process_input(self.in_buffer[:self.current_length], self.current_length)
            self.in_buffer = self.in_buffer[self.current_length:]
            self.recvstate = self.LENGTH_STATE
            self.current_length = self.HEADER_LENGTH
    def connectionMade(self):
        self.name = self.factory.name
        self.in_buffer=''
        self.recvstate=self.LENGTH_STATE
        self.current_length = self.HEADER_LENGTH
        adminobj_hash[self.name] = self
        logger.info('%s adminserver made!', self.name)
        s = marshal.dumps('%s admin port connect made!' % self.name)
        g_adminclient.push(struct.pack('!L16s',len(s)+16,'petconnect')+s)

    def push(self, buffer):
        self.transport.write(buffer)

class AdminProtocol(protocol.Protocol):
    def connectionMade(self):
        global g_adminclient
        g_adminclient = self
        logger.debug('adminclient=%s', g_adminclient)
        #pass #self.sendLine("Web checker console. Type 'help' for help.")

    LENGTH_STATE =1
    CONTENT_STATE=2
    HEADER_LENGTH=4
    in_buffer = ''
    recvstate=LENGTH_STATE
    current_length = HEADER_LENGTH
    def dataReceived(self, data):
        if not data: return
        self.in_buffer+=data
        while 1:
            if len(self.in_buffer)<self.current_length: return
            if self.recvstate == self.LENGTH_STATE:
                length, = struct.unpack('!L',self.in_buffer[:self.current_length])
                self.in_buffer = self.in_buffer[self.current_length:]
                self.current_length = length
                self.recvstate = self.CONTENT_STATE
                logger.debug('admin data length=%d',self.current_length)
                continue
            #data = self.in_buffer[:self.current_length]
            self.process_input(self.in_buffer[:self.current_length])
            self.in_buffer = self.in_buffer[self.current_length:]
            self.recvstate = self.LENGTH_STATE
            self.current_length = self.HEADER_LENGTH
    def push(self, buffer):
        self.transport.write(buffer)
    def process_input(self, buffer):
        logger.debug('buf=%r', buffer)
        if buffer == 'quit':
            self.do_quit()
        else:
            self.do_eval(buffer)
    def connectAdmin(self, name, unixfile):
        if name not in adminobj_hash:
            reactor.connectUNIX(unixfile, AdminClientFactory(name))
    def cmd(self, name, cmdstr):
        if name=='admin':
            res = eval(cmdstr)
            s = marshal.dumps(res)
            g_adminclient.push(struct.pack('!L16s',len(s)+16, name)+s)
            return
        adminobj_hash[name].push(struct.pack('!L',len(cmdstr))+cmdstr)
    def do_test(self):
        """help [command]: List commands, or show help on the given command"""
        s = 'test ok!'
        self.push(struct.pack('!L',len(s))+s)
    def do_quit(self):
        """quit: Quit this session"""
        s = 'Goodbye.'
        self.push(struct.pack('!L',len(s))+s)
        self.transport.loseConnection()
    def connect(self, name):
        #print name, g_name_hash[name]
        self.connectAdmin(name, g_name_hash[name])
    def do_eval(self, buf):
        s=marshal.loads(buf)
        logger.debug('buf=%s', s)
        #print dir(self)
        try:
            getattr(self,s[0])(*s[1:])
        except:
            s = marshal.dumps(traceback.format_exc())
            self.push(struct.pack('!L16s',len(s)+16, 'do_eval')+s)
    def do_shutdown(self):
        self.do_quit()
        reactor.stop()

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        #reactor.stop()
        g_adminclient =  None
from twisted.web import http
import os
def renderHomePage(request):
    #print request
    request.setHeader("Content-Type","text/plain")
    #request.write(open('admin/htdocs/main.html').read())
    request.write('192.168.245.131:6090')
    request.finish()
def handlePost(request):
    params = request.args
    #sign = params['sign'][0]
    #del params['sign']
    #asign=sign3.ali_sign_server(params)
    #newdata = request.content.getvalue()
    logger.info('req=%s',params)
    #syncreq=simplejson.loads(newdata)
    #sign=sign3.sign3(syncreq)
    request.setHeader("Content-Type","text/plain")
    '''if 'call_in_no' not in params:
    	res = """<response><module>true</module></response>"""
    else:
    	res = """<response><play_code>185</play_code><record>false</record><call_type>0</call_type><op_type>1</op_type>
	<call_out_no>15098122312</call_out_no> </response>"""
    request.write(res)
    request.finish()
    return'''
    if 'call_out_no' in params:
        res ={

        "alibaba_aliqin_secret_call_control_response":{
        "play_code":185,
        "record":'false',
        "call_type":0,
        "op_type":1,
        #"call_in_no":"8613811685435",
        "call_in_no":"13501180766",
        'display_code':'0',
            }
        }
    else:
        res= {
        "alibaba_aliqin_secret_platform_push_call_release_response":{
        "module":'true'
        }
        }
    request.write(json.dumps(res))
    #request.write(res)
    request.finish()
def handlePost_old(request):
    params = request.args
    sign = params['sign'][0]
    del params['sign']
    asign=sign3.ali_sign_server(params)
    #newdata = request.content.getvalue()
    logger.info('req=%s, sign=%s, asign=%s',params, sign, asign)
    #syncreq=simplejson.loads(newdata)
    #sign=sign3.sign3(syncreq)
    request.setHeader("Content-Type","text/plain")
    if sign != asign:
        request.write(json.dumps({"response":{"is_success":'false',"err_code":"400","err_msg":"呼叫类型不能为空！".decode('utf8')}}))
        request.finish()
        return
    if syncreq['timer']/1000 +MAX_TIMER < time.time():
        request.write(simplejson.dumps({'code':1, 'reason':'expire timer'}))
        request.finish()
        return
    try:
        reason = process_syncreq(syncreq)
        if len(reason) == 8:
            code = 0
        else:
            code, reason = reason
    except KeyError:
        #code, reason = 'err', traceback.format_exc()
        code, reason =  'err', traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
    if code == 0:
        resp ={'code':0, 'reason':'enter sync queue'}
        g_synclist.append(reason)
    else:
        resp={'code':1, 'reason':reason}
    #request.write(simplejson.dumps(resp))
    request.finish()
#from Cheetah.Template import Template
BASE_TEMPLATE_DIR = '/root/omni2011a/admin/htdocs/bill2'
#class TwistedCheetahTemplate(Template):
#	twrequest = None
def stylehandle(request):
    request.setHeader("Content-Type","text/css")
    request.write(open('admin/htdocs/bill/css/style2.css').read())
    request.finish()
def result_info(request,namespace={}):
    filename = os.path.join(BASE_TEMPLATE_DIR,request.path[1:]+'.html')
    request.setHeader("Content-Type","text/html")
    t = Template(file=filename, searchList=[namespace]).respond()
    #tmplt.twrequest = request
    request.write(t.encode('utf-8'))
    #print '%r' % t.encode('utf-8')
    request.finish()
def imageshandle(request):
    if request.path.endswith('.gif'):
        imgtype='gif'
    elif request.path.endswith('.png'):
        imgtype = 'png'
    else:
        imgtype = 'gif'
    request.setHeader("Content-Type","text/"+imgtype)
    request.write(open('admin/htdocs/bill'+request.path).read())
    request.finish()
def lefthandle(request):
    menu_list = [
    [('进程群管理','/spms2/spservice.py'),
        [("启动进程群","spservice_input"),
        ("重新启动进程","spservice_list"),
        ("进程状态","spservice_query")]],
    [("计费进程增减",""),
    [("增加一个计费进程","uploadfeeuser"),
    ("减少一个计费进程","blackupload"),
    ]],
    [("双进程群热备",""),
        [	("增加备份进程群", "user_query"),
            ("下线备份进程群","user_list"),
    ]],
    [("帐号管理",""),
            [
            ("帐号列表","feetask_list"),
            ("帐号删除","feetask_input")]],
    [("话单管理",""),
            [
            ("话单列表","kefu_list"),
            ("话单查询","kefu_input"),
            ]],
    [("计费协议测试",""),
        [
        ("Submit","kefu_list"),
        ("Report","kefu_input"),
        ("SENDFAIL",'smsendfail'),
        ('deliver', 'smdelive'),
        ('压力测试','presstest'),]],
    ]
    result_info(request,{'menu_list':menu_list})
req_total = 0
class FunctionHandledRequest(http.Request):
    pageHandlers={
        '/':renderHomePage,
        '/left': lefthandle,
        '/style.css':stylehandle,
        '/router/rest':handlePost,
    }
    def process(self):
        #self.setHeader("Content-Type","text/html")
        #print '------------',self.path
        global req_total
        req_total+=1
        if req_total % 1000 == 0:
            logger.info("name=%s,req_total = %s", progname, req_total)
        #time.sleep(0.049)
        if self.pageHandlers.has_key(self.path):
            handler=self.pageHandlers[self.path]
            handler(self)
        elif self.path.startswith('/images'):
            imageshandle(self)
        else:
            self.setHeader("Content-Type","text/html")
            self.setResponseCode(http.NOT_FOUND)
            self.write("<h1>Not Found</h1>Sorry, no such page.")
            self.finish()
class MyHttp(http.HTTPChannel):
    requestFactory=FunctionHandledRequest
class MyHttpFactory(http.HTTPFactory):
    protocol=MyHttp

if __name__ == "__main__":
    global progname
    progname = sys.argv[1]
    main()
