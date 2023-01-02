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

def tas_dea_cross_V221106(c: CZSC, di=55) -> OrderedDict:
    """dea穿过0轴次数

    信号逻辑：
    连续三根macd柱子值依次增大，向上；反之，向下

    信号列表：
    - Signal('15分钟_倒55根K线DEA_上穿0轴_1次_任意_任意_0')
    - Signal('15分钟_倒55根K线DEA_处于0轴以上_是_任意_任意_0')
    - Signal('15分钟_倒55根K线DEA_处于0轴以下_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒3根K线
    :return:
    """

    s = OrderedDict()

    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="上穿0轴", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="处于0轴以上", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="处于0轴以下", v1="其他", v2='其他', v3='其他')
    ]

    for signal in default_signals:
        s[signal.key] = signal.value

    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    # dea上穿0轴 , dea和一串0的数组比较
    up = down_cross_count([0 for i in range(len(dea))], dea)
    down = down_cross_count(dea, [0 for i in range(len(dea))])

    # 上穿一次0轴，最后一根K线的DEA在0轴上，倒数第5根K线DEA在0轴下?
    if up == 1 and down == 0 and dea[-1] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="上穿0轴", v1=f"1次")
        s[v.key] = v.value

    # 上穿一次或始终处于0轴上方，最近X根K线macd均处于0轴上方
    if up == down == 0 and dea[-di] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="处于0轴以上", v1=f"是")
        s[v.key] = v.value
    elif up == down == 0 and dea[-di] < 0:
        v = Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DEA", k3="处于0轴以下", v1=f"是")
        s[v.key] = v.value

    return s

def tas_dif_zero_V221106(c: CZSC, di=55) -> OrderedDict:
    """dif回抽0轴

    信号逻辑：
    1.首先在基于di根k线为一段向上趋势；
    2.其次连续di根k线形成的dif最低点在 +—dif最大值0.2倍之间，在此期间判断为上涨过程中回抽0轴

    信号列表：
    - Signal('15分钟_倒55根K线DIF_回抽0轴_否_任意_任意_0')
    - Signal('15分钟_倒55根K线DIF_回抽0轴_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """
    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]

    s = OrderedDict()

    # 近di根K线的dif的最小值，在正负0.2*dif最大值区间内，即回抽0轴
    if - max(dif) * 0.2 < min(dif) < max(dif) * 0.2:
        v = Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DIF", k3="回抽0轴", v1=f"是")
    else:
        v = Signal(k1=str(c.freq.value), k2=f"倒{di}根K线DIF", k3="回抽0轴", v1=f"否")
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


# 计算倒di根k线Macd面积
# macd红绿柱子变换次数
def tas_macd_change_V221105(c: CZSC, di: int = 55) -> OrderedDict:
    """MACD颜色变化
    信号逻辑：
    计算最近di根K线对应的macd红绿柱子变换次数

    信号列表：
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_0次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_1次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_2次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_3次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_4次_任意_任意_0')
                                …
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_9次_任意_任意_0')

    :param c: czsc对象
    :param di:最近di跟K线
    :return:
    """

    k1, k2, k3 = f"{c.freq.value}_倒{di}根K线MACD_与0轴交叉次数".split('_')

    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    cross = check_cross_info(dif, dea)

    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]
    cross_ = []

    if len(re_cross) == 0:
        num = 0

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
        num = len(cross_)
    # macd与0轴交叉次数
    v1 = f"{num}次"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value

    return s


def tas_macd_cross_cnt_V221105(c: CZSC, di: int = 55) -> OrderedDict:
    """MACD颜色变化
    信号逻辑：
    计算最近di根K线对应的macd红绿柱子变换次数

    信号列表：
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_0次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_1次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_2次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_3次_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_4次_任意_任意_0')
                                …
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_9次_任意_任意_0')

    :param c: czsc对象
    :param di:最近di跟K线
    :return:
    """

    k1, k2, k3 = f"{c.freq.value}_倒{di}根K线MACD_与0轴交叉次数".split('_')

    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    cross = check_cross_info(dif, dea)

    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]
    cross_ = []

    if len(re_cross) == 0:
        num = 0

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
        num = len(cross_)
    # macd与0轴交叉次数
    v1 = f"{num}次"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value

    return s


def tas_macd_cross_cnt_div(c: CZSC, di: int = 55, dcnt: int = 4 ) -> OrderedDict:
    """MACD颜色变化
    信号逻辑：
    计算最近di根K线对应的macd红绿柱子变换次数

    信号列表：
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_3次以下_任意_任意_0')
    - Signal('15分钟_倒55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0')

    :param c: czsc对象
    :param di:最近di跟K线
    :return:
    """

    k1, k2, k3 = f"{c.freq.value}_倒{di}根K线MACD_与0轴交叉次数".split('_')

    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    cross = check_cross_info(dif, dea)

    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]
    cross_ = []

    if len(re_cross) == 0:
        num = 0

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
        num = len(cross_)

    # macd与0轴交叉次数
    if 0 <= num < dcnt:
        v1 = f"{num}次以下"
    elif num >= dcnt:
        v1 = f"{num}次以上"


    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value

    return s

def tas_macd_dir(c: CZSC, di: int=3):
    # 最近3根 MACD ⽅向信号
    s = OrderedDict()
    freq: Freq = c.freq

    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="底部", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="顶部", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"倒{di}K", k3="MACD背驰辅助", v1="其他", v2='其他', v3='其他')
    ]

    k1, k2, k3 = str(c.freq.value), f"D{di}K", "MACD背驰辅助"

    bars = get_sub_elements(c.bars_raw, di=1, n=10)
    macd = [bar.cache['MACD']['macd'] for bar in bars]

    if macd[-1] > macd[-2] > macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='向上')
    elif macd[-1] < macd[-2] < macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='向下')
    else:
        v = Signal(k1=str(freq.value), k2='倒3K', k3='MACD⽅向', v1='模糊')
    s[v.key] = v.value

    return s
# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------

def trader_strategy(symbol):
    """马鸣三买择时"""

    # 定义交易周期
    freq: Freq = '60分钟'

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        # 基础限制,交易时间限定, 涨跌停限定
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))


        # 周期用日线
        # 更新macd缓存
        signals.update_macd_cache(cat.kas[freq])
        # macd变色次数
        s.update(tas_macd_cross_cnt_div(cat.kas[freq]))
        # dea上穿0轴
        s.update(tas_dea_cross_V221106(cat.kas[freq]))
        s.update(tas_dea_cross_V221106(cat.kas[freq],di=30))
        # s.update(get_macd_third_buy(cat.kas['日线']))
        # dif回抽0轴
        s.update(tas_dif_zero_V221106(cat.kas[freq],di=30))
        # 突破中枢
        s.update(tas_macd_zs_v221106(cat.kas[freq]))
        # macd面积背驰
        s.update(tas_macd_area_compare_V221106(cat.kas[freq]))
        # macd方向
        s.update(tas_macd_dir(cat.kas[freq]))

        # 止损止盈
        s.update(signals.pos.get_s_long01(cat, th=500))                  # 亏损5个点止损
        s.update(signals.pos.get_s_long02(cat, th=2000))                 # 回撤20个点止盈

        # 更新多周期macd缓存
        # for _, c in cat.kas.items():
        #     if c.freq == Freq.D:
        #         s.update(get_macd_third_buy(c))
        # return s

        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1, T0=False, long_min_interval=3600 * 4)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name=f"{freq}三买", signals_all=[
                Signal(f'{freq}_倒55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal(f'{freq}_倒55根K线DEA_上穿0轴_1次_任意_任意_0'),
                # Signal('日线_⾦叉⾯积_背驰_是_任意_任意_0'),
                Signal(f'{freq}_红柱子_背驰_红柱子_是_任意_0'),
                Signal(f'{freq}_K线价格_冲高回落_中枢之上_任意_任意_0')
            ], signals_any=[
                Signal(f'{freq}_倒3K_MACD⽅向_向下_任意_任意_0'),
                Signal(f'{freq}_倒3K_MACD⽅向_模糊_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
              Factor(name=f"{freq}⼀卖", signals_all=[
                  Signal(f'{freq}_倒55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                  Signal(f'{freq}_倒30根K线DEA_处于0轴以上_是_任意_任意_0'),
                  Signal(f'{freq}_倒30根K线DIF_回抽0轴_是_任意_任意_0'),
              ], signals_any=[
                  # Signal('日线_死叉⾯积_背驰_是_任意_任意_0'),
                  # Signal('日线_死叉快线_背驰_是_任意_任意_0'),
                  Signal(f'{freq}_绿柱子_背驰_绿柱子_是_任意_0'),
              ]),
              Factor(name="三买破坏", signals_all=[
                  Signal(f'{freq}_K线价格_冲高回落_中枢之内_任意_任意_0')]),
              Factor(name="⽌损5%", signals_all=[
                  Signal("多头_亏损_超500BP_是_任意_任意_0")]),
              Factor(name="最⼤回撤20%", signals_all=[
                  Signal("多头_回撤_超2000BP_是_任意_任意_0")]),
                  ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": [freq],
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
symbols = get_symbols(dc, 'etfs')

# 执行结果路径
results_path = r"D:\ts_data\macd_3bs"

# 【必须】策略回测参数设置
dummy_params = {
    "symbols": get_symbols(dc, 'etfs'),  # 回测使用的标的列表
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20200101",  # 策略回测开始时间
    "edt": "20221231",  # 策略回测结束时间
}


# 策略回放参数设置【可选】
# 300498.SZ#E 温氏股份, 002234.SZ#E 民和股份 300438.SZ#E 鹏辉能源
replay_params = {
    # "symbol": "002234.SZ#E",  # 回放交易品种
    "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20160101",  # 策略回放开始时间
    "edt": "20221214",  # 策略回放结束时间
}
