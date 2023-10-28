# -*- coding: utf-8 -*-

import logging
import inspect
import os

class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        current_function_name = inspect.currentframe().f_back.f_code.co_name
        current_file_name = os.path.basename(inspect.currentframe().f_back.f_code.co_filename)
        line_number = inspect.currentframe().f_back.f_lineno
        msg = f"({current_function_name} in {current_file_name}:{line_number}) {msg}"
        super().info(msg, *args, **kwargs)
        
    def warning(self, msg, *args, **kwargs):
        current_function_name = inspect.currentframe().f_back.f_code.co_name
        current_file_name = os.path.basename(inspect.currentframe().f_back.f_code.co_filename)
        line_number = inspect.currentframe().f_back.f_lineno
        msg = f"({current_function_name} in {current_file_name}:{line_number}) {msg}"
        super().warning(msg, *args, **kwargs)
        
    def error(self, msg, *args, **kwargs):
        current_function_name = inspect.currentframe().f_back.f_code.co_name
        current_file_name = os.path.basename(inspect.currentframe().f_back.f_code.co_filename)
        line_number = inspect.currentframe().f_back.f_lineno
        msg = f"({current_function_name} in {current_file_name}:{line_number}) {msg}"
        super().error(msg, *args, **kwargs)   

# 设置日志记录器的名称
_logger_nm = "xqfollower"

# 创建日志记录器，使用自定义的CustomLogger
logger = CustomLogger(_logger_nm)
logger.setLevel(logging.INFO)

# 定义日志格式
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s]: %(message)s"
)

# 创建日志文件处理器，以追加模式写入日志文件
handler = logging.FileHandler('%s.log' % _logger_nm, mode='a', encoding='utf-8')
handler.setFormatter(fmt)

# 将文件处理器添加到日志记录器
logger.addHandler(handler)

# 创建控制台处理器
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(fmt)

# 将控制台处理器添加到日志记录器
logger.addHandler(console)

if __name__ == "__main__":
    def example_function():
        logger.info("This is a log message from example_function.")
    example_function()