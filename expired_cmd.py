# -*- coding: utf-8 -*-
import pickle
import abc
import os

class ExpiredCmd(metaclass=abc.ABCMeta):
    
    CMD_CACHE_FILE = "cmd_cache.pk"

    def __init__(self):
        self.expired_cmds = set()
        
    def add_cmd_to_expired_cmds(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        self.expired_cmds.add(key)

        with open(self.get_cmd_cache_file_nm(), "wb") as f:
            pickle.dump(self.expired_cmds, f)

    @staticmethod
    def generate_expired_cmd_key(cmd):
        return "{}_{}_{}_{}_{}".format(
            cmd["strategy_name"],
            cmd["user"],
            cmd["stock_code"],
            cmd["action"],
            cmd["msg_id"],
        )
        
    def get_cmd_cache_file_nm(self):
        _new_name = '%s' % (self.CMD_CACHE_FILE)
        return _new_name
     
    def is_cmd_expired(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        return key in self.expired_cmds
    
    def load_expired_cmd_cache(self):
        _new_name = self.get_cmd_cache_file_nm()
        if os.path.exists(_new_name):
            with open(_new_name, "rb") as f:
                self.expired_cmds = pickle.load(f) 

