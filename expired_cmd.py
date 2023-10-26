import pickle
import os

class ExpiredCmd:

    CMD_CACHE_FILE = "cmd_cache.pk"

    def __init__(self):
        self.expired_cmds = set()
        self.load_expired_cmd_cache()

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
        return self.CMD_CACHE_FILE

    def add_cmd_to_expired_cmds(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        self.expired_cmds.add(key)
        self.save_expired_cmd_cache()

    def is_cmd_expired(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        return key in self.expired_cmds

    def load_expired_cmd_cache(self):
        cache_file = self.get_cmd_cache_file_nm()
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                self.expired_cmds = pickle.load(f)

    def save_expired_cmd_cache(self):
        with open(self.get_cmd_cache_file_nm(), "wb") as f:
            pickle.dump(self.expired_cmds, f)