from xq_follower import XueQiuFollower
from threading import Thread
from .log import logger
import time
import os
import signal
import time_utils

xq = XueQiuFollower()
xq.follow()

def do_loop():
    while True:
        time.sleep(1)
        if time_utils.should_exit():
            logger.info("15:00 exit(0)")
            os.kill(os.getpid(), signal.SIGINT)
        try:
            xq.track_strategy_worker()
        except Exception as e:
            logger.warning(e)
            time.sleep(5)
    
logger.info("open new thread,loop database...")
strategy_worker = Thread(
    target=do_loop,
)
strategy_worker.start()
