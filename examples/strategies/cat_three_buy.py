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
from czsc.signals.utils import down_cross_count


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

def tas_dea_cross_V221106(c: CZSC, di=55) -> OrderedDict:
    """dea穿过0轴次数

    信号逻辑：
    连续三根macd柱子值依次增大，向上；反之，向下

    信号列表：
    - Signal('15分钟_近55根K线DEA_上穿0轴_1次_任意_任意_0')
    - Signal('15分钟_近55根K线DEA_处于0轴以上_是_任意_任意_0')
    - Signal('15分钟_近55根K线DEA_处于0轴以下_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒3根K线
    :return:
    """

    s = OrderedDict()

    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="上穿0轴", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以上", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以下", v1="其他", v2='其他', v3='其他')
    ]

    for signal in default_signals:
        s[signal.key] = signal.value

    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    # dea上穿0轴 , dea和一串0的数组比较
    up = down_cross_count([0 for i in range(len(dea))], dea)
    down = down_cross_count(dea, [0 for i in range(len(dea))])

    # 上穿一次0轴，最后一根K线的DEA在0轴上，倒数第5根K线DEA在0轴下?
    if up == 1 and down == 0 and dea[-1] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="上穿0轴", v1=f"1次")
        s[v.key] = v.value

    # 上穿一次或始终处于0轴上方，最近X根K线macd均处于0轴上方
    if up == down == 0 and dea[-di] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以上", v1=f"是")
        s[v.key] = v.value
    elif up == down == 0 and dea[-di] < 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以下", v1=f"是")
        s[v.key] = v.value

    return s

def tas_dif_zero_V221106(c: CZSC, di=55) -> OrderedDict:
    """dif回抽0轴

    信号逻辑：
    1.首先在基于di根k线为一段向上趋势；
    2.其次连续di根k线形成的dif最低点在 +—dif最大值0.2倍之间，在此期间判断为上涨过程中回抽0轴

    信号列表：
    - Signal('15分钟_近55根K线DIF_回抽0轴_否_任意_任意_0')
    - Signal('15分钟_近55根K线DIF_回抽0轴_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """
    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]

    s = OrderedDict()

    # 近di根K线的dif的最小值，在正负0.2*dif最大值区间内，即回抽0轴
    if - max(dif) * 0.2 < min(dif) < max(dif) * 0.2:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DIF", k3="回抽0轴", v1=f"是")
    else:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DIF", k3="回抽0轴", v1=f"否")
    s[v.key] = v.value
    return s

def tas_macd_zs_v221106(c: CZSC, di=55) -> OrderedDict:
    """单纯通过价格判断股价突破中枢

    信号逻辑：
    1.划定[-di:-13]区间为中枢区间，取其高点；
    2.取倒13根K线的最高点，此笔为中枢突破；
    3.取倒3笔的低点，判断该点位与中枢的相对位置

    信号列表：
    - Signal('15分钟_K线价格_冲高回落_中枢之内_任意_任意_0')
    - Signal('15分钟_K线价格_冲高回落_中枢之上_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """
    s = OrderedDict()

    high_zs = max([x.high for x in c.bars_raw][-di:-13])
    high_last_bi = max([x.high for x in c.bars_raw][-13:])
    low_last_bi = min([x.low for x in c.bars_raw][-3:])

    if high_zs < low_last_bi < high_last_bi < high_zs * 1.1:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="中枢之上")
        s[v.key] = v.value
    elif high_zs > low_last_bi:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="中枢之内")
        s[v.key] = v.value
    else:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="其他")
        s[v.key] = v.value

    return s


from czsc.signals.utils import check_cross_info

def tas_macd_area_compare_V221106(c: CZSC, di: int = 55) -> OrderedDict:
    # 计算倒di根k线Macd面积
    # macd柱子面积背驰
    """MACD柱子面积背驰

    信号逻辑：
    计算最近di根K线周期中，两次相邻macd柱子面积背驰比较

    信号列表：
    - Signal('15分钟_绿柱子_背驰_绿柱子_否_任意_0')
    - Signal('15分钟_绿柱子_背驰_绿柱子_是_任意_0')
    - Signal('15分钟_红柱子_背驰_红柱子_否_任意_0')
    - Signal('15分钟_红柱子_背驰_红柱子_是_任意_0')

    :param c: czsc对象
    :param di:最近di跟K线
    :return:
    """

    k1, k2, k3 = f"{c.freq.value}_绿柱子_背驰".split('_')
    m1, m2, m3 = f"{c.freq.value}_红柱子_背驰".split('_')

    # dif快线, dea慢线, cross快慢线交叉点
    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    cross = check_cross_info(dif, dea)

    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]
    cross_ = []

    if len(re_cross) == 0:
        pass
    else:
        for i in range(0, len(re_cross)):
            if len(cross_) >= 1 and re_cross[i]['类型'] == re_cross[i - 1]['类型']:
                # 不将上一个元素加入cross_
                del cross_[-1]

                # 我这里只重新计算了面积、快慢线的高低点，其他需要重新计算的参数各位可自行编写
                re_cross[i]['面积'] = re_cross[i - 1]['面积'] + re_cross[i]['面积']

                re_cross[i]['快线高点'] = max(re_cross[i - 1]['快线高点'], re_cross[i]['快线高点'])
                re_cross[i]['快线低点'] = min(re_cross[i - 1]['快线低点'], re_cross[i]['快线低点'])

                re_cross[i]['慢线高点'] = max(re_cross[i - 1]['慢线高点'], re_cross[i]['慢线高点'])
                re_cross[i]['慢线低点'] = min(re_cross[i - 1]['慢线低点'], re_cross[i]['慢线低点'])

                cross_.append(re_cross[i])
            else:
                cross_.append(re_cross[i])

    # 金叉判断基于剔除抖动的cross_列表
    gold_x = [i for i in cross_ if i['类型'] == '金叉']
    die_x = [i for i in cross_ if i['类型'] == '死叉']

    s = OrderedDict()
    # 最后一次金叉的面积 < 倒数第二次金叉的面积
    if len(gold_x) >= 2 and gold_x[-1]['面积'] < gold_x[-2]['面积']:
        v1 = '绿柱子'
        v2 = '是'
    else:
        v1 = '绿柱子'
        v2 = '否'
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value

    if len(die_x) >= 2 and die_x[-1]['面积'] < die_x[-2]['面积']:
        w1 = '红柱子'
        w2 = '是'
    else:
        w1 = '红柱子'
        w2 = '否'
    signal = Signal(k1=m1, k2=m2, k3=m3, v1=w1, v2=w2)
    s[signal.key] = signal.value

    return s

# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """60分钟MACD择时"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        # 基础限制,交易时间限定, 涨跌停限定
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        signals.update_macd_cache(cat.kas['30分钟'])
        # s.update(tas_macd_bc_V221108(cat.kas['30分钟']), di=1)
        s.update(tas_macd_area_compare_V221106(cat.kas['30分钟']), di=55)
        s.update(tas_dif_zero_V221106(cat.kas['30分钟']), di=55)
        s.update(tas_dea_cross_V221106(cat.kas['30分钟']), di=55)
        s.update(tas_macd_zs_v221106(cat.kas['30分钟']), di=55)

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
                # Signal("30分钟_倒1K_MACD背驰辅助_底部_任意_任意_0"),
                Signal('30分钟_绿柱子_背驰_绿柱子_是_任意_0'),
                Signal("30分钟_近55根K线DEA_上穿0轴_1次_任意_任意_0"),
                Signal('30分钟_近55根K线DEA_处于0轴以上_是_任意_任意_0'),
                Signal("30分钟_近55根K线DIF_回抽0轴_是_任意_任意_0"),
                Signal("30分钟_K线价格_冲高回落_中枢之上_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                Signal("日线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD强弱_超强_任意_任意_0"),
                Signal("周线_D1K_MACD_任意_向上_任意_0"),
                # Signal('30分钟_倒1K_MACD背驰辅助_顶部_任意_任意_0'),
                Signal('30分钟_近55根K线DEA_处于0轴以下_是_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[
                  Signal("交易_0935_1450_是_任意_任意_0"),
                  Signal("15分钟_D1K_ZDT_其他_任意_任意_0"),
              ],
              factors=[
                  Factor(name="30分钟顶背驰", signals_all=[
                      # Signal('30分钟_倒1K_MACD背驰辅助_顶部_任意_任意_0'),
                      Signal('30分钟_红柱子_背驰_红柱子_是_任意_0'),
                  ]),

                  Factor(name="持有资金", signals_all=[
                      # Signal('30分钟_倒1K_MACD背驰辅助_其他_任意_任意_0'),
                      Signal('30分钟_绿柱子_背驰_绿柱子_否_任意_0'),
                      Signal('30分钟_红柱子_背驰_红柱子_否_任意_0'),
                  ]),
              ]),
    ]

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


# 定义命令行接口的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"D:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train')

# 执行结果路径
results_path = r"D:\ts_data\three_buy"

# 策略回放参数设置【可选】
# 300498.SZ#E 温氏股份, 002234.SZ#E 民和股份 300438.SZ#E 鹏辉能源
replay_params = {
    "symbol": "300438.SZ#E",  # 回放交易品种
    # "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20210101",  # 策略回放开始时间
    "edt": "20221128",  # 策略回放结束时间
}
