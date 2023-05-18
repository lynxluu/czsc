# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/11/27 20:16
describe: 
"""
import numpy as np
from collections import OrderedDict
from czsc import CZSC, signals
from czsc.data import TsDataCache, get_symbols
from czsc.objects import Freq, Operate, Signal, Factor, Event
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar
from czsc.utils import get_sub_elements


# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """60分钟MACD择时"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        signals.update_macd_cache(cat.kas['60分钟'])
        s.update(signals.tas_macd_bc_V221201(cat.kas['60分钟'], di=1, n=3, m=10))
        s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=1, key='macd'))
        s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=5, key='macd'))

        signals.update_macd_cache(cat.kas['日线'])
        s.update(signals.tas.tas_macd_power_V221108(cat.kas['日线'], di=1))

        signals.update_macd_cache(cat.kas['周线'])
        s.update(signals.tas.tas_macd_power_V221108(cat.kas['周线'], di=1))
        s.update(signals.tas_macd_base_V221028(cat.kas['周线'], di=1, key='macd'))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO,
              signals_not=[Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                           Signal("60分钟_D1N3M10_MACD背驰_顶部_任意_任意_0")],
              factors=[
                  Factor(name="60分钟MACD金叉", signals_all=[
                      Signal("交易_0935_1450_是_任意_任意_0"),
                      Signal("60分钟_D1K_MACD_多头_任意_任意_0"),
                      Signal("60分钟_D5K_MACD_空头_任意_任意_0"),
                      Signal("60分钟_D1N3M10_MACD背驰_底部_任意_任意_0"),
                  ]),
              ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[Signal("交易_0935_1450_是_任意_任意_0")],
              signals_not=[Signal("15分钟_D1K_ZDT_跌停_任意_任意_0")],
              factors=[
                  Factor(name="60分钟顶背驰", signals_all=[
                      Signal("60分钟_D1N3M10_MACD背驰_顶部_任意_任意_0"),
                  ]),

                  Factor(name="60分钟MACD死叉", signals_all=[
                      Signal("60分钟_D1K_MACD_空头_任意_任意_0"),
                  ]),
              ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['60分钟', '日线', '周线'],
        "get_signals": get_signals,
        "long_pos": long_pos,
        "long_events": long_events,
        "short_pos": None,
        "short_events": None,
    }
    return tactic


# 定义命令行接口的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"C:\ts_data_czsc")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train')

# 执行结果路径
results_path = r"C:\ts_data_czsc\f60_MACD"

# 策略回放参数设置【可选】
replay_params = {
    "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20180101",  # 策略回放开始时间
    "edt": "20220101",  # 策略回放结束时间
}
