import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xqfollower import calculate_total_assets

class TestAssetFunctions(unittest.TestCase):

    def test_1(self):
        strategy_id = "ABC"
        configs = [
            {"ZH": "ABC", "cap0": 100, "total_assets": 0},
            {"ZH": "XYZ", "cap0": 200, "total_assets": 0},
        ]
        net_value = 1.5

        result = calculate_total_assets(strategy_id, configs, net_value)
        # 预期结果：
        # [{"ZH": "ABC", "cap0": 100, "total_assets": 150.0}, {"ZH": "XYZ", "cap0": 200, "total_assets": 0}]


if __name__ == '__main__':
    unittest.main()
