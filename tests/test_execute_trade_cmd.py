import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xqfollower import *
from datetime import datetime

class TestExecuteTradeCmd(unittest.TestCase):
    def test_valid_trade_cmd(self):
        trade_cmd = {
            "action": "buy",
            "stock_code": "AAPL",
            "msg_id": 12345,
            "strategy_name": "my_strategy",
            "price": 150.0,
            "amount": 100,
            "datetime": datetime.now()
        }
        args, action, price = execute_trade_cmd(trade_cmd)
        self.assertIsNotNone(args)
        self.assertEqual(action, "buy")
        self.assertEqual(price, 150.0)

    def test_invalid_price(self):
        trade_cmd = {
            "action": "buy",
            "stock_code": "AAPL",
            "msg_id": 12345,
            "strategy_name": "my_strategy",
            "price": -10.0,  # Invalid price
            "amount": 100,
            "datetime": datetime.now()
        }

        # Mock the logger.warning method to capture log messages
        args, action, price = execute_trade_cmd(trade_cmd)
        self.assertIsNone(args)  # Should not return args
        self.assertIsNone(action)  # Should not return action
        self.assertIsNone(price)  # Should not return price

    def test_invalid_amount(self):
        trade_cmd = {
            "action": "sell",
            "stock_code": "GOOG",
            "msg_id": 54321,
            "strategy_name": "another_strategy",
            "price": 1200.0,
            "datetime": datetime.now(),
            "amount": 0  # Invalid amount
        }

        # Mock the logger.warning method to capture log messages
        args, action, price = execute_trade_cmd(trade_cmd)
        self.assertIsNone(args)  # Should not return args
        self.assertIsNone(action)  # Should not return action
        self.assertIsNone(price)  # Should not return price

if __name__ == '__main__':
    unittest.main()
