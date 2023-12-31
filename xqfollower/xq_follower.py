# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import json
import time
from datetime import datetime
from dotenv import load_dotenv
from db_mgr import DbMgr
from .log import logger
import xq_parser
import time_utils
import assets_mgr
import abc
import queue
import threading
import time
import exceptions
from .log_util import log_warning, log_error, log_info, log_trade
from  expired_cmd import ExpiredCmd
from .xq_mgr import XqMgr
import cmd_mgr
from .xq_ws_mgr import XueQiuWebsocketManager

class XueQiuFollower(metaclass=abc.ABCMeta):
    
    trade_cmd_expire_seconds=120
    net_val_dict = {}
    configs = []
    msg_id_set = set()  # 通過socket傳過來的message id（也就是交易信息會存在這裡）

    def __init__(self, **kwargs):
        load_dotenv()  # 加载 .env 文件中的配置
        self.trade_queue = queue.Queue()
        self.exp_cmd = ExpiredCmd()
        self.track_fail = 0
        self.xq_mgr = XqMgr()
        self._adjust_sell = None
        self._users = None
        self.msg_id_set_lock = threading.Lock()
        self.db_mgr = DbMgr()
        self.configs = self.db_mgr._read_config()

    def follow(  # type: ignore
        self,
        users,
        strategy_list,
        adjust_sell=False,
        trade_cmd_expire_seconds=120
    ):
        """跟踪 joinquant 对应的模拟交易，支持多用户多策略
        :param users: 支持 easytrader 的用户对象，支持使用 [] 指定多个用户
        :param strategies: 雪球组合名, 类似 ZH123450
        :param trade_cmd_expire_seconds: 交易指令过期时间, 单位为秒
        """
        self.set_exp_secs(trade_cmd_expire_seconds)
        self._adjust_sell = adjust_sell
        self._users = self.warp_list(users)

        for strategy_url in strategy_list:
            print(strategy_url)
            self.calculate_assets(strategy_url)
            time.sleep(5)
    
    def calculate_assets(self, strategy_id):
        """
        这段代码用于管理特定策略的总资产，
        并根据一些条件对其进行计算和验证。
        如果资产不符合规定的条件，它会引发相应的错误。
        """
        # 都设置时优先选择 total_assets
        if strategy_id not in self.net_val_dict.keys():
            net_value = self._get_portfolio_net_value(strategy_id)
            self.net_val_dict[strategy_id] = net_value
        else:
            net_value = self.net_val_dict[strategy_id]
        logger.info("%s net val: %.2f" % (strategy_id, net_value))
        logger.info("calculate portofolio fund managetment...")
        self.configs = assets_mgr.calculate_total_assets(strategy_id, self.configs, net_value)
        self.ws_mgr = XueQiuWebsocketManager()

    ############################################
    #             track
    ############################################
    def consume_offline_msg(self):
        self.ws_mgr.consume_special_messages()
    
    ############################################
    #             socket
    ############################################
    def do_socket_trade(self, body_content):
        myjson = json.loads(body_content)
        msg_id = myjson['result'][0]["messages"][0]['messageId']

        # Acquire a lock before accessing msg_id_set
        with self.msg_id_set_lock:
            if msg_id in self.msg_id_set:  # Avoid receiving duplicate push messages
                logger.info("same msg id, skip")
                return
            self.msg_id_set.add(msg_id)
        view = myjson['result'][0]["messages"][0]['view']
        logger.info(view)
        try:
            transactions, zh_id, num, strategy_name = self._parse_view_string(view, time.time(), msg_id)
        except:
            logger.info("parse error %s,skip" % view)
            return
        logger.info('parse ok:')
        logger.info(transactions)
        logger.info('making user asserts map...')
        assets_list = self._get_assets_list(zh_id)
        logger.info(assets_list)
        if len(assets_list) != 0:
            logger.info('change over 4,need more details...')
            self.track_strategy(zh_id, strategy_name, assets_list, msg_id)
            logger.info('trade all done, mark database as done')
        else:
            logger.info('not followed trade, mark database as done')
            
    # 在需要拉取详细的交易记录时候， 这个函数会被调用
    def track_strategy(self, strategy, name, assets_list, msg_id,  **kwargs):
        for mytrack_times in range(5):
            try:
                logger.info(f"{mytrack_times}. 拉取详细的调仓记录")

                # 从网络获取交易记录
                tran_list = self.query_strategy_transaction(strategy, assets_list, **kwargs)
                expire = (datetime.now() - tran_list[0][0]['datetime']).total_seconds()

                for user_id, transactions in enumerate(tran_list):
                    self.deal_trans(user_id, transactions, strategy, name, msg_id, **kwargs)

                if expire < self.trade_cmd_expire_seconds:
                    break
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
            
    def _process_transactions(self, transactions, assets_list):
        rets = []
        try:
            tran_list = xq_parser.format_transaction(transactions, assets_list)
            logger.info(tran_list)
            if len(tran_list) == len(self._users):
                for user_id in range(len(self._users)):
                    logger.info('正在处理用户%d的交易数据...' % (user_id))
                    logger.info(tran_list[user_id])
                    rets.append({
                        "uid":user_id, 
                        "trans":tran_list[user_id]
                    })
        except Exception as e:
            logger.warning(e)
        return rets
    
    def _parse_view_string(self, view, insert_t, msg_id):
        zuhe_id = xq_parser.parse_view_zuhe_id(view)   
        strategy_name = xq_parser.parse_view_strategy_name(view)
        stok_num = xq_parser.parse_view_stk_num(view)
        trans_list = xq_parser.parse_view_string(view, insert_t, msg_id)
        for tran in trans_list:
            stk_nm = tran["stock_name"]
            code = self.get_code(stk_nm)
            close = self.get_price(stk_nm)
            if close == 0:
                logger.info(f"{stk_nm}价格获取失败")
                tran["price"] = 0
                tran["stock_symbol"] = 0
            else:
                tran["price"] = close
                tran["stock_symbol"] = code
        if stok_num > 0:
            return trans_list, zuhe_id, stok_num, strategy_name
        else:
            return [], zuhe_id, 0, strategy_name
    
    def deal_trans(self, userid, transactions, strategy, name, msg_id, interval=10,  **kwargs):
        idx = 0
        for transaction in transactions:
            trade_cmd = cmd_mgr.build_trade_cmd(userid, transaction, strategy, name, msg_id)
            if self.exp_cmd.is_cmd_expired(trade_cmd):
                logger.info('指令与缓存指令冲突')
                continue
            log_trade(logger, trade_cmd, name)
            self.execute_trade_cmd(trade_cmd)
            self.exp_cmd.add_cmd_to_expired_cmds(trade_cmd)
            idx += 1
        return idx
    
    def execute_trade_cmd(self, trade_cmd):
        """
        分发交易指令到对应的 user 并执行
        """
        user_id = trade_cmd['user']
        user = self.get_users(user_id)
        args, action, price =  cmd_mgr.execute_trade_cmd(trade_cmd)
        try:
            # 调用 user 对象的指定 action 方法，传入参数 args
            response = getattr(user, action)(**args)
        except exceptions.TradeError as e:
            # 如果出现 TradeError 异常，捕获并处理
            trader_name = type(user).__name__
            err_msg = f"{type(e).__name__}: {e.args}"
            # 记录错误信息到日志，包括交易命令、交易者名称、价格、错误消息
            log_error(logger, trade_cmd, trader_name, price, err_msg)
        else:
            # 如果没有异常，记录交易信息到日志，包括交易命令和价格
            log_info(logger, trade_cmd, price, response)

    def extract_strategy_name(self, strategy_url):
        self.strategy_name = self.xq_mgr.extract_strategy_name(strategy_url)
        return self.strategy_name

    '''
    解压历史交易(可能有两次调仓, 每次调仓有两笔交易)
    '''
    def extract_transactions(self, history):
        return xq_parser.extract_transactions(history)

    def project_transactions(self, transactions, assets):
        xq_parser.project_transactions(transactions, assets)

    def _get_portfolio_info(self, portfolio_code):
        resp = self.xq_mgr._get_portfolio_info(portfolio_code)
        return xq_parser.parse_portfolio_info(resp)

    def _get_portfolio_net_value(self, portfolio_code):
        """
        获取组合信息
        """
        portfolio_info = self._get_portfolio_info(portfolio_code)
        return xq_parser.get_portfolio_net_value(portfolio_info)
                
    def query_strategy_transaction(self, strategy, assets_list, **kwargs):
        history = self.xq_mgr.query_strategy_transaction(strategy)
        return xq_parser.parse_strategy_transaction(history, assets_list, kwargs)

    def set_exp_secs(self, _s):
        self.trade_cmd_expire_seconds = _s

    @staticmethod
    def warp_list(value):
        if not isinstance(value, list):
            value = [value]
        return value

    def load_expired_cmd_cache(self):
        self.exp_cmd._load_expired_cmd_cache()
    def _get_assets_list(self, zh_id):
        user_domains = [u.get_domain() for u in self.users]
        return assets_mgr.get_assets_list(zh_id, user_domains, self.configs)
    def get_users(self, userid):
        return self._users[userid]
    