yixin branch start 2
FSasPaaS.py 是我的esl的程序入扣
fshttpclient.py是罗博士跟我esl的接口。
其他都是我的esl相关的模块
FS<-->FSasPaaS.py<-->fshttpclient.py<-->阿里或测试用httpserver。
FS<-->FSasPaaS.py使用inbound的esl
FSasPaaS.py<-->fshttpclient.py是unixsocket或tcp/ip
是罗博士定义的私有协议。
fshttpclient.py跟阿里或其他server就是http协议了。目前用的是阿里小号提供的axb业务的协议。
webserver.py 测试用http server
