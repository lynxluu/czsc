# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/10/31 22:17
describe: jcc 是 Japanese Candlestick Charting 的缩写，日本蜡烛图技术
"""
from typing import List, Any
from collections import OrderedDict
from czsc import CZSC
from czsc.objects import Signal, RawBar
from czsc.utils import get_sub_elements


def jcc_san_xing_xian_V221023(c: CZSC, di=1, th=2) -> OrderedDict:
    """伞形线

    **有效信号列表：**

    * Signal('15分钟_D5TH200_伞形线_满足_上吊_任意_0')
    * Signal('15分钟_D5TH200_伞形线_满足_锤子_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :param th: 可调阈值，下影线超过实体的倍数，保留两位小数
    :return: 伞形线识别结果
    """
    th = int(th * 100)
    k1, k2, k3 = f"{c.freq.value}_D{di}TH{th}_伞形线".split('_')

    # 判断对应K线是否满足：1) 下影线超过实体 th 倍；2）上影线小于实体 0.2 倍
    bar: RawBar = c.bars_raw[-di]
    # x1 - 上影线大小；x2 - 实体大小；x3 - 下影线大小
    x1, x2, x3 = bar.high - max(bar.open, bar.close), abs(bar.close - bar.open), min(bar.open, bar.close) - bar.low
    v1 = "满足" if x3 > x2 * th / 100 and x1 < 0.2 * x2 else "其他"

    # 判断K线趋势【这是一个可以优化的方向】
    v2 = "其他"
    if len(c.bars_raw) > 20 + di:
        left_bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=20)
        left_max = max([x.high for x in left_bars])
        left_min = min([x.low for x in left_bars])
        gap = left_max - left_min

        if bar.low <= left_min + 0.25 * gap:
            v2 = "锤子"
        elif bar.high >= left_max - 0.25 * gap:
            v2 = "上吊"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def jcc_ten_mo_V221028(c: CZSC, di=1) -> OrderedDict:
    """吞没形态；贡献者：琅盎

    **吞没形态，有三条判别标准：**

    1. 在吞没形态之前，市场必须处在明确的上升趋势（看跌吞没形态）或下降趋势（看涨吞没形态）中，哪怕这个趋势只是短期的。
    2. 吞没形态由两条蜡烛线组成。其中第二根蜡烛线的实体必须覆盖第一根蜡烛线的实体（但是不一定需要吞没前者的上下影线）。
    3. 吞没形态的第二个实体应与第一个实体的颜色相反。

    **有效信号列表：**

    * Signal('15分钟_D1_吞没形态_满足_看跌吞没_任意_0')
    * Signal('15分钟_D1_吞没形态_满足_看涨吞没_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :return: 吞没形态识别结果
    """

    k1, k2, k3 = f"{c.freq.value}_D{di}_吞没形态".split('_')
    bar1 = c.bars_raw[-di]
    bar2 = c.bars_raw[-di - 1]
    v1 = '满足' if bar1.high > bar2.high and bar1.low < bar2.low else "其他"

    v2 = "其他"
    if len(c.bars_raw) > 20 + di:
        left_bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=20)
        left_max = max([x.high for x in left_bars])
        left_min = min([x.low for x in left_bars])
        gap = left_max - left_min

        if bar1.low <= left_min + 0.25 * gap and bar1.close > bar1.open \
                and bar1.close > bar2.high and bar1.open < bar2.low:
            v2 = "看涨吞没"

        elif bar1.high >= left_max - 0.25 * gap and bar1.close < bar1.open \
                and bar1.close < bar2.low and bar1.open > bar2.high:
            v2 = "看跌吞没"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def jcc_bai_san_bing_V221030(c: CZSC, di=1, th=0.5) -> OrderedDict:
    """白三兵；贡献者：鲁克林

    **信号逻辑：**

    1. 白三兵由接连出现的三根白色蜡烛线组成的，收盘价依次上升;
    2. 开盘价位于前一天的收盘价和开盘价之间;
    3. 分为三种形态: 挺进形态,受阻形态,停顿形态

    **信号列表：**

    * Signal('15分钟_D3TH50_白三兵_满足_挺进_任意_0')
    * Signal('15分钟_D3TH50_白三兵_满足_受阻_任意_0')
    * Signal('15分钟_D3TH50_白三兵_满足_停顿_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di根K线 取倒数三根k线
    :param th: 可调阈值，上影线超过实体的倍数，保留两位小数
    :return: 白三兵识别结果
    """
    th = int(th * 100)
    k1, k2, k3 = f"{c.freq.value}_D{di}TH{th}_白三兵".split('_')

    # 取三根K线 判断是否满足基础形态
    bars: List[RawBar] = get_sub_elements(c.bars_raw, di, n=3)
    bar1, bar2, bar3 = bars

    v1 = "其他"
    if bar3.close > bar2.close > bar3.open > bar1.close > bar2.open > bar1.open:
        v1 = "满足"

    # 判断最后一根k线的上影线 是否小于实体0.5倍 x1 bar3上影线与bar3实体的比值,
    # 判断最后一根k线的收盘价,涨幅是否大于倒数第二根k线实体的0.2倍, x2 bar2到bar3的涨幅与bar2实体的比值,
    v2 = "其他"
    if v1 == "满足":
        x1 = (bar3.high - bar3.close) / (bar3.close - bar3.open) * 100
        x2 = (bar3.close - bar2.close) / (bar3.close - bar3.open) * 100
        if x1 > th:
            v2 = "受阻"
        elif x1 <= th and x2 <= 0.2*100:
            v2 = "停顿"
        elif x1 <= th and x2 > 0.2*100:
            v2 = "挺进"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def jcc_wu_yun_gai_ding_V221101(c: CZSC, di=1, z=500, th=50) -> OrderedDict:
    """乌云盖顶，贡献者：魏永超

    **信号逻辑：**

    1. 当前的走势属于上升趋势，或者水平调整区间的顶部。
    2. 前一天是坚挺的白色实体，也就是大阳线。
    3. 当天跳空高开，开盘价高于前一天的最高价。
    4. 当天收盘在最低价附近，且明显向下扎入前一天的K线实体内。一般要求当天收盘价低于前一天阳线实体的50%。

    **信号列表：**

    * Signal('日线_D5Z500TH50_乌云盖顶_满足_任意_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :param z: 可调阈值，前一天上涨K线实体的最低涨幅（收盘价-开盘价）/开盘价*10000，500表示至少涨5%
    :param th: 可调阈值，当天收盘价跌入前一天实体高度的百分比
    :return: 乌云盖顶识别结果
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}Z{z}TH{th}_乌云盖顶".split('_')
    v1 = "其他"

    if len(c.bars_raw) > di + 10:

        # 判断前一天K线是否满足：实体涨幅 大于 z
        pre_bar: RawBar = c.bars_raw[-di - 1]
        z0 = ((pre_bar.close - pre_bar.open) / pre_bar.open) * 10000
        flag_z = z0 > z
        # 判断当天K线是否满足：1) 跳空高开；2）收盘低于前一天实体th位置
        bar: RawBar = c.bars_raw[-di]
        flag_ho = bar.open > pre_bar.high
        flag_th = bar.close < (pre_bar.close + pre_bar.open) * (th / 100)

        # 上升趋势的高点，或者平台整理的高点
        if len(c.bars_raw) > di + 10:
            left_bars: List[RawBar] = get_sub_elements(c.bars_raw, di + 2, n=10)
            left_max_close = max([x.close for x in left_bars])

            flag_up = pre_bar.close >= left_max_close

            v1 = "满足" if flag_z and flag_ho and flag_th and flag_up else "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s


def jcc_ci_tou_V221101(c: CZSC, di=1, z=100, th=50) -> OrderedDict:
    """刺透形态

    **信号列表：**

    * Signal('日线_D5Z500TH50_刺绣形态_满足_任意_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :param z: 可调阈值，前一天下跌K线实体的最低跌幅（收盘价-开盘价）/开盘价*10000，500表示至少跌5%
    :param th: 可调阈值，当天收盘价涨超前一天实体高度的百分比
    :return: 刺绣形态识别结果
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}Z{z}TH{th}_刺透形态".split('_')

    if len(c.bars_raw) < di + 15:
        v1 = "其他"
    else:
        bar2, bar1 = get_sub_elements(c.bars_raw, di=di, n=2)
        c1 = bar2.close < bar2.open and 1 - bar2.close / bar2.open > z / 10000
        c2 = bar1.open < bar2.low and bar1.close > bar2.close + (bar2.open - bar2.close) * (th/100)

        v1 = "满足" if c1 and c2 else "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s


def jcc_san_fa_20221118(c: CZSC, di=1) -> OrderedDict:
    """上升&下降三法

    **上升三法形态由以下几个方面组成：**

    1. 首先出现的是一根长长的阳线。
    2.在这根长长的阳线之后，紧跟着一群依次下降的或者横向延伸的小实体蜡烛线。这群小实体蜡烛线的理想数目是3根，但是2根或者3根以上
    也是可以接受的，条件是：只要这群小实体蜡烛线基本上都局限在前面长长的白色蜡烛线的高点到低点的价格范围之内。小蜡烛线既可以是
    白色的，也可以是黑色的，不过，黑色蜡烛线最理想。
    3. 最后一天应当是一根坚挺的白色实体蜡烛线，并且它的收盘价高于前一天的收盘价，同时其开盘价应当高于前一天的收盘价。

    **下降三法形态由以下几个方面组成：**

    1.下降三法形态与上升三法形态完全是对等的，只不过方向相反。这类形态的形成过程如下：
    2.市场应当处在下降趋势中，首先出场的是一根长长的黑色蜡烛线。在这根黑色蜡烛线之后，跟随着大约3根依次上升的小蜡烛线，并且这群
    蜡烛线的实体都局限在第一根蜡烛线的范围之内（包括其上、下影线）。
    3.最后一天，开盘价应低于前一天的收盘价，并且收盘价应低于第一根黑色蜡烛线的收盘价。本形态与看跌旗形或看跌三角旗形形态相似。
    本形态的理想情形是，在第一根长实体之后，小实体的颜色与长实体相反。

    **信号列表：**

    - Signal('60分钟_D1K_三法A_上升三法_8K_任意_0')
    - Signal('60分钟_D1K_三法A_上升三法_6K_任意_0')
    - Signal('60分钟_D1K_三法A_上升三法_5K_任意_0')
    - Signal('60分钟_D1K_三法A_下降三法_5K_任意_0')
    - Signal('60分钟_D1K_三法A_下降三法_6K_任意_0')
    - Signal('60分钟_D1K_三法A_上升三法_7K_任意_0')
    - Signal('60分钟_D1K_三法A_下降三法_7K_任意_0')
    - Signal('60分钟_D1K_三法A_下降三法_8K_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :return: 上升及下降三法形态识别结果
    """
    def __check_san_fa(bars: List[RawBar]):
        if len(bars) < 5:
            return "其他"

        # 条件1：最近一根和最后一根K线同向
        if bars[-1].close > bars[-1].open and bars[0].close > bars[0].open and bars[-1].close > bars[0].high:
            c1 = "上升"
        elif bars[-1].close < bars[-1].open and bars[0].close < bars[0].open and bars[-1].close < bars[0].low:
            c1 = "下降"
        else:
            c1 = "其他"

        # 条件2：中间K线的高低点要求
        hhc = max([x.close for x in bars[1:-1]])
        llc = min([x.close for x in bars[1:-1]])
        hhv = max([x.high for x in bars[1:-1]])
        llv = min([x.low for x in bars[1:-1]])
        if c1 == "上升" and bars[-1].close > hhv > bars[0].high and llv > bars[0].open and bars[0].close > hhc:
            c2 = "上升三法"
        elif c1 == "下降" and bars[0].low > llv > bars[-1].close and hhv < bars[0].open and bars[0].close < llc:
            c2 = "下降三法"
        else:
            c2 = "其他"

        return c2

    k1, k2, k3 = f"{c.freq.value}_D{di}K_三法A".split('_')

    for n in (5, 6, 7, 8):
        _bars = get_sub_elements(c.bars_raw, di=di, n=n)
        v1 = __check_san_fa(_bars)
        if v1 != "其他":
            v2 = f"{n}K"
            break
        else:
            v2 = "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def jcc_san_fa_20221115(c: CZSC, di=1, zdf=500) -> OrderedDict:
    """上升&下降三法；贡献者：琅盎

    **上升三法形态由以下几个方面组成：**

    1. 首先出现的是一根长长的阳线。
    2.在这根长长的阳线之后，紧跟着一群依次下降的或者横向延伸的小实体蜡烛线。这群小实体蜡烛线的理想数目是3根，但是2根或者3根以上
    也是可以接受的，条件是：只要这群小实体蜡烛线基本上都局限在前面长长的白色蜡烛线的高点到低点的价格范围之内。小蜡烛线既可以是
    白色的，也可以是黑色的，不过，黑色蜡烛线最理想。
    3. 最后一天应当是一根坚挺的白色实体蜡烛线，并且它的收盘价高于前一天的收盘价，同时其开盘价应当高于前一天的收盘价。

    **下降三法形态由以下几个方面组成：**

    1.下降三法形态与上升三法形态完全是对等的，只不过方向相反。这类形态的形成过程如下：
    2.市场应当处在下降趋势中，首先出场的是一根长长的黑色蜡烛线。在这根黑色蜡烛线之后，跟随着大约3根依次上升的小蜡烛线，并且这群
    蜡烛线的实体都局限在第一根蜡烛线的范围之内（包括其上、下影线）。
    3.最后一天，开盘价应低于前一天的收盘价，并且收盘价应低于第一根黑色蜡烛线的收盘价。本形态与看跌旗形或看跌三角旗形形态相似。
    本形态的理想情形是，在第一根长实体之后，小实体的颜色与长实体相反。

    **信号列表：**

    * Signal('60分钟_D1_上升&下降三法_满足_上升三法_任意_0')
    * Signal('60分钟_D1_上升&下降三法_满足_下降三法_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :param zdf: 倒1和倒数第5根K线涨跌幅，单位 BP
    :return: 上升及下降三法形态识别结果
    """

    k1, k2, k3 = f"{c.freq.value}_D{di}K_三法".split('_')
    bar6, bar5, bar4, bar3, bar2, bar1 = get_sub_elements(c.bars_raw, di=di, n=6)

    bar1_zdf = abs((bar2.close - bar1.close) / bar2.close) * 10000
    bar5_zdf = abs((bar6.close - bar5.close) / bar6.close) * 10000
    max_high = max(bar2.high, bar3.high, bar4.high)
    min_low = min(bar2.low, bar3.low, bar4.low)

    v1 = '满足' if bar1_zdf >= zdf and bar5_zdf > zdf and bar5.high > max_high else "其他"

    if bar5.close > bar5.open and bar1.close > bar1.open \
            and bar1.close > bar5.high and bar1.close > max_high and bar1.open > bar2.close:
        v2 = "上升三法"
    elif bar5.close < bar5.open and bar1.close < bar1.open \
            and bar1.close < bar5.low and bar1.close < min_low and bar1.open < bar2.close:
        v2 = "下降三法"
    else:
        v2 = "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def jcc_xing_xian_v221118(c: CZSC, di=2, th=2) -> OrderedDict:
    """星形态

    **星形态，判断标准：**

    1.启明星：

        蜡烛线1。一根长长的黑色实体，形象地表明空头占据主宰地位
        蜡烛线2。一根小小的实体，并且它与前一根实体之间不相接触（这两条蜡烛线组成了基本的星线形态）。小实体意味着卖方丧失了驱动市场走低的能力
        蜡烛线3。一根白色实体，它明显地向上推进到了第一个时段的黑色实体之内，标志着启明星形态的完成。这表明多头已经夺回了主导权

        在理想的启明星形态中，第二根蜡烛线（即星线）的实体，与第三根蜡烛线的实体之间有价格跳空。根据我的经验，即使没有这个价格跳空，
        似乎也不会削减启明星形态的技术效力。其决定性因素是，第二根蜡烛线应为纺锤线，同时第三根蜡烛线应显著深入到第一根黑色蜡烛线内部

    2.黄昏星：

        a. 如果第一根与第二根蜡烛线，第二根与第三根蜡烛线的实体之间不存在重叠。
        b. 如果第三根蜡烛线的收市价向下深深扎入第一根蜡烛线的实体内部。
        c. 如果第一根蜡烛线的交易量较小，而第三根蜡烛线的交易量较大。这表明之前趋势的驱动力正在减弱，新趋势方向的驱动力正在加强

    3.十字黄昏星

        在常规的黄昏星形态中，第二根蜡烛线具有较小的实体，如果不是较小的实体，而是一个十字线，则称为十字黄昏星形态
    4.十字启明星

        在启明星形态中，如果其星线（即三根蜡烛线中的第二根蜡烛线）是一个十字线，则成为十字启明星形态

    **信号列表：**

    - Signal('60分钟_D1TH2_星形线_黄昏星_任意_任意_0')
    - Signal('60分钟_D1TH2_星形线_启明星_任意_任意_0')
    - Signal('60分钟_D1TH2_星形线_启明星_中间十字_任意_0')
    - Signal('60分钟_D1TH2_星形线_黄昏星_中间十字_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线
    :param th: 左侧实体是当前实体的多少倍
    :return: 星形线识别结果
    """
    assert di >= 1

    k1, k2, k3 = f"{c.freq.value}_D{di}TH{th}_星形线".split('_')

    bar3, bar2, bar1 = get_sub_elements(c.bars_raw, di=di, n=3)
    x3 = abs(bar3.close - bar3.open)
    x2 = abs(bar2.close - bar2.open)
    x1 = abs(bar1.close - bar1.open)

    v1 = "其他"
    if bar3.high > bar2.high < bar1.high and bar3.low > bar2.low < bar1.low:
        """
        方向向下，启明星
            - 蜡烛线3。一根长长的黑色实体，形象地表明空头占据主宰地位。
            - 蜡烛线2。一根小小的实体，并且它与前一根实体之间不相接触（这两条蜡烛线组成了基本的星线形态）。小实体意味着卖方丧失了驱动市场走低的能力。
            - 蜡烛线1。一根白色实体，它明显地向上推进到了第一个时段的黑色实体之内，标志着启明星形态的完成。这表明多头已经夺回了主导权
        """
        if bar3.close < bar3.open and x2 * th < x3 < x2 + x1 and bar1.close > bar1.open > max(bar2.close, bar2.open):
            v1 = "启明星"

    elif bar3.high < bar2.high > bar1.high and bar3.low < bar2.low > bar1.low:
        """
        方向向上，黄昏星。
            1. 如果第一根与第二根蜡烛线，第二根与第三根蜡烛线的实体之间不存在重叠。
            2. 如果第三根蜡烛线的收市价向下深深扎入第一根蜡烛线的实体内部。
            3. 如果第一根蜡烛线的交易量较小，而第三根蜡烛线的交易量较大。这表明之前趋势的驱动力正在减弱，新趋势方向的驱动力正在加强
        """
        if bar3.close > bar3.open and x2 * th < x3 < x2 + x1 and bar1.close < bar1.open < min(bar2.close, bar2.open):
            v1 = "黄昏星"

    v2 = "中间十字" if bar2.close == bar2.open else "任意"
    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s

