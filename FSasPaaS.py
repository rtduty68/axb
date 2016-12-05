#coding=utf-8

#from global_var import *
from global_var import client_socket
from global_var import client_esl
from global_var import monitor
       
def main():
    monitor.setDaemon(True)
    monitor.start()
    
    client_esl.setDaemon(True)
    client_esl.start()
    client_socket.start()   #本操作是阻塞的
    
if __name__=="__main__":
    main()