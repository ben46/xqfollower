import re
import json
from .log import logger
from datetime import datetime

def parse_portfolio_info(resp):
    if resp is None:
            return
    match_info = re.search(r"(?<=SNB.cubeInfo = ).*(?=;\n)", resp.text)
    if match_info is None:
        raise Exception("cant get portfolio info, portfolio url : {}".format(portfolio_code))
    try:
        portfolio_info = json.loads(match_info.group())
    except Exception as e:
        raise Exception("get portfolio info error: {}".format(e))
    return portfolio_info

def get_portfolio_net_value(portfolio_info):
    return portfolio_info["net_value"]

# noinspection PyMethodOverriding
def none_to_zero(data):
    if data is None:
        return 0
    return data

# noinspection PyMethodOverriding
def project_transactions(transactions, assets):
    for transaction in transactions:
        # print(transaction)
        weight_diff = none_to_zero(transaction["weight"]) - none_to_zero(
            transaction["prev_weight"]
        )
        if transaction["price"] == 0:
            logger.info("价格为0,跳过这个交易, %s" % transaction)
            continue
        initial_amount = abs(weight_diff) / 100 * assets / transaction["price"]
        transaction["datetime"] = datetime.fromtimestamp(
            transaction["created_at"] // 1000
        )
        transaction["stock_code"] = transaction["stock_symbol"].lower()
        transaction["action"] = "buy" if weight_diff > 0 else "sell"
        if transaction['stock_name'].find('转') > 0 and transaction['stock_code'][-6:].find('1') == 0:
            __temp_amount = int(round(initial_amount, -1))
            transaction["amount"] = __temp_amount
        else:
            transaction["amount"] = int(round(initial_amount, -2))
        # print(transaction["action"],transaction["stock_code"], transaction["amount"])

'''
解压历史交易(可能有两次调仓, 每次调仓有两笔交易)
'''
def extract_transactions(history):
    if history["count"] <= 0:
        return []
    rebalancing_index = 0
    raw_transactions = history["list"][rebalancing_index]["rebalancing_histories"]
    transactions = []
    for transaction in raw_transactions:
        # print(transaction)
        if transaction["price"] is None:
            # logger.info("该笔交易无法获取价格，疑似未成交，跳过。交易详情: %s", transaction)
            continue
        transactions.append(transaction)

    if len(transactions) == 0:
        # logger.info("len =0, get index 1")
        rebalancing_index = 1
        raw_transactions = history["list"][rebalancing_index]["rebalancing_histories"]
        for transaction in raw_transactions:
            # print(transaction)
            if transaction["price"] is None:
                # logger.info("该笔交易无法获取价格，疑似未成交，跳过。交易详情: %s", transaction)
                continue
            transactions.append(transaction)
        # print(transactions)
    return transactions

def order_transactions_sell_first(transactions):
    # 调整调仓记录的顺序为先卖再买
    sell_first_transactions = []
    for transaction in transactions:
        if transaction["action"] == "sell":
            sell_first_transactions.insert(0, transaction)
        else:
            sell_first_transactions.append(transaction)
    return sell_first_transactions

def parse_strategy_transaction(self, history, assets_list, **kwargs):
    tra_list = []
    for assets in assets_list:
        transactions = self.extract_transactions(history)
        kwargs['assets'] = assets
        project_transactions(transactions, **kwargs)
        ret = order_transactions_sell_first(transactions)
        copy_list = []
        for tra in ret:
            copy_list.append(tra.copy())
        tra_list.append(copy_list)
    return tra_list
