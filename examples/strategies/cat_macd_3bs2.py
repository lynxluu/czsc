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
from czsc.utils.ta import MACD
from czsc.signals.utils import check_cross_info,down_cross_count


def get_macd_third_buy(c: CZSC, di=55):
    """
    N⽇总成交额信号
    c：base-bar
    di:基础K线数量
    完全分类：
    Signal('⽇线_55根K线MACD_与0轴交叉次数_3次以下_任意_任意_0'),
    Signal('⽇线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
    Signal('⽇线_55根K线DEA_上穿0轴次数_1次_任意_任意_0'),
    Signal('⽇线_倒3K_MACD⽅向_向上_任意_任意_0'),
    Signal('⽇线_倒3K_MACD⽅向_模糊_任意_任意_0'),
    Signal('⽇线_倒3K_MACD⽅向_向下_任意_任意_0'),
    Signal('⽇线_⾦叉⾯积_背驰_是_任意_任意_0'),
    Signal('⽇线_K线价格_冲⾼回落_中枢之上_任意_任意_0')
    Signal('⽇线_K线价格_冲⾼回落_中枢之内_任意_任意_0')
    """
    s = OrderedDict()
    freq: Freq = c.freq

    default_signals = [
        # Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3=f"与0轴交叉次数", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3="与0轴交叉次数", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2=f"{di}根K线DEA", k3="上穿0轴次数", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2='倒3K', k3="MACD⽅向", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2='⾦叉⾯积', k3="背驰", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2='死叉⾯积', k3="背驰", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2='K线价格', k3="冲⾼回落", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2=f"近30根K线DEA", k3="处于0轴以上", v1="其他", v2='其他', v3="其他"),
        Signal(k1=str(freq.value), k2=f"近30根K线DIF", k3="回抽0轴", v1="其他", v2='其他', v3="其他")
    ]
    for signal in default_signals:
        s[signal.key] = signal.value
    if len(c.bars_raw) < di + 40:
        return s

    # 最近⼏⼗根根K线的收盘价列表(为了计算准确，多计算40根K线）
    close = np.array([x.close for x in c.bars_raw][-(di + 40):])
    dif, dea, macd = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

    # 只取最后di根K线的指标
    dif = dif[-di:]
    dea = dea[-di:]
    cross = check_cross_info(dif, dea)
    list = [i for i in cross if i['距离'] >= 2]  # 过滤低级别信号抖动造成的⾦叉死叉(这
    cross_ = []
    for i in range(0, len(list)-1):
        if len(cross_) >= 1 and list[i]['类型'] == list[i-1]['类型']:
            # 不将上⼀个元素加⼊cross_
            del cross_[-1]
            cross_.append(list[i])
        else:
            cross_.append(list[i])

    # macd与0轴交叉次数
    num = len(cross_)
    if num <= 3:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3="与0轴交叉次数", v1="3次以下")
    elif num >= 4:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3="与0轴交叉次数", v1="4次以上")
    s[v.key] = v.value

    # dea上穿0轴
    count = down_cross_count([0 for i in range(len(dea))], dea)
    # 上穿⼀次0轴，最后⼀根K线的DEA在0轴上，倒数第5根K线DEA在0轴下
    if count == 1 and dea[-1] > 0 and dea[-20] < 0:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线DEA", k3="上穿0轴次数", v1="1次")
        s[v.key] = v.value
    # 上穿⼀次或始终处于0轴上⽅，最近X根K线macd均处于0轴上⽅
    if count <= 1 and dea[-1] > 0 and dea[-30] > 0:
        v = Signal(k1=str(freq.value), k2=f"近30根K线DEA", k3="处于0轴以上", v1="是")
        s[v.key] = v.value
    # 近30根K线的dif的最⼩值，在正负0.2*dif最⼤值区间内，即回抽0轴
    if - max(dif[-30:]) * 0.2 < min(dif[-30:]) < max(dif[-30:]) * 0.2:
        v = Signal(k1=str(freq.value), k2=f"近30根K线DIF", k3="回抽0轴", v1="是")
        s[v.key] = v.value

    # 最近3根 MACD ⽅向信号
    if macd[-1] > macd[-2] > macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='向上')
    elif macd[-1] < macd[-2] < macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='向下')
    else:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='模糊')
    s[v.key] = v.value

    # ⾦叉判断基于剔除抖动的cross_列表
    gold_x = [i for i in cross_ if i['类型'] == '⾦叉']
    # 死叉判断基于不剔除抖动的cross列表
    die_x = [i for i in cross if i['类型'] == '死叉']

    # 最后⼀次⾦叉的⾯积 < 倒数第⼆次⾦叉的⾯积
    if len(gold_x) >= 2 and gold_x[-1][f"面积"] < gold_x[-2][f"面积"]:
        v = Signal(k1=str(freq.value), k2='⾦叉⾯积', k3='背驰', v1='是')
    else:
        v = Signal(k1=str(freq.value), k2='⾦叉⾯积', k3='背驰', v1='其他')
    s[v.key] = v.value

    if len(die_x) >= 2 and die_x[-1]["面积"] < die_x[-2]["面积"]:
        v = Signal(k1=str(freq.value), k2='死叉⾯积', k3="背驰", v1="是")
    else:
        v = Signal(k1=str(freq.value), k2='死叉⾯积', k3="背驰", v1="其他")
    s[v.key] = v.value

    # 死叉快线⾼点背驰（设置⼀个参数，让背驰更突出⼀些，⽐如⼩于上⼀个⾼点的0.8）
    if len(die_x) >= 2 and 0 < die_x[-1]["快线高点"] < die_x[-2]["快线高点"] * 0.8:
        v = Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="是")
    else:
        v = Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="其他")
    s[v.key] = v.value
    high_zs = max([x.high for x in c.bars_raw][-di:-20])
    high_last_bi = max([x.high for x in c.bars_raw][-20:])

    low_last_bi = min([x.low for x in c.bars_raw][-3:])
    if high_zs < low_last_bi < high_last_bi < high_zs * 1.1:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲⾼回落", v1="中枢之上")
    elif high_zs > low_last_bi:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲⾼回落", v1="中枢之内")
    else:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲⾼回落", v1="其他")
    s[v.key] = v.value
    return s

# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """马鸣三买择时"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        # signals.update_macd_cache(cat.kas['15分钟'])
        # s.update(get_macd_third_buy(cat.kas["15分钟"]),di=55)

        signals.update_macd_cache(cat.kas['日线'])
        s.update(get_macd_third_buy(cat.kas['日线']))

        s.update(signals.pos.get_s_long01(cat, th=500))                  # 5个点⽌
        s.update(signals.pos.get_s_long02(cat, th=2000))                 # 回撤20
        for _, c in cat.kas.items():
            if c.freq == Freq.D:
                s.update(get_macd_third_buy(c))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="⽇线三买", signals_all=[
                Signal('⽇线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal('⽇线_55根K线DEA_上穿0轴次数_1次_任意_任意_0'),
                Signal('⽇线_⾦叉⾯积_背驰_是_任意_任意_0'),
                Signal('⽇线_K线价格_冲⾼回落_中枢之上_任意_任意_0')
            ], signals_any=[
                Signal('⽇线_倒3K_MACD⽅向_向下_任意_任意_0'),
                Signal('⽇线_倒3K_MACD⽅向_模糊_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
              Factor(name="⽇线⼀卖", signals_all=[
                  Signal('⽇线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                  Signal('⽇线_近30根K线DEA_处于0轴以上_是_任意_任意_0'),
                  Signal('⽇线_近30根K线DIF_回抽0轴_是_任意_任意_0'),
              ], signals_any=[
                  Signal('⽇线_死叉⾯积_背驰_是_任意_任意_0'),
                  Signal('⽇线_死叉快线_背驰_是_任意_任意_0'),
              ]),
              Factor(name="三买破坏", signals_all=[
                  Signal('⽇线_K线价格_冲⾼回落_中枢之内_任意_任意_0')]),
              Factor(name="⽌损5%", signals_all=[
                  Signal("多头_亏损_超500BP_是_任意_任意_0")]),
              Factor(name="最⼤回撤20%", signals_all=[
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
results_path = r"D:\ts_data\three_buy2"

# 策略回放参数设置【可选】
replay_params = {
    "symbol": "300438.SZ#E",  # 回放交易品种
    # "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20210101",  # 策略回放开始时间
    "edt": "20221214",  # 策略回放结束时间
}

# import pandas as pd
# from czsc.utils import BarGenerator
# from czsc.traders.utils import trade_replay
# from czsc.data import TsDataCache, freq_cn2ts

# if __name__ == '__main__':
#     trader_strategy(symbols)


# tactic = trader_strategy(symbols)
# base_freq = tactic['base_freq']
# bars = dc.pro_bar_minutes(replay_params["symbol"], replay_params["mdt"], replay_params["edt"], freq=freq_cn2ts[base_freq], asset="E", adj="hfq")

# # 设置回放快照文件保存目录
# res_path = r"D:\ts_data\replay_three_buy2"


# 拆分基础周期K线，一部分用来初始化BarGenerator，随后的K线是回放区间
# start_date = pd.to_datetime("20200101")
# bg = BarGenerator(base_freq, freqs=tactic['freqs'])
# bars1 = [x for x in bars if x.dt <= start_date]
# bars2 = [x for x in bars if x.dt > start_date]
# for bar in bars1:
#     bg.update(bar)


# if __name__ == '__main__':
#     trade_replay(bg, bars2, trader_strategy, results_path)