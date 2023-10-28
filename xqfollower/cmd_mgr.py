
from datetime import datetime
import hashlib

from .log import logger
from .log_util import *
from typing import Optional, Tuple, Union

def execute_trade_cmd(trade_cmd) -> Optional[Tuple[dict, str, float]]:
    now = datetime.now()
    # 使用字典解构来获取字段
    action = trade_cmd["action"]
    stock_code = trade_cmd["stock_code"]
    msg_id = trade_cmd["msg_id"]
    strategy_name = trade_cmd["strategy_name"]
    price = trade_cmd["price"]
    amount = trade_cmd["amount"]

    if not _is_number(price) or price <= 0:
        logger.warning(log_warning(trade_cmd, now, "!price"))
        return None, None, None

    if amount <= 0:
        logger.warning(log_warning(trade_cmd, now, "!amount"))
        return None, None, None

    # 删除价格作为hash的来源， 因为价格是实时获取的，不是推送的
    data = f"{action},{stock_code},{msg_id},{strategy_name}"  # 要进行加密的数据
    my_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
    args = {
        "security": stock_code,
        "price": price,
        "amount": amount,
        "hash": my_hash,
    }
    return args, action, price

def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def build_trade_cmd(userid, transaction, strategy, name, msg_id):
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
    return trade_cmd