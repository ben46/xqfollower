import pickle
import os

class ExpiredCmd:

    CMD_CACHE_FILE = "cmd_cache.pk"

    def __init__(self):
        self.expired_cmds = set()
        self._load_expired_cmd_cache()
        
    def add_cmd_to_expired_cmds(self, cmd):
        key = self._generate_expired_cmd_key(cmd)
        self.expired_cmds.add(key)
        self._save_expired_cmd_cache()

    def is_cmd_expired(self, cmd):
        key = self._generate_expired_cmd_key(cmd)
        return key in self.expired_cmds

    @staticmethod
    def _generate_expired_cmd_key(cmd):
        return "{}_{}_{}_{}_{}".format(
            cmd["strategy_name"],
            cmd["user"],
            cmd["stock_code"],
            cmd["action"],
            cmd["msg_id"],
        )
        
    def _get_cmd_cache_file_nm(self):
        return self.CMD_CACHE_FILE

    def _load_expired_cmd_cache(self):
        cache_file = self._get_cmd_cache_file_nm()
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                self.expired_cmds = pickle.load(f)

    def _save_expired_cmd_cache(self):
        with open(self._get_cmd_cache_file_nm(), "wb") as f:
            pickle.dump(self.expired_cmds, f)