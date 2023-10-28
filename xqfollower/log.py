# -*- coding: utf-8 -*-

import logging
import inspect
import os
from logging.handlers import TimedRotatingFileHandler

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

# 获取当前日期作为文件夹和日志文件名
import datetime
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_folder = os.path.join("logs", current_date)

# 如果日志文件夹不存在，创建它
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# 设置日志记录器的名称
_logger_nm = "xqfollower"

# 创建日志记录器，使用自定义的CustomLogger
logger = CustomLogger(_logger_nm)
logger.setLevel(logging.INFO)

# 定义日志格式
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s]: %(message)s"
)

# 创建TimedRotatingFileHandler以按日期轮换日志文件
'''这行代码是用来创建一个`TimedRotatingFileHandler`对象，它用于处理日志文件的按时间轮换。下面是每个参数的含义：

1. `filename`: 这是要写入日志的文件的名称。在这里，我们使用`os.path.join(log_folder, f'{_logger_nm}.log')`来生成日志文件的完整路径。`log_folder`是包含日志文件的文件夹路径，`f'{_logger_nm}.log'`是日志文件的名称，其中`_logger_nm`是您定义的日志记录器的名称。这确保了日志文件将被保存在指定的文件夹中，并具有正确的名称。

2. `when`: 这是指定何时轮换日志文件的参数。在这里，`'midnight'`表示每天午夜时分触发轮换。也就是说，每当系统的日期从前一天切换到下一天的时候，都会创建一个新的日志文件。

3. `interval`: 这是指定轮换的时间间隔的参数。在这里，`interval=1`表示每天都会轮换日志文件，因为我们在`when`参数中选择了`'midnight'`。

4. `backupCount`: 这是指定保留多少个旧日志文件的参数。在这里，`backupCount=7`表示会保留最多7个旧日志文件，包括当前日志文件。一旦达到这个数量，最旧的日志文件将被删除，以便释放磁盘空间。

综合起来，这行代码创建了一个按日期轮换的日志文件处理器，将日志写入指定的文件，每天午夜时分切换到新的日志文件，保留最多7个旧的日志文件。这有助于管理日志文件，确保它们不会无限增长并占用磁盘空间。'''
log_handler = TimedRotatingFileHandler(filename=os.path.join(log_folder, f'{_logger_nm}.log'), when='midnight', interval=1, backupCount=90)
log_handler.setFormatter(fmt)
logger.addHandler(log_handler)

# 创建控制台处理器
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(fmt)
logger.addHandler(console)

if __name__ == "__main__":
    def example_function():
        logger.info("This is a log message from example_function.")
    example_function()
