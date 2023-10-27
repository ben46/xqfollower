from numbers import Number
from .log import logger

def calculate_total_assets(strategy_id, configs, net_value):
    for conf in configs:
        if conf["ZH"] == strategy_id and ("total_assets" not in conf or conf["total_assets"] is None or conf["total_assets"] == 0):
                conf["total_assets"] = float(conf["cap0"]) * net_value
                logger.info(conf)
                if not isinstance(conf["total_assets"], Number):
                    raise TypeError("input assets type must be number(int, float)")
                if conf["total_assets"] < 1000.0:
                    raise ValueError("雪球总资产不能小于1000元，当前预设值 {}".format(conf["total_assets"]))
    return configs

def get_assets_list( zh_id, users,configs ):
    """
    这段代码用于查找并提取特定策略下的资产信息，
    然后将这些资产信息存储在一个列表中，
    以供进一步处理或分析。如果某些配置项不包含 "total_assets" 字段，它也会进行相应的输出。
    """
    reval = []
    idx=-1
    for user in users:
        idx+=1
        for conf in configs:
            if conf["ZH"] == zh_id and conf['host'] == user.get_domain():
                print(conf)
                if "total_assets" not in conf:
                    print("not here")
                    print(conf)
                else:
                    logger.info(f'{idx}, {user.get_domain()}, {zh_id}, {conf["total_assets"]}')
                    reval.append(conf["total_assets"])
                break
    return reval
