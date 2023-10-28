from numbers import Number
from .log import logger

def calculate_total_assets(strategy_id, configs, net_value):
    # 创建一个新的配置列表
    new_configs = []
    # 遍历原始的配置列表
    for conf in configs:
        # 尝试执行以下操作
        try:
            # 检查conf["ZH"]和strategy_id是否是同一类型
            if not isinstance(conf["ZH"], type(strategy_id)):
                raise TypeError(f"conf['ZH'] and strategy_id must be the same type, got {type(conf['ZH'])} and {type(strategy_id)}")
            # 如果conf["ZH"]等于strategy_id，并且conf中没有"total_assets"键或其值为空或为0
            if conf["ZH"] == strategy_id and (not conf.get("total_assets") or conf["total_assets"] == 0):
                # 计算总资产
                conf["total_assets"] = float(conf["cap0"]) * net_value
                # 打印日志信息
                logger.info(conf)
                # 检查总资产是否是数字类型
                if not isinstance(conf["total_assets"], Number):
                    raise TypeError(f"input assets type must be number(int, float), got {type(conf['total_assets'])}")
                # 检查总资产是否大于等于1000元
                if conf["total_assets"] < 1000.0:
                    raise ValueError(f"雪球总资产不能小于1000元，当前预设值 {conf['total_assets']}")
            # 将修改后的conf添加到新的配置列表中
            new_configs.append(conf)
        # 如果出现异常，打印错误信息，并继续循环
        except Exception as e:
            logger.error(e)
            continue
    # 返回新的配置列表
    return new_configs

def get_assets_list(zh_id, user_domains, configs):
    """
    这段代码用于查找并提取特定策略下的资产信息，
    然后将这些资产信息存储在一个列表中，
    以供进一步处理或分析。如果某些配置项不包含 "total_assets" 字段，它也会进行相应的输出。
    """
    reval = []
    for idx, domain in enumerate(user_domains):
        for conf in configs:
            if conf["ZH"] == zh_id and conf['host'] == domain:
                if "total_assets" not in conf:
                    logger.info(f'Not found in {idx}, {domain}, {zh_id}')
                else:
                    logger.info(f'Found in {idx}, {domain}, {zh_id}, {conf["total_assets"]}')
                    reval.append(conf["total_assets"])
                break

    return reval
