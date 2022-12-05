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


def tas_macd_bc_V221108(c: CZSC, di: int = 1) -> OrderedDict:
    """获取倒数第i根K线的MACD背驰辅助信号

    底背弛辅助条件：
    1）最近10根K线的MACD为绿柱；
    2）最近10根K线的最低点 == 最近3根K线的最低点；
    3）最近10根K线的MACD绿柱最小值 < 最近3根K线的MACD绿柱最小值

    :param c: CZSC对象
    :param di: 定位K
    :return:
    """
    k1, k2, k3 = str(c.freq.value), f"D{di}K", "MACD背驰辅助"

    bars = get_sub_elements(c.bars_raw, di=1, n=10)
    macd = [bar.cache['MACD']['macd'] for bar in bars]
    d_c1 = min([x.low for x in bars[-3:]]) == min([x.low for x in bars])
    g_c1 = max([x.high for x in bars[-3:]]) == max([x.high for x in bars])

    if d_c1 and min(macd[-3:]) > min(macd[-10:]):
        v1 = "底部"
    elif g_c1 and max(macd[-3:]) < max(macd[-10:]):
        v1 = "顶部"
    else:
        v1 = "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s


# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """60分钟MACD择时"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        signals.update_macd_cache(cat.kas['60分钟'])
        s.update(tas_macd_bc_V221108(cat.kas['60分钟'], di=1))
        s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=1, key='macd'))

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
            Factor(name="低吸", signals_all=[
                Signal("交易_0935_1450_是_任意_任意_0"),
                Signal("60分钟_D1K_MACD_多头_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                Signal("日线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD_任意_向上_任意_0"),
                Signal("60分钟_D1K_MACD背驰辅助_顶部_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[
                  Signal("交易_0935_1450_是_任意_任意_0"),
                  Signal("15分钟_D1K_ZDT_其他_任意_任意_0"),
              ],
              factors=[
                  Factor(name="60分钟顶背驰", signals_all=[
                      Signal("60分钟_D1K_MACD背驰辅助_顶部_任意_任意_0"),
                  ]),

                  Factor(name="持有资金", signals_all=[
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
dc = TsDataCache(r"D:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train')

# 执行结果路径
results_path = r"D:\ts_data\f60_MACD"

# 策略回放参数设置【可选】
replay_params = {
    "symbol": "300724.SZ#E",  # 回放交易品种
    # "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20210101",  # 策略回放开始时间
    "edt": "20221128",  # 策略回放结束时间
}
