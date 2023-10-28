import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xqfollower import *

class TestExpiredCmd(unittest.TestCase):

    # 用于设置临时文件夹和文件
    def setUp(self):
        self.cmd_cache_file = "cmd_cache.pk"

    # 方法用于清理测试过程中生成的文件
    def tearDown(self):
        if os.path.exists(self.cmd_cache_file):
            os.remove(self.cmd_cache_file)

    def test_add_cmd_to_expired_cmds(self):
        cmd = {
            "strategy_name": "test_strategy",
            "user": "test_user",
            "stock_code": "AAPL",
            "action": "buy",
            "msg_id": 123
        }
        expired_cmd = ExpiredCmd()
        self.assertFalse(expired_cmd.is_cmd_expired(cmd))
        expired_cmd.add_cmd_to_expired_cmds(cmd)
        self.assertTrue(expired_cmd.is_cmd_expired(cmd))

    def test_is_cmd_expired(self):
        cmd1 = {
            "strategy_name": "test_strategy",
            "user": "test_user",
            "stock_code": "AAPLGOOG",
            "action": "buy",
            "msg_id": 123456
        }
        cmd2 = {
            "strategy_name": "another_strategy",
            "user": "another_user",
            "stock_code": "GOOG",
            "action": "sell",
            "msg_id": 456
        }
        expired_cmd = ExpiredCmd()
        self.assertFalse(expired_cmd.is_cmd_expired(cmd1))
        self.assertFalse(expired_cmd.is_cmd_expired(cmd2))
        expired_cmd.add_cmd_to_expired_cmds(cmd1)
        self.assertTrue(expired_cmd.is_cmd_expired(cmd1))
        self.assertFalse(expired_cmd.is_cmd_expired(cmd2))

if __name__ == '__main__':
    unittest.main()
