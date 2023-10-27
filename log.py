# -*- coding: utf-8 -*-
import logging

# 设置日志记录器的名称
_logger_nm = "xqfollower"

# 创建日志记录器
logger = logging.getLogger(_logger_nm)
logger.setLevel(logging.INFO)

# 定义日志格式
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s %(lineno)s: %(message)s"
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
