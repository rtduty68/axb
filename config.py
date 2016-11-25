#coding=utf-8
'''系统参数配置'''
''' FS dialplan 参考配置
<extension name="esl_inbound">
    <condition field="destination_number" expression="^95013\d{0,12}$">
        <action application="set" data="servicekey=95013service"/>
        <action application="set" data="park_timeout=30"/>
        <action application="park" data=""/>
    </condition>
</extension>
'''
# 系统日志文件名
path_log = "./"
# 接口服务器地址
server_interface = ("/tmp/httpc_freeswitch")        #unixsock模式
#server_interface = ("127.0.0.1", 1234)                    #tcp/ip模式
# FS ESL 配置
server_esl = ("127.0.0.1",  8021, "ClueCon" )
#server_esl = ("192.168.1.230",  8021, "Pbx740123" )
service_key = "95013service"    #需与dialplan中servicekey一致