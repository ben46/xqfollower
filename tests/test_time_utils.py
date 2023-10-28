import unittest
from unittest.mock import patch
from datetime import datetime
import pytz
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xqfollower import *

class TestTradingFunctions(unittest.TestCase):

    @patch('xqfollower.datetime')
    def test_FROMOPEN_seconds(self, mock_datetime):
        # Test when current time is before the market opens (before 09:30 AM)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 9, 0, tzinfo=pytz.timezone('Asia/Chongqing'))
        self.assertEqual(FROMOPEN_seconds(), 0)

        # Test during the morning trading hours (between 09:30 AM and 11:30 AM)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, tzinfo=pytz.timezone('Asia/Chongqing'))
        self.assertEqual(FROMOPEN_seconds(), 1800)

        # Add more test cases for different time scenarios

    @patch('xqfollower.datetime')
    def test_should_exit(self, mock_datetime):
        # Test when the current hour is before 3 PM
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0, tzinfo=pytz.timezone('Asia/Chongqing'))
        self.assertFalse(should_exit())

        # Test when the current hour is after or at 3 PM
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 0, tzinfo=pytz.timezone('Asia/Chongqing'))
        self.assertTrue(should_exit())

        # Add more test cases for different time scenarios

    @patch('xqfollower.FROMOPEN_seconds')
    def test_is_off_trading_hour(self, mock_FROMOPEN_seconds):
        # Test when FROMOPEN_seconds returns 0
        mock_FROMOPEN_seconds.return_value = 0
        self.assertTrue(is_off_trading_hour())

        # Test when FROMOPEN_seconds returns 7200 (2 hours)
        mock_FROMOPEN_seconds.return_value = 7200
        self.assertTrue(is_off_trading_hour())

        # Test when FROMOPEN_seconds returns 14400 (4 hours)
        mock_FROMOPEN_seconds.return_value = 14400
        self.assertTrue(is_off_trading_hour())

        # Test when FROMOPEN_seconds returns 1800 (30 minutes)
        mock_FROMOPEN_seconds.return_value = 1800
        self.assertFalse(is_off_trading_hour())

        # Add more test cases for different scenarios

    @patch('xqfollower.FROMOPEN_seconds')
    def test_should_fetch_off_trades(self, mock_FROMOPEN_seconds):
        # Test when FROMOPEN_seconds returns 1
        mock_FROMOPEN_seconds.return_value = 1
        self.assertTrue(should_fetch_off_trades())

        # Test when FROMOPEN_seconds returns 121
        mock_FROMOPEN_seconds.return_value = 121
        self.assertTrue(should_fetch_off_trades())

        # Test when FROMOPEN_seconds returns 7199 (1 second before 2 hours)
        mock_FROMOPEN_seconds.return_value = 7199
        self.assertTrue(should_fetch_off_trades())

        # Test when FROMOPEN_seconds returns 7200 (2 hours)
        mock_FROMOPEN_seconds.return_value = 7200
        self.assertFalse(should_fetch_off_trades())

        # Add more test cases for different scenarios

if __name__ == '__main__':
    unittest.main()
