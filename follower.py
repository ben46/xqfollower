# -*- coding: utf-8 -*-
import abc
import datetime
import os
import pickle
import queue
import threading
import time
from typing import List
import requests
from easytrader import exceptions
from easytrader.log import logger
import hashlib
import re
from log_warning import log_warning, log_error, log_info, log_trade
from  expired_cmd import ExpiredCmd
import xq_parser
from .xq_mgr import XqMgr

class BaseFollower(metaclass=abc.ABCMeta):
    LOGIN_PAGE = ""
    LOGIN_API = ""
    TRANSACTION_API = ""
    WEB_REFERER = ""
    WEB_ORIGIN = ""
    skn_nm_cache = None
    trade_cmd_expire_seconds=120
    def __init__(self):
        self.trade_queue = queue.Queue()
        self.cmd_mgr = ExpiredCmd()

        self.s = requests.Session()
        self.s.verify = False

        self.slippage: float = 0.0
        self.trader = None
        self.track_fail = 0
        self.xq_mgr = XqMgr()


    # 在需要拉取详细的交易记录时候， 这个函数会被调用
    def track_strategy(self, strategy, name, assets_list, msg_id,  **kwargs):
        for mytrack_times in range(5):
            try:
                logger.info(f"{mytrack_times}. 拉取详细的调仓记录")

                # 从网络获取交易记录
                tran_list = self.query_strategy_transaction(
                    strategy, assets_list, **kwargs
                )  # 返回值：多个用户组成的二维数组交易条目

                expire = (datetime.datetime.now() - tran_list[0][0]['datetime']).total_seconds()

                user_id = 0
                # 循环不同的用户
                for transactions in tran_list:
                    # 执行交易指令，因为我们并没有制定msgid， 所以这里会自动生成一个时间戳作为msgid
                    self.deal_trans(user_id, transactions, strategy, name, msg_id, **kwargs)
                    user_id += 1
                if expire < self.trade_cmd_expire_seconds:
                    break
            # pylint: disable=broad-except
            except Exception as e:
                logger.exception("%d: 无法获取策略 %s 调仓信息, 错误: %s, 跳过此次调仓查询", self.track_fail, name, e)
                self.track_fail += 1
                print('connect fail', self.track_fail)
                time.sleep(3 * self.track_fail)
                continue
            if self.track_fail != 0:
                print('reconnected!')
            self.track_fail = 0
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("程序退出")
                exit()
                
    def query_strategy_transaction(self, strategy, assets_list, **kwargs):
        history = self.xq_mgr.query_strategy_transaction(strategy)
        return xq_parser.parse_strategy_transaction(history, assets_list, kwargs)
        
    def deal_trans(self, userid, transactions, strategy, name, msg_id, interval=10,  **kwargs):
        idx = 0
        for transaction in transactions:
            trade_cmd = {
                "strategy": strategy,
                "user": userid,
                "msg_id": transaction["msg_id"] if "msg_id" in transaction else msg_id,
                "strategy_name": name,
                "action": transaction["action"],
                "stock_code": transaction["stock_code"],
                "amount": transaction["amount"],
                "price": transaction["price"],
                "datetime": transaction["datetime"],
            }
            if self.cmd_mgr.is_cmd_expired(trade_cmd):
                logger.info('指令与缓存指令冲突')
                continue
            log_trade(logger, trade_cmd, name)
            self.execute_trade_cmd(trade_cmd)
            self.cmd_mgr.add_cmd_to_expired_cmds(trade_cmd)
            idx += 1
        return idx

    def set_exp_secs(self, _s):
        self.trade_cmd_expire_seconds = _s

    def execute_trade_cmd(self, trade_cmd):
        """
        分发交易指令到对应的 user 并执行
        """
        user_id = trade_cmd['user']
        user = self.get_users(user_id)
        now = datetime.datetime.now()
        
        # 使用字典解构来获取字段
        action = trade_cmd["action"]
        stock_code = trade_cmd["stock_code"]
        msg_id = trade_cmd["msg_id"]
        strategy_name = trade_cmd["strategy_name"]
        price = trade_cmd["price"]
        amount = trade_cmd["amount"]

        if not self._is_number(price) or price <= 0:
            log_warning(logger, trade_cmd, now, "!price")
            return

        if amount <= 0:
            log_warning(logger, trade_cmd, now, "!amount")
            return

        # 删除价格作为hash的来源， 因为价格是实时获取的，不是推送的
        data = f"{action},{stock_code},{msg_id},{strategy_name}"  # 要进行加密的数据
        my_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
        
        args = {
            "security": stock_code,
            "price": price,
            "amount": amount,
            "hash": my_hash,
        }
        
        try:
            response = getattr(user, action)(**args)
        except exceptions.TradeError as e:
            trader_name = type(user).__name__
            err_msg = f"{type(e).__name__}: {e.args}"
            log_error(logger, trade_cmd, trader_name, price, err_msg)
        else:
            log_info(logger, trade_cmd, price, response)

    def order_transactions_sell_first(self, transactions):
        return xq_parser.order_transactions_sell_first(transactions)
    # ==================================================
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # 
    # ==================================================
    def project_transactions(self, transactions, **kwargs):
        """
        修证调仓记录为内部使用的统一格式
        :param transactions: [] 调仓记录的列表
        :return: [] 修整后的调仓记录
        """
        pass
    
    def extract_transactions(self, history) -> List[str]:
        """
        抽取接口返回中的调仓记录列表
        :param history: 调仓接口返回信息的字典对象
        :return: [] 调参历史记录的列表
        """
        return []

    @staticmethod
    def re_find(pattern, string, dtype=str):
        return dtype(re.search(pattern, string).group())

    @staticmethod
    def re_search(pattern, string, dtype=str):
        return dtype(re.search(pattern,string).group(1))

    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_users(self, userid):
        return None
    
    def login(self, user=None, password=None, **kwargs):
        pass

    def check_login_success(self, rep):
        pass

    def create_login_params(self, user, password, **kwargs) -> dict:
        return {}
    
    
    def getStrategy(self):
        return self.strategy

    @staticmethod
    def warp_list(value):
        if not isinstance(value, list):
            value = [value]
        return value

    def extract_strategy_name(self, strategy_url):
        pass

    def load_expired_cmd_cache(self):
        self.cmd_mgr.load_expired_cmd_cache()
