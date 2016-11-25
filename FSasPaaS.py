#coding=utf-8

#from global_var import *
from global_var import client_socket
from global_var import client_esl
       
def main():
    
    client_esl.setDaemon(True)
    
    client_esl.start()
    client_socket.start()
   
if __name__=="__main__":
    main()