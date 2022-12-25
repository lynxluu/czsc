# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/10/31 22:27
describe: 专用于信号检查的策略
"""
import talib as ta
import numpy as np
import pandas as pd
from collections import OrderedDict
from typing import List
from loguru import logger
from czsc import CZSC, signals, RawBar, Direction
from czsc.data import TsDataCache, get_symbols
from czsc.utils import get_sub_elements, single_linear, fast_slow_cross
from czsc.objects import Freq, Operate, Signal, Factor, Event, BI
from czsc.objects import PositionLong, PositionShort, RawBar
from czsc.traders import CzscAdvancedTrader
from czsc.signals.tas import tas_macd_second_bs_V221201

# 定义信号函数
# ----------------------------------------------------------------------------------------------------------------------
def macd_bs2_v2(cat: CzscAdvancedTrader, freq: str):
    """MACD金叉死叉判断第二买卖点

    原理：最近一次交叉为死叉，DEA大于0，且前面三次死叉都在零轴下方，那么二买即将出现；二卖反之。

    完全分类：
        Signal('15分钟_MACD_BS2V2_二卖_任意_任意_0'),
        Signal('15分钟_MACD_BS2V2_二买_任意_任意_0')
    :return:
    """

    s = OrderedDict()
    cache_key = f"{freq}MACD"
    cache = cat.cache[cache_key]
    assert cache and cache['update_dt'] == cat.end_dt
    cross = cache['cross']
    macd = cache['macd']
    up = [x for x in cross if x['类型'] == "金叉"]
    dn = [x for x in cross if x['类型'] == "死叉"]

    v1 = "其他"

    b2_con1 = len(cross) > 3 and cross[-1]['类型'] == '死叉' and cross[-1]['慢线'] > 0
    b2_con2 = len(dn) > 3 and dn[-3]['慢线'] < 0 and dn[-2]['慢线'] < 0 and dn[-3]['慢线'] < 0
    b2_con3 = len(macd) > 10 and macd[-1] > macd[-2]
    if b2_con1 and b2_con2 and b2_con3:
        v1 = "二买"

    s2_con1 = len(cross) > 3 and cross[-1]['类型'] == '金叉' and cross[-1]['慢线'] < 0
    s2_con2 = len(up) > 3 and up[-3]['慢线'] > 0 and up[-2]['慢线'] > 0 and up[-3]['慢线'] > 0
    s2_con3 = len(macd) > 10 and macd[-1] < macd[-2]
    if s2_con1 and s2_con2 and s2_con3:
        v1 = "二卖"

    signal = Signal(k1=freq, k2="MACD", k3="BS2V2", v1=v1)
    s[signal.key] = signal.value
    return s


# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------
def trader_strategy(symbol):
    """择时策略"""

    # 定义交易周期
    freq: Freq = '60分钟'

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        signals.update_macd_cache(cat.kas['15分钟'])
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        signals.update_macd_cache(cat.kas[freq])
        s.update(tas_macd_second_bs_V221201(cat.kas[freq], di=1))
        # s.update(macd_bs2_v2(cat.kas['15分钟'], freq='15分钟'))


        signals.update_macd_cache(cat.kas['日线'])
        s.update(signals.tas.tas_macd_power_V221108(cat.kas['日线'], di=1))

        signals.update_macd_cache(cat.kas['周线'])
        s.update(signals.tas.tas_macd_power_V221108(cat.kas['周线'], di=1))
        s.update(signals.tas_macd_base_V221028(cat.kas['周线'], di=1, key='macd'))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸",
                   signals_all=[
                Signal("交易_0935_1450_是_任意_任意_0"),
                # Signal('15分钟_MACD_BS2V2_二买_任意_任意_0'),
            ],
                   signals_any=[
                Signal(f'{freq}_D1MACD_BS2_二买_金叉_任意_0'),
                Signal(f'{freq}_D1MACD_BS2_二买_死叉_任意_0'),],
                   signals_not=[
                Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                Signal("日线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD_任意_向上_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[
                  Signal("交易_0935_1450_是_任意_任意_0"),
                  Signal("15分钟_D1K_ZDT_其他_任意_任意_0"),
              ],
              factors=[
                  Factor(name="15分钟顶背驰", signals_all=[
                      # Signal('15分钟_MACD_BS2V2_二卖_任意_任意_0'),
                      Signal(f'{freq}_D1MACD_BS2_二卖_金叉_任意_0'),
                      Signal(f'{freq}_D1MACD_BS2_二卖_死叉_任意_0')
                  ]),
              ]),
    ]

    # tactic = {
    #     "base_freq": '15分钟',
    #     "freqs": ['60分钟', '日线'],
    #     "get_signals": get_signals,
    # }
    tactic = {
        "base_freq": '15分钟',
        "freqs": ['30分钟', '日线', '周线'],
        "get_signals": get_signals,
        "long_pos": long_pos,
        "long_events": long_events,
        "short_pos": None,
        "short_events": None,
    }

    return tactic


# 定义命令行接口【信号检查】的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"D:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train')

# 执行结果路径
results_path = r"D:\ts_data\macd_2bs"

# 信号检查参数
# check_params = {
#     "symbol": "002234.SZ#E",  # 交易品种，格式为 {ts_code}#{asset}
#     # "symbol": "000001.SZ#E",    # 交易品种，格式为 {ts_code}#{asset}
#     "sdt": "20150101",  # 开始时间
#     "edt": "20221218",  # 结束时间
# }

# 回放参数
replay_params = {
    "symbol": "002234.SZ#E",  # 交易品种，格式为 {ts_code}#{asset}
    # "symbol": "000001.SZ#E",    # 交易品种，格式为 {ts_code}#{asset}
    "sdt": "20150101",  # 开始时间
    "mdt": "20210101",  # 策略回放开始时间
    "edt": "20221218",  # 结束时间
}
