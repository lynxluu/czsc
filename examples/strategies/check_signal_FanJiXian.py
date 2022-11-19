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
    """反击线；贡献者：lynx

    **信号逻辑：**

    1. 反击线分两种，看涨反击线和看跌反击线，共同特点是两根K线收盘价接近;
    2. 看涨反击线，下降趋势，先阴线，后大幅低开收阳线;
    3. 看跌反击线，上升趋势，先阳线，后大幅高开收阴线;

    **信号列表：**

    * Signal('15分钟_D1T_反击线_满足_看涨_任意_0')
    * Signal('15分钟_D1T_反击线_满足_看跌_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di根K线 取倒数三根k线
    :return: 反击线识别结果
    """

    k1, k2, k3 = f"{c.freq.value}_D{di}_反击线".split('_')

    # 取三根K线 判断是否满足基础形态
    bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=3)
    bar1, bar2, bar3 = bars


    # 大幅高/低开 高/低开幅度除以bar2实体大于1； x1 = abs(bar3.open -bar2.close)/abs(bar2.close-bar2.open) >= 1
    # 收盘价接近 bar2和bar3的收盘价差值 除以bar2实体小于0.1； x2 = abs(bar3.close-bar2.close)/abs(bar2.close-bar2.open) <= 0.1
    v1 = "其他"
    # 用来比较的bar2实体不能等于0，避免0做除数
    if bar2.close != bar2.open:
        x1 = abs(bar3.open - bar2.close) / abs(bar2.close - bar2.open)
        x2 = abs(bar3.close - bar2.close) / abs(bar2.close - bar2.open)
        if x1 >= 1 and x2 <= 0.1:
            v1 = "满足"

    # 趋势用两根K线的收盘价来判断不准确，要增加判断方法
    # 看涨：下降趋势 bar1.close > bar2.close； bar2阴线 bar2.open > bar2.close； bar3低开 bar2.close > bar3.open；
    # 看跌：上升趋势 bar2.close > bar1.close； bar2阳线 bar2.close > bar2.open； bar3高开 bar3.open > bar2.close；
    v2 = "其他"
    if v1 == "满足":
        if bar1.close > bar2.close and bar2.open > bar2.close > bar3.open:
            v2 = "看涨"
        elif bar2.close > bar1.close and bar3.open > bar2.close > bar2.open:
            v2 = "看跌"

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
