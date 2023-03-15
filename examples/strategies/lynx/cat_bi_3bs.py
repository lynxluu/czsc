# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/11/27 20:16
describe:
"""
import numpy as np
from collections import OrderedDict
from czsc import CZSC, signals,traders
from czsc.data import TsDataCache, get_symbols
from czsc.objects import Freq, Operate, Signal, Factor, Event
from czsc.traders import CzscAdvancedTrader,CzscTrader
from czsc.objects import PositionLong, PositionShort, RawBar
from czsc.utils import get_sub_elements
from czsc.signals.utils import down_cross_count,check_cross_info


def tas_macd_bc_V221108(c: CZSC, di: int = 1) -> OrderedDict:
    """获取倒数第i根K线的MACD背驰辅助信号

    底背弛辅助条件：
    1）最近10根K线的MACD为绿柱； --确保下降趋势的连续性
    2）最近10根K线的最低点 == 最近3根K线的最低点； --确保在相对底部
    3）最近10根K线的MACD绿柱最小值 < 最近3根K线的MACD绿柱最小值; --刚开始跌,确保下跌三天后才取

    信号列表：
    - Signal('15分钟_倒1K_MACD背驰辅助_底部_任意_任意_0')
    - Signal('15分钟_倒1K_MACD背驰辅助_顶部_任意_任意_0')
    - Signal('15分钟_倒1K_MACD背驰辅助_其他_任意_任意_0')


    :param c: CZSC对象
    :param di: 定位K
    :return:
    """
    # s = OrderedDict()

    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="底部", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="顶部", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="其他", v2='其他', v3='其他')
    ]

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
    """马鸣三买择时"""

    # 定义交易周期

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        # 基础限制,交易时间限定, 涨跌停限定
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        # 周线笔三买判断
        signals.bxt.get_s_base_xt(cat.kas['周线'],di=1)
        # 更新macd缓存
        signals.update_macd_cache(cat.kas['30分钟'])
        #次级别背驰信号
        signals.tas_macd_bc_V221201(cat.kas['30分钟'])




        # 止损止盈
        s.update(signals.pos.get_s_long01(cat, th=500))                  # 亏损5个点止损
        s.update(signals.pos.get_s_long02(cat, th=2000))                 # 回撤20个点止盈


        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="30分钟三买", signals_all=[
                Signal('周线_倒1笔_基础形态_类三买_五笔_任意_0'),
                Signal('周线_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0'),
            ], signals_any=[
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
              Factor(name=f"30分钟⼀卖", signals_all=[
              ], signals_any=[
              ]),
              Factor(name="三买破坏", signals_all=[

              ]),
              Factor(name="⽌损5%", signals_all=[
                  Signal("多头_亏损_超500BP_是_任意_任意_0")]),
              Factor(name="最⼤回撤20%", signals_all=[
                  Signal("多头_回撤_超2000BP_是_任意_任意_0")]),
                  ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['30分钟','日线','周线'],
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
# 300498.SZ#E 温氏股份, 002234.SZ#E 民和股份 300438.SZ#E 鹏辉能源
symbol = '002234.SZ'
symbols = get_symbols(dc, 'train')
sdt = "20150101"
mdt = "20200101"
edt = "20221231"


# 执行结果路径
results_path = r"D:\ts_data\bi_3bs"

# 【必须】策略回测参数设置
dummy_params = {
    "symbols": symbols,  # 回测使用的标的列表
    "sdt": sdt,  # K线数据开始时间
    "mdt": mdt,  # 策略回测开始时间
    "edt": edt,  # 策略回测结束时间
}


# 策略回放参数设置【可选】
replay_params = {
    "symbol": symbol,  # 回放交易品种
    "sdt": sdt,  # K线数据开始时间
    "mdt": mdt,  # 策略回放开始时间
    "edt": edt,  # 策略回放结束时间
}
