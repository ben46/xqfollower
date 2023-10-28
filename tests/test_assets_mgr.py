import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xqfollower import calculate_total_assets, get_assets_list

class TestAssetFunctions(unittest.TestCase):

    def test_get_assets_list(self):
        zh_id = "ZH123"
        user_domains = ["domain1", "domain2"]
        configs = [
            {"ZH": "ZH123", "host": "domain1", "total_assets": 1500},
            {"ZH": "ZH123", "host": "domain2"},
            {"ZH": "ZH456", "host": "domain1", "total_assets": 800},
        ]
        # 特定策略下的资产信息
        assets_list = get_assets_list(zh_id, user_domains, configs)

        self.assertIn(1500, assets_list)
        self.assertNotIn(800, assets_list)

if __name__ == '__main__':
    unittest.main()
