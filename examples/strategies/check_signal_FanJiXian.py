# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/10/31 22:27
describe: 专用于信号检查的策略
"""
import talib as ta
import pandas as pd
from collections import OrderedDict
from typing import List
from loguru import logger
from czsc import CZSC, signals, RawBar
from czsc.data import TsDataCache, get_symbols
from czsc.utils import get_sub_elements
from czsc.objects import Freq, Operate, Signal, Factor, Event
from czsc.traders import CzscAdvancedTrader


# 定义信号函数
# ----------------------------------------------------------------------------------------------------------------------
def jcc_fan_ji_xian_v221121(c: CZSC, di=1) -> OrderedDict:
    """反击线；贡献者：lynxluu

    **信号逻辑：**

    1. 反击线分两种，看涨反击线和看跌反击线，共同特点是两根K线收盘价接近;
    2. 看涨反击线，下降趋势，先阴线，后大幅低开收阳线;
    3. 看跌反击线，上升趋势，先阳线，后大幅高开收阴线;

    **信号列表：**

    * Signal('15分钟_D1T_反击线_满足_看涨反击线_任意_0')
    * Signal('15分钟_D1T_反击线_满足_看跌反击线_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di根K线 取倒数三根k线
    :return: 反击线识别结果
    """

    k1, k2, k3 = f"{c.freq.value}_D{di}_反击线".split('_')

    # 取三根K线 判断是否满足基础形态
    bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=3)
    bar1, bar2, bar3 = bars

    # 取前20根K线，计算区间高度gap
    if len(c.bars_raw) > 20 + di:
        left_bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=20)
        left_max = max([x.high for x in left_bars])
        left_min = min([x.low for x in left_bars])
        gap = left_max - left_min

    v1 = "其他"
    # 用来比较的bar2实体不能等于0，避免0做除数
    if bar2.close != bar2.open:
        # 大幅高/低开 高/低开幅度除以bar2实体大于1； x1 >= 1
        # 收盘价接近 bar2和bar3的收盘价差值 除以bar2实体小于0.1； x2 <= 0.1
        # bar2实体除以前20根K线的区间的比值，此值影响比较大；x3 >= 0.02
        # bar3上影线除以bar2实体的比值, 看涨时上影线不宜过大； x4 < 1
        # bar3下影线除以bar2实体的比值，看跌时下影线不宜过大； x4a < 1
        bar2h = abs(bar2.close - bar2.open)
        x1 = abs(bar3.open - bar2.close) / bar2h
        x2 = abs(bar3.close - bar2.close) / bar2h
        x3 = bar2h / gap
        x4 = (bar3.high - max(bar3.open, bar3.close)) / bar2h
        x4a = (min(bar3.open, bar3.close) - bar3.low) / bar2h
        if x1 >= 1 and x2 <= 0.1 and x3 >= 0.02:
            v1 = "满足"

    # 看涨：下降趋势； bar2阴线； bar3低开；
    # 看跌：上升趋势； bar2阳线； bar3高开；
    v2 = "其他"
    if bar1.low <= left_min + 0.25 * gap and bar1.close > bar2.close \
            and bar2.open > bar2.close > bar3.open: # and x4 < 1:
        v2 = "看涨反击线"

    elif bar1.high >= left_max - 0.25 * gap and bar2.close > bar1.close \
            and bar3.open > bar2.close > bar2.open: # and x4a < 1:
        v2 = "看跌反击线"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------
def trader_strategy(symbol):
    """择时策略"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(jcc_fan_ji_xian_v221121(cat.kas['60分钟'], di=1))
        return s

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['60分钟', '日线'],
        "get_signals": get_signals,
    }
    return tactic


# 定义命令行接口【信号检查】的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"D:\ts_data")

# # 执行结果路径 不起作用
# results_path = r"D:\ts_data\check_signal_FanJiXian"

# 信号检查参数设置【可选】
# check_params = {
#     "symbol": "000001.SZ#E",    # 交易品种，格式为 {ts_code}#{asset}
#     "sdt": "20180101",          # 开始时间
#     "edt": "20220101",          # 结束时间
# }


check_params = {
    "symbol": "300001.SZ#E",  # 交易品种，格式为 {ts_code}#{asset}
    "sdt": "20150101",  # 开始时间
    "edt": "20220101",  # 结束时间
}
