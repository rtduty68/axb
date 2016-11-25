#coding=utf-8

from config import * 

''''''
import logging,logging.handlers
# 创建一个logger  
logger = logging.getLogger()
# 创建用于写入日志文件的handler
handler_file = logging.handlers.TimedRotatingFileHandler(path_log+"/fsaspaas.log") 
# 建用于输出到控制台的handler  
handler_stream = logging.StreamHandler()
# 定义handler的输出格式formatter  
formatter = logging.Formatter("'%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler_file.setFormatter(formatter)
handler_stream.setFormatter(formatter)

# 设置日志级别
logger.setLevel(logging.DEBUG)
# 给logger添加handler  
logger.addHandler(handler_file)
logger.addHandler(handler_stream)
