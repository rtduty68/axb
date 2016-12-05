#coding=utf-8
'''
处理接收到的ESL事件
'''
import logging

logger = logging.getLogger("ESLEvent")

def process(con,  event):
    #logger.debug(event.serialize())
    
    from global_var import client_socket
    
    uuid = event.getHeader("unique-id")
    msgType = event.getType()
    
    if msgType == "CHANNEL_PARK":
        request = {
            'platform_key':'TZ01_95013',
            'uuid':uuid,
           'call_id': event.getHeader("variable_sip_call_id"),
           'no_x': event.getHeader("variable_sip_to_user"),
           'call_out_no':event.getHeader("variable_sip_from_user")}
        #发送给接口服务器
        client_socket.send_pack(request)
    
    elif msgType == "SERVER_DISCONNECTED":
        pass
    
    elif msgType == "HEARTBEAT":
        pass
    
    elif msgType == "CHANNEL_HANGUP_COMPLETE":
        logger.debug(event.serialize())
        
    return msgType