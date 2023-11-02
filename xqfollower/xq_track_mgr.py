from threading import Thread
import time
import os
import signal
import time_utils

from .log import logger


class XueQiuTrackManager:
    def __init__(self, target, action):
        self.target = target
        self.action = action
        strategy_worker = Thread(target=self.track_strategy)
        strategy_worker.start()
        
    def track_strategy(self):
        while True:
            if time_utils.is_off_trading_hour():
                time.sleep(1)
                continue
            time.sleep(1)
            if time_utils.should_exit():
                logger.info("15:00 exit(0)")
                os.kill(os.getpid(), signal.SIGINT)
            try:
                getattr(self.target, self.action)()
            except Exception as e:
                logger.warning(e)
                time.sleep(5)