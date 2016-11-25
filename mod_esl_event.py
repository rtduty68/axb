#coding=utf-8

import logging

def process(con,  event):
    logger = logging.getLogger("ESLEvent")
    #logger.debug(event.serialize("json"))
    
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
        client_socket.send_pack(request)
    
    elif msgType == "SERVER_DISCONNECTED":
        pass
    
    elif msgType == "HEARTBEAT":
        pass
                
    return msgType