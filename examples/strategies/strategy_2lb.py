# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/11/19 19:03
describe: A股隔夜择时策略

基本原理：
1. 两连板开板就买入
2. 持有到第一个5日线多头信号
"""
from collections import OrderedDict
from czsc import signals
from czsc.data import TsDataCache, get_symbols
from czsc.objects import Freq, Operate, Signal, Factor, Event
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar


# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """两连板择时策略"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='开多', span=('0935', '1450')))
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='平多', span=('0935', '1450')))

        s.update(signals.bar_zdt_V221111(cat, '日线', di=1))
        s.update(signals.bar_zdt_V221111(cat, '日线', di=2))
        s.update(signals.bar_zdt_V221111(cat, '日线', di=3))
        s.update(signals.bar_zdt_V221111(cat, '日线', di=4))

        # 均线信号
        signals.update_ma_cache(cat.kas['日线'], ma_type='SMA', timeperiod=5)
        s.update(signals.tas_ma_base_V221101(cat.kas['日线'], di=1, key='SMA5'))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    long_events = [
        Event(name="开多", operate=Operate.LO,
              signals_not=[Signal('日线_D1K_涨跌停_涨停_任意_任意_0'),
                           Signal('日线_D4K_涨跌停_涨停_任意_任意_0')],
              factors=[
                  Factor(name="两连板开板", signals_all=[
                      Signal("开多_0935_1450_是_任意_任意_0"),
                      Signal('日线_D2K_涨跌停_涨停_任意_任意_0'),
                      Signal('日线_D3K_涨跌停_涨停_任意_任意_0'),
                  ]),
              ]),

        Event(name="平多", operate=Operate.LE,
              signals_not=[Signal('日线_D1K_涨跌停_跌停_任意_任意_0')],
              factors=[
                  Factor(name="SMA5多头", signals_all=[
                      Signal("日线_D1K_SMA5_多头_任意_任意_0"),
                  ]),
              ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,
    }

    return tactic


# 定义命令行接口的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"D:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train')

# 执行结果路径
results_path = r"C:\ts_data\cat_liang_ban"

# 策略回放参数设置【可选】
replay_params = {
    "symbol": "000005.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20180101",  # 策略回放开始时间
    "edt": "20220101",  # 策略回放结束时间
}
