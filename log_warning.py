

def log_warning(logger, trade_cmd, now, msg):
    logger.warning(
        "策略 [%s] 指令(股票: %s 动作: %s 数量: %s 价格: %s)超时，指令产生时间: %s 当前时间: %s, %s , 被丢弃",
        trade_cmd["strategy_name"],
        trade_cmd["stock_code"],
        trade_cmd["action"],
        trade_cmd["amount"],
        trade_cmd["price"],
        trade_cmd["datetime"],
        now,
        msg
    )
    
def log_error(logger, trade_cmd, trader_name, actual_price, err_msg):
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
def log_info(logger, trade_cmd, actual_price, response):
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