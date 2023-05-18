# -*- coding: utf-8 -*-
"""
author: lynx
email: lynxluu@gmail.com
create_dt: 2022/12/08 20:16
describe: 
"""
from typing import Tuple, List

from czsc.signals.tas import update_ma_cache

try:
    import talib as ta
except:
    from czsc.utils import ta
import numpy as np
from collections import OrderedDict
from czsc import CZSC, signals
from czsc.data import TsDataCache, get_symbols
from czsc.objects import Freq, Operate, Signal, Factor, Event
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar
from czsc.utils import get_sub_elements

def update_ma_cache1(cat: CzscAdvancedTrader, freq: str,
                     ma_params: Tuple = (5, 10, 20, 55, 110, 220)):
    """更新某个级别的均线缓存

    :param cat: 交易对象
    :param freq: 指定周期
    :param ma_params: 均线参数
    :return:
    """
    assert freq in cat.freqs, f"{freq} 不在 {cat.freqs} 中"
    cache_key = f"{freq}均线"
    ma_cache = cat.cache.get(cache_key, {})
    ma_cache['update_dt'] = cat.end_dt
    close = np.array([x.close for x in cat.kas[freq].bars_raw])
    ma_cache['close'] = close
    for t in ma_params:
        ma_cache[f"MA{t}"] = ta.MA(close, timeperiod=t,matype = 0)
    cat.cache[cache_key] = ma_cache


def double_ma(c: CZSC, di: int = 1, ma_type='SMA', ma_seq=(5, 10)) -> OrderedDict:
    """双均线相关信号

    **信号逻辑**
    dif=ma1-ma2
    dif 从负变正，多头； 从正变负，空头

    有效信号列表：
    60分钟_D1K_双均线5-10_金叉_多头_任意_0
    60分钟_D1K_双均线5-10_死叉_空头_任意_0
    """
    assert len(ma_seq) == 2 and ma_seq[0] < ma_seq[1]
    # update_ma_cache函数返回的是 cache_key = f"{ma_type.upper()}{timeperiod}",通过调试发现key1,key2返回了空，改写
    # key1 = update_ma_cache(c, ma_type,ma_seq[0])
    # key2 = update_ma_cache(c, ma_type, ma_seq[1])
    key1,key2 = f"{ma_type}{ma_seq[0]}",f"{ma_type}{ma_seq[1]}"
    print(key1, key2)

    s = OrderedDict()
    k1,k2,k3 = f"{c.freq.value}_D{di}K_双均线{ma_seq[0]}-{ma_seq[1]}".split("_")
    v1, v2 = '任意', '任意'

    # n = 11
    # bars = get_sub_elements(c.bars_raw, di=di, n=n)

    bars = c.bars_raw
    n = len(bars)
    dif = [0] * n
    #  SMA5前4个是NONE，SMA10，前9个是NONE，要解决这个问题
    for i in range(n):
        if bars[i].cache:
            # print(bars[i].cache)
            dif[i] = bars[i].cache[key1] - bars[i].cache[key2]
            # print(i,dif[i])
    if len(dif) > 0:
        if (dif[-1] > 0 and dif[-2] <= 0):
            v1,v2 = "金叉","多头"
        elif (dif[-1] < 0 and dif[-2] >= 0):
            v1,v2 = "死叉","空头"

    x1 = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3='任意')
    s[x1.key] = x1.value
    return s

# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """60分钟双均线择时"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        signals.update_ma_cache(cat.kas["60分钟"], ma_type='SMA', timeperiod=5)
        signals.update_ma_cache(cat.kas["60分钟"], ma_type='SMA', timeperiod=10)
        double_ma(cat.kas['60分钟'])
        # double_ma(cat.kas['60分钟'], ma_type='SMA', ma_seq=(5, 10))
        # signals.tas_double_ma_V221203(cat.kas['60分钟'])
        # signals.update_macd_cache(cat.kas['60分钟'])
        # s.update(signals.tas_macd_bc_V221201(cat.kas['60分钟'], di=1, n=3, m=10))
        # s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=1, key='macd'))
        # s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=5, key='macd'))
        #
        # signals.update_macd_cache(cat.kas['日线'])
        # s.update(signals.tas.tas_macd_power_V221108(cat.kas['日线'], di=1))
        #
        # signals.update_macd_cache(cat.kas['周线'])
        # s.update(signals.tas.tas_macd_power_V221108(cat.kas['周线'], di=1))
        # s.update(signals.tas_macd_base_V221028(cat.kas['周线'], di=1, key='macd'))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO,
              signals_not=[Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                           # Signal("60分钟_D1N3M10_MACD背驰_顶部_任意_任意_0")
                           ],
              factors=[
                  Factor(name="60分钟双均线金叉", signals_all=[
                      Signal("交易_0935_1450_是_任意_任意_0"),
                      # Signal("60分钟_D1K_MACD_多头_任意_任意_0"),
                      Signal("60分钟_D1K_双均线5-10_金叉_多头_任意_0"),
                  ]),
              ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[Signal("交易_0935_1450_是_任意_任意_0")],
              signals_not=[Signal("15分钟_D1K_ZDT_跌停_任意_任意_0")],
              factors=[
                  Factor(name="60分钟双均线死叉", signals_all=[
                      Signal("60分钟_D1K_双均线5-10_死叉_多头_任意_0"),
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
dc = TsDataCache(r"C:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train20')

# 执行结果路径
results_path = r"C:\ts_data_czsc\f60_double_ma"

# 【必须】策略回测参数设置
dummy_params = {
    "symbols": symbols,  # 回测使用的标的列表
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20200101",  # 策略回测开始时间
    "edt": "20221231",  # 策略回测结束时间
}
# 策略回放参数设置【可选】
replay_params = {
    "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20180101",  # 策略回放开始时间
    "edt": "20220101",  # 策略回放结束时间
}

# 信号检查参数设置【可选】
check_params = {
    "symbol": "000001.SZ#E",    # 交易品种，格式为 {ts_code}#{asset}
    "sdt": "20180101",          # 开始时间
    "edt": "20220101",          # 结束时间
}
