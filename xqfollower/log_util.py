def log_warning(trade_cmd, now, msg):
    return "策略 [%s] 指令(\n  股票: %s \n  动作: %s \n  数量: %s \n  价格: %s \n  指令产生: %s \n  打印时间: %s, \n  错误信息: %s , 被丢弃"%(
        trade_cmd["strategy_name"],
        trade_cmd["stock_code"],
        trade_cmd["action"],
        trade_cmd["amount"],
        trade_cmd["price"],
        trade_cmd["datetime"],
        now,
        msg
    )
    
def log_error(trade_cmd, trader_name, actual_price, err_msg):
    return "%s 执行 策略 [%s] 指令(\n  股票: %s \n  动作: %s \n  数量: %s \n  价格: %s \n  指令产生: %s) 失败, \n  错误信息: %s" %(
        trader_name,
        trade_cmd["strategy_name"],
        trade_cmd["stock_code"],
        trade_cmd["action"],
        trade_cmd["amount"],
        actual_price,
        trade_cmd["datetime"],
        err_msg,
    )
    
def log_info( trade_cmd, actual_price, response):
    return "策略 [%s] 指令(\n  股票: %s \n  动作: %s \n  数量: %s \n  价格: %s \n  指令产生: %s) \n  执行成功, 返回: %s"%(
        trade_cmd["strategy_name"],
        trade_cmd["stock_code"],
        trade_cmd["action"],
        trade_cmd["amount"],
        actual_price,
        trade_cmd["datetime"],
        response,
    )
    
def log_trade(trade_cmd, name):
    return "策略 [%s] 发送指令到交易队列, \n  股票: %s 动作: %s \n  数量: %s \n  价格: %s \n  信号产生: %s"%(
        name,
        trade_cmd["stock_code"],
        trade_cmd["action"],
        trade_cmd["amount"],
        trade_cmd["price"],
        trade_cmd["datetime"],
    )