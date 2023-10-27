# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import json
import re
import time
from datetime import datetime
from numbers import Number
from .follower import BaseFollower
import asyncio
import websockets
from threading import Thread
import os
import signal
import inspect
import utils_zq.Myqq as Myqq
import threading
from dotenv import load_dotenv
from db_mgr import DbMgr
from .log import logger
import xq_parser
import time_utils
import assets_mgr

class XueQiuFollower(BaseFollower):
    net_val_dict = {}
    configs = []
    track_strategy_worker_db = None
    msg_id_set = set()  # 通過socket傳過來的message id（也就是交易信息會存在這裡）

    def __init__(self, **kwargs):
        super().__init__()
        self._adjust_sell = None
        self._users = None
        self.fetch_code_nm()
        # assert self.get_code("夜光明") == '873527'
        self.msg_id_set_lock = threading.Lock()
        load_dotenv()  # 加载 .env 文件中的配置
        self.db_mgr = DbMgr()
        self.configs = self.db_mgr._read_config()

    def follow(  # type: ignore
        self,
        users,
        strategy_list,
        total_assets=10000,
        initial_assets=None,
        adjust_sell=False,
        track_interval=10,
        trade_cmd_expire_seconds=120,
        cmd_cache=True,
        slippage: float = 0.0,
    ):
        """跟踪 joinquant 对应的模拟交易，支持多用户多策略
        :param users: 支持 easytrader 的用户对象，支持使用 [] 指定多个用户
        :param strategies: 雪球组合名, 类似 ZH123450
        :param total_assets: 雪球组合对应的总资产， 格式 [组合1对应资金, 组合2对应资金]
            若 strategies=['ZH000001', 'ZH000002'],
                设置 total_assets=[10000, 10000], 则表明每个组合对应的资产为 1w 元
            假设组合 ZH000001 加仓 价格为 p 股票 A 10%,
                则对应的交易指令为 买入 股票 A 价格 P 股数 1w * 10% / p 并按 100 取整
        :param adjust_sell: 是否根据用户的实际持仓数调整卖出股票数量，
            当卖出股票数大于实际持仓数时，调整为实际持仓数。目前仅在银河客户端测试通过。
            当 users 为多个时，根据第一个 user 的持仓数决定
        :type adjust_sell: bool
        :param initial_assets: 雪球组合对应的初始资产,
            格式 [ 组合1对应资金, 组合2对应资金 ]
            总资产由 初始资产 × 组合净值 算得， total_assets 会覆盖此参数
        :param track_interval: 轮训模拟交易时间，单位为秒
        :param trade_cmd_expire_seconds: 交易指令过期时间, 单位为秒
        :param cmd_cache: 是否读取存储历史执行过的指令，防止重启时重复执行已经交易过的指令
        :param slippage: 滑点，0.0 表示无滑点, 0.05 表示滑点为 5%
        """
        super().follow(
            users=users,
            strategy=strategy_list,
            track_interval=track_interval,
            trade_cmd_expire_seconds=trade_cmd_expire_seconds,
            cmd_cache=cmd_cache,
            slippage=slippage,
        )
        # assert trade_cmd_expire_seconds <= 20
        self.set_exp_secs(trade_cmd_expire_seconds)
        self._adjust_sell = adjust_sell
        self._users = self.warp_list(users)

        for strategy_url in strategy_list:
            print(strategy_url)
            self.calculate_assets(strategy_url)
            time.sleep(5)

        logger.info("open new thread,loop database...")
        strategy_worker = Thread(
            target=self.track_strategy_worker,
        )
        strategy_worker.start()

        logger.info("openning ws...")
        asyncio.get_event_loop().run_until_complete(self.hello())
        asyncio.get_event_loop().run_forever()


    def _get_assets_list(self, zh_id):
        """
        这段代码用于查找并提取特定策略下的资产信息，
        然后将这些资产信息存储在一个列表中，
        以供进一步处理或分析。如果某些配置项不包含 "total_assets" 字段，它也会进行相应的输出。
        """
        return assets_mgr.get_assets_list(zh_id, self._users, self.configs)

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

    @staticmethod
    def extract_strategy_id(strategy_url):
        return strategy_url

    

    def _get_trading_trades(self, _is_trading):
        """
        这段代码用于从数据库中获取未读的交易记录，
        根据 `_is_trading` 参数来筛选。
        如果 `_is_trading` 为None，则引发类型错误。
        然后执行数据库查询操作，返回结果。
        如果出现异常，会将异常信息发送到Myqq并记录日志。
        """
        if _is_trading is None:
            raise TypeError("is trading is none")
        try:
            self.db_mgr._get_trading_trades(_is_trading)
        except Exception as e:
            with Myqq.Myqq() as myqq:
                myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)
            logger.warning("database might disconnected! %s" % e)

    def _do_loop(self, body_content):
        body_content = json.loads(body_content)
        if body_content["type"] == 1:
            logger.info("new msg arrived, %s" % body_content)
            if time_utils.is_off_trading_hour():
                # 非交易时间的, 暂时不处理, 等交易时间再处理
                logger.info("not trading time%s" % body_content)
                return
            try:
                self.do_socket_trade(body_content["data"])
            except Exception as e:
                with Myqq.Myqq() as myqq:
                    myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)

    async def hello(self):
        while 1:
            try:
                async with websockets.connect(
                        'ws://127.0.0.1:4000') as websocket:
                    logger.info("ws connected...")
                    with Myqq.Myqq() as myqq:
                        myqq.send_suc(__file__, inspect.stack()[0][0].f_code.co_name, "connected to ws")
                    while True:
                        try:
                            body_content = await websocket.recv()
                            self._do_loop(body_content)
                        except websockets.WebSocketException.ConnectionClosed as e:
                            await websocket.close()  # Close the WebSocket connection
                            logger.info("WebSocket disconnected")
                            with Myqq.Myqq() as myqq:
                                myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name,
                                                    "WebSocket disconnected")
                            break
                        except Exception as e:
                            with Myqq.Myqq() as myqq:
                                myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, str(e))
                            break
            except Exception as e:
                # disconnect
                with Myqq.Myqq() as myqq:
                    myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)
                time.sleep(5)


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

        self.db_mgr.mark_as_read()


    def get_users(self, userid):
        return self._users[userid]
    
    def FROMOPEN_seconds():
        return time_utils.FROMOPEN_seconds()

    def _track_strategy_worker(self):
        my_result = None
        # 获取离线交易
        if time_utils.should_fetch_off_trades():
            off_trades = self._get_trading_trades(_is_trading=0)
            logger.info(off_trades)
            if len(off_trades) > 0:
                logger.info('found off trades')
                my_result = off_trades
        if my_result is None:  # 如果没有离线交易
            return
        mark_as_dones = []
        # ------------------
        for x in my_result:
            # x[3]: msgid
            my_msg_id = int(x[3])
            if x[3] in self.msg_id_set:  # 如果原来这个消息已经接受过， 那么在数据库里面更新这条消息
                mark_as_dones.append(x[1])
            view = x[0]
            logger.info(view)
            try:
                # x[2]: insert time
                transactions, zh_id, num, strategy_name = self._parse_view_string(view, float(x[2]), my_msg_id)
            except:
                continue
            logger.info('parse ok:')
            logger.info(transactions)
            logger.info('生成用户资产map...')
            assets_list = self._get_assets_list(zh_id)
            logger.info(assets_list)
            if len(assets_list) != 0:
                # todo 这里可能存在多次推送导致数据库来回改了好多次从而信息不准确
                if num > 3:
                    # 需要远程重新获取交易记录
                    logger.info('调仓数目超过4条,需要爬虫获取详细信息...')
                    self.track_strategy(zh_id, strategy_name, assets_list, my_msg_id)
                else:
                    # 直接处理数据库里面的交易记录， 这里的流程和得到socket推送应该差不多
                    logger.info('正在整理数据格式...')
                    try:
                        tran_list = self._format_transaction(transactions, assets_list)
                        logger.info(tran_list)
                        print(self._users)
                        if len(tran_list) == len(self._users):
                            for user_id in range(len(self._users)):
                                logger.info('正在处理用户%d的交易数据...' % (user_id))
                                logger.info(tran_list[user_id])
                                self.deal_trans(user_id, tran_list[user_id], zh_id, strategy_name, my_msg_id)
                    except Exception as e:
                        logger.warning(e)
                logger.info('交易分配完毕, 将数据库标记为已完成')
            else:
                logger.info('推送中没有需要跟单交易的组合, 将数据库标记为已完成')
        self.db_mgr.mark_xqp_as_done(mark_as_dones)

    def track_strategy_worker(self):
        self.db_mgr._make_mysql_connect()
        _last_time = time.time()
        while True:
            time.sleep(1)
            if time.time() - _last_time > 30:
                logger.info("keep mysql connection")
                self.db_mgr.keep_alive()
                _last_time = time.time()
            if time_utils.should_exit():
                logger.info("15:00 exit(0)")
                os.kill(os.getpid(), signal.SIGINT)
            try:
                self._track_strategy_worker()
            except Exception as e:
                with Myqq.Myqq() as myqq:
                    myqq.send_exception(__file__, inspect.stack()[0][0].f_code.co_name, e)
                try:
                    self.db_mgr.close()
                except:
                    pass
                time.sleep(5)
                self.db_mgr._make_mysql_connect()

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

    def _format_transaction(self, transactions, assets_list, **kwargs):
        tra_list = []
        for assets in assets_list:
            transactions = transactions.copy()
            kwargs['assets'] = assets
            self.project_transactions(transactions, **kwargs)
            ret = self.order_transactions_sell_first(transactions)
            copy_list = []
            for tra in ret:
                copy_list.append(tra.copy())
            tra_list.append(copy_list)
        return tra_list

    def extract_strategy_name(self, strategy_url):
        rep = self.xq_mgr.extract_strategy_name(strategy_url)
        print(rep)
        info_index = 0
        self.strategy_name = rep.json()[info_index]["name"]
        return self.strategy_name

    '''
    解压历史交易(可能有两次调仓, 每次调仓有两笔交易)
    '''
    def extract_transactions(self, history):
        return xq_parser.extract_transactions(history)

    def project_transactions(self, transactions, assets):
        xq_parser.project_transactions(transactions, assets)

    def _get_portfolio_info(self, portfolio_code):
        """
        这段代码的功能是获取指定组合（portfolio）的信息。具体功能包括：
        1. 构建请求URL：根据给定的组合代码（portfolio_code）构建用于获取组合信息的URL。
        2. 发送HTTP请求：使用Python的 requests 库发送HTTP GET请求，以获取与给定URL相关的响应。
        3. 从响应中提取组合信息：通过使用正则表达式，从HTTP响应的文本内容中提取组合信息（JSON格式数据），该信息通常包含在文本中的 "SNB.cubeInfo = " 之后，以及分号之前的部分。
        4. 解析JSON数据：尝试将提取的JSON数据解析为Python字典。如果解析失败，会引发异常。
        5. 返回组合信息：如果成功获取并解析组合信息，将其作为字典返回。
        6. 处理异常情况：如果在获取组合信息的过程中出现任何异常，会记录异常信息并等待10秒后进行重试，最多重试10次。
        此代码的主要目的是通过HTTP请求从特定URL获取组合信息，然后将其以字典形式返回。如果无法成功获取组合信息，将记录异常信息。
        """
        resp = self._get_portfolio_info(portfolio_code)
        return xq_parser.parse_portfolio_info(resp)

    def _get_portfolio_net_value(self, portfolio_code):
        """
        获取组合信息
        """
        portfolio_info = self._get_portfolio_info(portfolio_code)
        return xq_parser.get_portfolio_net_value(portfolio_info)
