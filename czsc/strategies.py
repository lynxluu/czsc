# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/5/6 13:24
describe: 提供一些策略的编写案例

以 trader_ 开头的是择时交易策略案例
"""
from czsc import signals
from czsc.objects import Freq, Operate, Signal, Factor, Event
from collections import OrderedDict
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar
# from czsc import analyze

def trader_standard(symbol, T0=False, min_interval=3600*4):
    """择时策略编写的一些标准说明

    输入参数：
    1. symbol 是必须要有的，且放在第一个位置，策略初始化过程指明交易哪个标的
    2. 除此之外的一些策略层面的参数可选，比如 T0，min_interval 等

    :param symbol: 择时策略初始化的必须参数，指明交易哪个标的
    :param T0:
    :param min_interval:
    :return:
    """
    pass


def trader_example1(symbol, T0=False, min_interval=3600*4):
    """A股市场择时策略样例，支持按交易标的独立设置参数

    :param symbol:
    :param T0: 是否允许T0交易
    :param min_interval: 最小开仓时间间隔，单位：秒
    :return:
    """
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=100))
        s.update(signals.pos.get_s_long02(cat, th=100))
        s.update(signals.pos.get_s_long05(cat, span='月', th=500))

        for _, c in cat.kas.items():
            s.update(signals.bxt.get_s_d0_bi(c))
            if c.freq in [Freq.F1]:
                s.update(signals.other.get_s_zdt(c, di=1))
                s.update(signals.other.get_s_op_time_span(c, op='开多', time_span=('13:00', '14:50')))
                s.update(signals.other.get_s_op_time_span(c, op='平多', time_span=('09:35', '14:50')))
            if c.freq in [Freq.F60, Freq.D, Freq.W]:
                s.update(signals.ta.get_s_macd(c, di=1))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=T0, long_min_interval=min_interval)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸", signals_all=[
                Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
                Signal("1分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
                Signal("1分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '1分钟',
        "freqs": ['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_a(symbol):
    """A股市场择时策略A"""
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=100))
        s.update(signals.pos.get_s_long02(cat, th=100))
        s.update(signals.pos.get_s_long05(cat, span='月', th=500))
        for _, c in cat.kas.items():
            if c.freq in [Freq.F15]:
                s.update(signals.bxt.get_s_d0_bi(c))
                s.update(signals.other.get_s_zdt(c, di=1))
                s.update(signals.other.get_s_op_time_span(c, op='开多', time_span=('13:00', '14:50')))
                s.update(signals.other.get_s_op_time_span(c, op='平多', time_span=('09:35', '14:50')))

            if c.freq in [Freq.F60, Freq.D, Freq.W]:
                s.update(signals.ta.get_s_macd(c, di=1))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600*4)
    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸", signals_all=[
                Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['60分钟', '日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic

def trader_stocks_base_t1(symbol):
    """60分钟MACD金叉死叉"""
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        for _, c in cat.kas.items():
            if c.freq in [Freq.F60]:
                s.update(signals.ta.get_s_macd(c, di=1))
                s.update(signals.other.get_s_zdt(c, di=1))

        return s


    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600*4)
    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="持多", signals_all=[
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
                Signal("60分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持币", signals_all=[
                Signal("60分钟_倒1K_MACD多空_空头_任意_任意_0"),
                Signal("60分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),
    ]

    # 定义空头持仓对象和交易事件
    # short_pos = PositionShort(symbol, hold_short_a=1, hold_short_b=1, hold_short_c=1,
    #                         T0=False, short_min_interval=3600*4)
    # short_events = [
    #     Event(name="开空", operate=Operate.SO, factors=[
    #         Factor(name="持空", signals_all=[
    #             Signal("60分钟_倒1K_MACD多空_空头_任意_任意_0"),
    #             Signal("60分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #         ]),
    #     ]),
    #
    #     Event(name="平空", operate=Operate.SE, factors=[
    #         Factor(name="持币", signals_all=[
    #             Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #             Signal("60分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #         ]),
    #     ]),
    # ]

    tactic = {
        "base_freq": '60分钟',
        "freqs": ['日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,
        "long_min_interval": 3600 * 12,

        # 'short_pos':short_pos,
        # "short_events": short_events,
        # "short_min_interval": 3600 * 12,
    }

    return tactic

def trader_strategy_sjx(symbol):
    """A股市场择时策略A"""
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        for _, c in cat.kas.items():
            if c.freq in [Freq.F15]:
                s.update(signals.example.double_ma(c, di=1, t1=5,t2=10))
                s.update(signals.other.get_s_zdt(c, di=1))

        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600*4)
    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸", signals_all=[
                Signal("15分钟_倒1K_5*10双均线_金叉_多头_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("15分钟_倒1K_5*10双均线_死叉_空头_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['15分钟', '60分钟', '日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,
        "long_min_interval": 3600 * 12,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_third_buy(symbol, T0=False, min_interval=0):
    """A股市场择时策略样例，支持按交易标的独立设置参数

    :param symbol:
    :param T0: 是否允许T0交易
    :param min_interval: 最小开仓时间间隔，单位：秒
    :return:
    """

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=500))  # 5个点止损
        s.update(signals.pos.get_s_long02(cat, th=2000))  # 回撤20%止盈

        for _, c in cat.kas.items():
            if c.freq == Freq.D:
                s.update(signals.signals.get_macd_third_buy(c))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=T0, long_min_interval=min_interval)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="日线三买", signals_all=[
                Signal('日线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal('日线_55根K线DEA_上穿0轴次数_1次_任意_任意_0'),
                Signal('日线_金叉面积_背驰_是_任意_任意_0'),
                Signal('日线_K线价格_冲高回落_中枢之上_任意_任意_0')
            ], signals_any=[
                Signal('日线_倒3K_MACD方向_向下_任意_任意_0'),
                Signal('日线_倒3K_MACD方向_模糊_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="日线一卖", signals_all=[
                Signal('日线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal('日线_近30根K线DEA_处于0轴以上_是_任意_任意_0'),
                Signal('日线_近30根K线DIF_回抽0轴_是_任意_任意_0'),
            ], signals_any=[
                Signal('日线_死叉面积_背驰_是_任意_任意_0'),
                Signal('日线_死叉快线_背驰_是_任意_任意_0'),
            ]),
            Factor(name="三买破坏", signals_all=[
                Signal('日线_K线价格_冲高回落_中枢之内_任意_任意_0')]),
            Factor(name="止损5%", signals_all=[
                Signal("多头_亏损_超500BP_是_任意_任意_0")]),
            Factor(name="最大回撤20%", signals_all=[
                Signal("多头_回撤_超2000BP_是_任意_任意_0")]),
        ]),

    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_bsb(symbol):
    """A股市场择时策略A"""
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        for _, c in cat.kas.items():
            if c.freq in [Freq.F15]:
                s.update(signals.jcc.jcc_bai_san_bing_V221030(c, di=3, th=0.5))
                s.update(signals.other.get_s_zdt(c, di=1))

        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600*4)
    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="追涨", signals_all=[
                Signal("15分钟_D3TH50_白三兵_满足_挺进_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("15分钟_D3TH50_白三兵_满足_受阻_任意_0"),
                Signal("15分钟_D3TH50_白三兵_满足_停顿_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['60分钟', '日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,
        "long_min_interval": 3600 * 12,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic
