from datetime import datetime
import pytz

def FROMOPEN_seconds():
    """
    用于判断当前时间处于交易日的哪个时间段，
    并返回距离该时间段开市时间的秒数。如果不在交易时间内，它会返回0。
    """
    now = datetime.now(pytz.timezone('Asia/Chongqing'))

    OPEN_AM = datetime.strptime('%d-%d-%d 09:30:00 +0800' % (now.year, now.month, now.day), '%Y-%m-%d %H:%M:%S %z')
    CLOSE_AM = datetime.strptime('%d-%d-%d 11:30:00 +0800' % (now.year, now.month, now.day), '%Y-%m-%d %H:%M:%S %z')

    OPEN_PM = datetime.strptime('%d-%d-%d 13:00:00 +0800' % (now.year, now.month, now.day), '%Y-%m-%d %H:%M:%S %z')
    CLOSE_PM = datetime.strptime('%d-%d-%d 15:00:00 +0800' % (now.year, now.month, now.day), '%Y-%m-%d %H:%M:%S %z')

    if now.timestamp() < OPEN_AM.timestamp():
        return 0
    # 早上
    if CLOSE_AM.timestamp() >= now.timestamp() >= OPEN_AM.timestamp():
        return int((now.timestamp() - OPEN_AM.timestamp()) )
    # 中午
    if OPEN_PM.timestamp() >= now.timestamp() >= CLOSE_AM.timestamp():
        return int((CLOSE_AM.timestamp() - OPEN_AM.timestamp()) )
    # 下午
    if CLOSE_PM.timestamp() >= now.timestamp() >= OPEN_PM.timestamp():
        return int((now.timestamp() - OPEN_PM.timestamp()) ) + 120*60
    if now.timestamp() > CLOSE_PM.timestamp():
        return 240*60
    return 0


def is_workday():
    now = datetime.now(pytz.timezone('Asia/Chongqing'))
    # 获取当前日期的星期几（星期一是0，星期日是6）
    weekday = now.weekday()
    
    # 检查是否是星期一至星期五
    if 0 <= weekday < 5:
        return True
    else:
        return False


def should_exit():
    return datetime.now(pytz.timezone('Asia/Chongqing')).hour >= 15

def is_off_trading_hour():
    sec = FROMOPEN_seconds()
    return sec == 240*60 or sec == 120*60 or sec == 0 or not is_workday()

def should_fetch_off_trades():
    return 0 < FROMOPEN_seconds() <= 20 or 120 * 60 < FROMOPEN_seconds() <= 120 * 60 + 20
