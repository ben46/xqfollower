# -*- coding: utf-8 -*-
import logging
_logger_nm = "xqfollower"
logger = logging.getLogger(_logger_nm)
logger.setLevel(logging.INFO)
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s %(lineno)s: %(message)s"
)
handler = logging.FileHandler('%s.log' % _logger_nm, 'a', 'utf-8')
handler.setFormatter(fmt)
logger.addHandler(handler)
# ---------------------
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(fmt)
logger.addHandler(console)