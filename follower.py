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
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tushare'))
import tushare as ts
import pytz

class BaseFollower2b(metaclass=abc.ABCMeta):
    LOGIN_PAGE = ""
    LOGIN_API = ""
    TRANSACTION_API = ""
    CMD_CACHE_FILE = "cmd_cache.pk"
    WEB_REFERER = ""
    WEB_ORIGIN = ""
    skn_nm_cache = None
    trade_cmd_expire_seconds=120
    def __init__(self):
        self.trade_queue = queue.Queue()
        self.expired_cmds = set()

        self.s = requests.Session()
        self.s.verify = False

        self.slippage: float = 0.0
        self.trader = None
        self.track_fail = 0

    def login(self, user=None, password=None, **kwargs):
        pass

    def _generate_headers(self):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/54.0.2840.100 Safari/537.36",
            "Referer": self.WEB_REFERER,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.WEB_ORIGIN,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        return headers

    def check_login_success(self, rep):
        pass

    def create_login_params(self, user, password, **kwargs) -> dict:
        return {}

    def follow(
        self,
        users,
        strategy,
        track_interval=1,
        trade_cmd_expire_seconds=120,
        cmd_cache=True,
        slippage: float = 0.0,
        **kwargs
    ):

        self.slippage = slippage
        self.strategy = strategy

    def getStrategy(self):
        return self.strategy

    def get_cmd_cache_file_nm(self):
        _new_name = '%s' % (self.CMD_CACHE_FILE)
        return _new_name

    def load_expired_cmd_cache(self):
        _new_name = self.get_cmd_cache_file_nm()
        if os.path.exists(_new_name):
            with open(_new_name, "rb") as f:
                self.expired_cmds = pickle.load(f)

    def get_stknm_cache_file_nm(self):
        return "stk_nm_%s" % datetime.datetime.now(pytz.timezone('Asia/Chongqing')).strftime('%Y_%m_%d')

    def fetch_code_nm(self):
        logger.info('获取股票名称和股票价格的df...')
        if self.skn_nm_cache is not None:
            return
        if os.path.exists(self.get_stknm_cache_file_nm()):
            print('文件本地存在')
            with open(self.get_stknm_cache_file_nm(), "rb") as f:
                self.skn_nm_cache = pickle.load(f)
                # print(self.skn_nm_cache)
        else:
            self.skn_nm_cache = ts.get_today_all()
            with open(self.get_stknm_cache_file_nm(), "wb") as f:
                pickle.dump(self.skn_nm_cache, f)

    def _get_idx_by_nm(self, stk_name, kw='st'):
        for i in range(self.skn_nm_cache.shape[0]):
            db_nm = self.skn_nm_cache.iloc[i]['name']
            input_nm = stk_name.lower().replace(kw.lower(), '').replace(" ", "").replace("*", "").replace("-", "")
            if db_nm.find(input_nm) >= 0:
                return i
        return 999999

    def _get_idx_by_nm2(self, stk_name):
        for i in range(self.skn_nm_cache.shape[0]):
            _stk_nm = self.skn_nm_cache.iloc[i]['name']
            if _stk_nm.find("Ａ") >= 0:
                tmp = stk_name.split("Ａ")[0].replace(" ", "")
                if _stk_nm.find(tmp):
                    return i
        return -1

    def get_stk_row(self, stk_code):
        try:
            stk_code = stk_code[-6:]
            return self.skn_nm_cache[self.skn_nm_cache['code'] == stk_code].iloc[0]
        except Exception as e:
            logger.info("获取%s代码出错" % stk_code)
            print(e)

    def _get_row_by_nm(self, stk_name):
        if stk_name.find('-U') >= 0:
            print(stk_name)
            return self.skn_nm_cache.iloc[self._get_idx_by_nm(stk_name, kw='-U')]
        if stk_name.find('st') >= 0 or stk_name.find('ST') >= 0:
            return self.skn_nm_cache.iloc[self._get_idx_by_nm(stk_name)]
        if stk_name.find('A') >= 0:
            return self.skn_nm_cache.iloc[self._get_idx_by_nm2(stk_name)]
        if stk_name.find('XD') >= 0:
            return self.skn_nm_cache.iloc[self._get_idx_by_nm(stk_name, kw='xd')]
        if stk_name.find('XR') >= 0:
            return self.skn_nm_cache.iloc[self._get_idx_by_nm(stk_name, kw='xr')]
        return self.skn_nm_cache[self.skn_nm_cache['name'] == stk_name].iloc[0]

    def get_code(self, stk_name):
        try:
            return self._get_row_by_nm(stk_name)['code']
        except Exception as e:
            logger.info("获取%s代码出错" % stk_name)
            print(e)

    def get_price(self, stk_name):
        try:
            return self._get_row_by_nm(stk_name)['trade']
        except Exception as e:
            logger.info("获取%s代码出错" % stk_name)
            print(e)
        return 0

    def get_stk_all(self):
        return self.skn_nm_cache




    @staticmethod
    def warp_list(value):
        if not isinstance(value, list):
            value = [value]
        return value

    @staticmethod
    def extract_strategy_id(strategy_url):
        pass

    def extract_strategy_name(self, strategy_url):
        pass

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
            if self.is_cmd_expired(trade_cmd):
                logger.info('指令与缓存指令冲突')
                continue

            logger.info(
                "策略 [%s] 发送指令到交易队列, 股票: %s 动作: %s 数量: %s 价格: %s 信号产生时间: %s",
                name,
                trade_cmd["stock_code"],
                trade_cmd["action"],
                trade_cmd["amount"],
                trade_cmd["price"],
                trade_cmd["datetime"],
            )
            self.execute_trade_cmd(trade_cmd)
            self.add_cmd_to_expired_cmds(trade_cmd)
            idx += 1
        return idx

    def set_exp_secs(self, _s):
        self.trade_cmd_expire_seconds = _s

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

    @staticmethod
    def generate_expired_cmd_key(cmd):
        return "{}_{}_{}_{}_{}".format(
            cmd["strategy_name"],
            cmd["user"],
            cmd["stock_code"],
            cmd["action"],
            cmd["msg_id"],
        )

    def is_cmd_expired(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        return key in self.expired_cmds

    def add_cmd_to_expired_cmds(self, cmd):
        key = self.generate_expired_cmd_key(cmd)
        self.expired_cmds.add(key)

        with open(self.get_cmd_cache_file_nm(), "wb") as f:
            pickle.dump(self.expired_cmds, f)


    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_users(self, userid):
        return None

    def execute_trade_cmd(
        self, trade_cmd
    ):
        """分发交易指令到对应的 user 并执行
        :param trade_cmd:
        :param users:
        :param expire_seconds:
        :param entrust_prop:
        :param send_interval:
        :return:
        """
        user_id = trade_cmd['user']
        user = self.get_users(user_id)
        # check expire
        now = datetime.datetime.now()
        expire = (now - trade_cmd["datetime"]).total_seconds()
        # 5. 取消超时（因为盘后的推送会被误以为是超时交易）
        # if expire > self.trade_cmd_expire_seconds:
        #     logger.warning(
        #         "策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格: %s)超时，指令产生时间: %s 当前时间: %s, 超过设置的最大过期时间 %s 秒, 被丢弃",
        #         trade_cmd["strategy_name"],
        #         trade_cmd["stock_code"],
        #         trade_cmd["action"],
        #         trade_cmd["amount"],
        #         trade_cmd["price"],
        #         trade_cmd["datetime"],
        #         now,
        #         self.trade_cmd_expire_seconds,
        #     )
        #     return

        # check price
        price = trade_cmd["price"]
        if not self._is_number(price) or price <= 0:
            logger.warning(
                "策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格: %s)超时，指令产生时间: %s 当前时间: %s, 价格无效 , 被丢弃",
                trade_cmd["strategy_name"],
                trade_cmd["stock_code"],
                trade_cmd["action"],
                trade_cmd["amount"],
                trade_cmd["price"],
                trade_cmd["datetime"],
                now,
            )
            return

        # check amount
        if trade_cmd["amount"] <= 0:
            logger.warning(
                "策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格: %s)超时，指令产生时间: %s 当前时间: %s, 买入股数无效 , 被丢弃",
                trade_cmd["strategy_name"],
                trade_cmd["stock_code"],
                trade_cmd["action"],
                trade_cmd["amount"],
                trade_cmd["price"],
                trade_cmd["datetime"],
                now,
            )
            return

        actual_price = trade_cmd["price"]
        # 删除价格作为hash的来源， 因为价格是实时获取的，不是推送的
        data = "%s,%s,%s,%s" % (trade_cmd["action"],
                                      trade_cmd["stock_code"],
                                      trade_cmd["msg_id"],
                                      trade_cmd["strategy_name"])  # 要进行加密的数据
        my_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
        args = {
            "security": trade_cmd["stock_code"],
            "price": actual_price,
            "amount": trade_cmd["amount"],
            "hash": my_hash,
        }
        try:
            response = getattr(user, trade_cmd["action"])(**args)
        except exceptions.TradeError as e:
            trader_name = type(user).__name__
            err_msg = "{}: {}".format(type(e).__name__, e.args)
            logger.error(
                "%s 执行 策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格(考虑滑点): %s 指令产生时间: %s) 失败, 错误信息: %s",
                trader_name,
                trade_cmd["strategy_name"],
                trade_cmd["stock_code"],
                trade_cmd["action"],
                trade_cmd["amount"],
                actual_price,
                trade_cmd["datetime"],
                err_msg,
            )
        else:
            logger.info(
                "策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格(考虑滑点): %s 指令产生时间: %s) 执行成功, 返回: %s",
                trade_cmd["strategy_name"],
                trade_cmd["stock_code"],
                trade_cmd["action"],
                trade_cmd["amount"],
                actual_price,
                trade_cmd["datetime"],
                response,
            )
            return

    def query_strategy_transaction(self, strategy, assets_list, **kwargs):
        params = self.create_query_transaction_params(strategy)
        rep = self.s.get(self.TRANSACTION_API, params=params)
        history = rep.json()
        tra_list = []
        for assets in assets_list:
            transactions = self.extract_transactions(history)
            kwargs['assets'] = assets
            self.project_transactions(transactions, **kwargs)
            ret = self.order_transactions_sell_first(transactions)
            copy_list = []
            for tra in ret:
                copy_list.append(tra.copy())
            tra_list.append(copy_list)
        return tra_list

    def extract_transactions(self, history) -> List[str]:
        """
        抽取接口返回中的调仓记录列表
        :param history: 调仓接口返回信息的字典对象
        :return: [] 调参历史记录的列表
        """
        return []

    def create_query_transaction_params(self, strategy) -> dict:
        """
        生成用于查询调参记录的参数
        :param strategy: 策略 id
        :return: dict 调参记录参数
        """
        return {}

    @staticmethod
    def re_find(pattern, string, dtype=str):
        return dtype(re.search(pattern, string).group())

    @staticmethod
    def re_search(pattern, string, dtype=str):
        return dtype(re.search(pattern,string).group(1))

    def project_transactions(self, transactions, **kwargs):
        """
        修证调仓记录为内部使用的统一格式
        :param transactions: [] 调仓记录的列表
        :return: [] 修整后的调仓记录
        """
        pass

    def order_transactions_sell_first(self, transactions):
        # 调整调仓记录的顺序为先卖再买
        sell_first_transactions = []
        for transaction in transactions:
            if transaction["action"] == "sell":
                sell_first_transactions.insert(0, transaction)
            else:
                sell_first_transactions.append(transaction)
        return sell_first_transactions