#coding=utf-8
'''
调用esl的execute，api，bgapi，send，sendRecv等命令实现放音，呼叫等操作
'''
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
import logging

logger = logging.getLogger("ESLOperate")

#呼叫leg b并与leg a桥接
def bridge(con,  uuid,  caller, callee, ringback, record):
    try:
        # 设置呼叫相关参数
            
        #设置是否路由媒体，bypass时无法用FS录音
        # con.execute("set", "bypass_media=true", uuid)
        
        # 设置自动挂断主叫。当channel被park后，需设置此参数才可实现leg b挂断时自动挂断leg a
        #con.execute("set", "hangup_after_bridge=true", uuid)     #放在leg b的dialstring无效
        
        # 设置主叫侧在接续时的回铃，可以设置成特定频率，也可用音频文件
        #con.execute("set", "ringback=%(2000, 4000, 440.0, 480.0)", uuid)     #放在leg b的dialstring无效
        #con.execute("set", "ringback=/usr/local/freeswitch/sounds/CONTINUE185.wav", uuid)    #放在leg b的dialstring无效
        
        # 设置是否立即播放ringback设定的音频
        '''请参见https://freeswitch.org/confluence/display/FREESWITCH/180+vs+183+vs+Early+Media'''
        #con.execute("set", "instant_ringback=true", uuid) #可以放在leg b的dial string中
        
        # 设置ignore_early_media：是否忽略leg b的early media
        '''当为false时，leg a一直听ringback直到leg b回180或183
        当为ring_ready时，忽略leg b的180，leg a一直听ringback直到leg b回183
        当为true时，忽略leg b的180和183，leg a一直听ringback直到leg b回200ok'''
        #con.execute("set", "ignore_early_media=ring_ready", uuid) #可以放在leg b的dial string中，默认值是false。 
        
        ''' 下面是hold和transfer_ringback的测试，可忽略
        #self._con_send.execute("set", "transfer_ringback=local_stream://moh", uuid)
        #self._con_send.execute("hold", "", uuid)
        '''
        
        # 把所有的set放到一起
        # hangup_complete_with_xml=true的使用待研究 
        ret = con.execute("multiset", "hangup_after_bridge=true ringback=/usr/local/freeswitch/sounds/CONTINUE185.wav", uuid)  
        if ret  == None: #连接已断开
            return "disconnected"
        
        # 启动录音
        if record == 'true' :#or 'false':
            ret = con.execute("record_session", "/tmp/"+uuid+".wav", uuid)
            if ret  == None: #连接已断开
                return "disconnected"
        # 发pre_answer
        #con.execute("pre_answer", "", uuid) #测试不发也可以,只要设置了ringback，就会向主叫发183
        
        # 启动呼叫
        # 呼叫可以用originate，但相比bridge，在目前场景(leg a呼入)偏麻烦。用在双向呼中比较合适
        # 呼叫中的通道变量，参考https://freeswitch.org/confluence/display/FREESWITCH/Channel+Variables'''
        #con.execute("originate", "sofia/gateway/gw1/13811334545", uuid)
        #ret = con.execute("bridge", "{instant_ringback=true}sofia/gateway/gw1/"+callee, uuid)
        ret = con.execute("bridge", "{instant_ringback=true}[leg_timeout=8]sofia/external/"+callee+"@172.16.195.78:5060|sofia/external/13811334545@127.0.0.1:6060", uuid)
        if ret  == None: #连接已断开
            return "disconnected"
    except Exception,e:
            logger.error("bridge error. %r%r",Exception,e)
            return "error"
    
    return "success"