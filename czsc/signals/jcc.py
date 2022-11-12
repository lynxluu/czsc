from typing import List, Any
from collections import OrderedDict
from czsc import CZSC
from czsc.objects import Signal, RawBar
from czsc import CzscAdvancedTrader


def get_sub_elements(elements: List[Any], di: int = 1, n: int = 10) -> List[Any]:
    """获取部分元素

    :param elements: 全部元素列表
    :param di: 指定结束元素为倒数第 di 个
    :param n: 指定需要的元素个数
    :return:

    >>>x = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>>y1 = get_sub_elements(x, di=1, n=3)
    >>>y2 = get_sub_elements(x, di=2, n=3)
    """
    assert di >= 1
    if di == 1:
        se = elements[-n:]
    else:
        se = elements[-n - di + 1: -di + 1]
    return se


def jcc_san_xing_xian(c: CZSC, di=1, th=2) -> OrderedDict:
    """伞形线

    有效信号列表：
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


def jcc_three_crow(c: CZSC, di=1):
    """三只乌鸦

    信号逻辑：
    1、连续出现了三根依次下降的黑色蜡烛线，每根黑色蜡烛线的开市价处于前一个实体的范围之内，则构成了所谓的常规三只乌鸦形态；
    2、三只乌鸦形态中的第二根和第三根蜡烛线都开市于之前的实体之下构成更加疲软的三只乌鸦形态；
    3、允许有上影线，但是不能出现包含关系；
    4、允许有下影线，但是最低价接近收盘价；
    5、该信号出现在阶段性顶部。

    信号列表：
    - Signal('15分钟_K线价格_冲高回落_中枢之内_任意_任意_0')
    - Signal('15分钟_K线价格_冲高回落_中枢之上_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """

    s = OrderedDict()
    k1, k2, k3 = f"{c.freq.value}_D{di}_三只乌鸦".split('_')
    signal = Signal(k1=k1, k2=k2, k3=k3, v1='其他', v2='其他')
    s[signal.key] = signal.value

    # 逻辑判断：1) 三根K线均收盘价 < 开盘价；2)三根K线收盘价越来越低；3)三根K线最高价越来越低；4)三根K线下影线小于实体一半（可调节）；5)三根K线上影线小于实体
    bar1 = c.bars_raw[-di]
    bar2 = c.bars_raw[-di - 1]
    bar3 = c.bars_raw[-di - 2]

    if len(c.bars_raw) > 20 + 3:
        left_bars: List[RawBar] = get_sub_elements(c.bars_raw, di=3, n=20)
        left_max = max([x.high for x in left_bars])
        left_min = min([x.low for x in left_bars])
        gap = left_max - left_min

        if bar3.high >= left_max - 0.25 * gap:
            pass
        else:
            return s

    if bar1.close < bar1.open and bar2.close < bar2.open and bar3.close < bar3.open and bar1.close < bar2.close < bar3.close and bar3.high > bar2.high > bar1.high:
        if (bar1.close - bar1.low) < 0.5 * (bar1.open - bar1.close) and (bar2.close - bar2.low) < 0.5 * (
                bar2.open - bar2.close) and (bar3.close - bar3.low) < 0.5 * (bar3.open - bar3.close) \
                and (bar1.high - bar1.open) < (bar1.open - bar1.close) and (bar2.high - bar2.open) < (
                bar2.open - bar2.close) and (bar3.high - bar3.open) < (bar3.open - bar3.close):
            if bar2.close <= bar1.open <= bar2.open and bar3.close <= bar2.open <= bar3.open:
                v1 = '满足'
                v2 = '常规'
            elif bar1.open < bar2.close and bar2.open < bar3.close:
                v1 = '满足'
                v2 = '加强'
            elif (bar2.close <= bar1.open <= bar2.open and bar3.open < bar3.close) or \
                    (bar3.close <= bar2.open <= bar3.open and bar1.open < bar2.close):
                v1 = '满足'
                v2 = '半加强'
            else:
                v1 = '其他'
                v2 = '其他'
        else:
            v1 = '其他'
            v2 = '其他'
    else:
        v1 = "其他"
        v2 = '其他'

    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value

    return s


def jcc_three_soldiers(c: CZSC, di=1, th=1, ri=0.2) -> OrderedDict:
    """白三兵

    有效信号列表：
    * Signal('15分钟_TH50_白三兵_满足_挺进_任意_0')
    * Signal('15分钟_TH50_白三兵_满足_受阻_任意_0')
    * Signal('15分钟_TH50_白三兵_满足_停顿_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线 取倒数三根k线
    :param th: 可调阈值，倒1K上影线与倒1K实体的比值，保留两位小数
    :param ri: 可调阈值，倒1K涨幅与倒2K涨幅的比值，保留两位小数
    :return: 白三兵识别结果
    """

    s = OrderedDict()
    k1, k2, k3 = f"{c.freq.value}_D{di}TH{th}_白三兵".split('_')

    # th = 倒1K上涨阻力； ri = 倒1K相对涨幅；
    th = int(th * 100)
    ri = int(ri * 100)

    # 先后顺序 bar3 <-- bar2 <-- bar1， 所以计算顺序要调整
    # 判断逻辑: 1) 三根K线均收盘价 > 开盘价；2)三根K线开盘价越来越高； 3)三根K线收盘价越来越高；
    # 可选条件： 4） 三根K线的开盘价都在前一根K线的实体范围之间；5）倒1K上影线与倒1K实体的比值th_cal小于th； 6) 倒1K涨幅与倒2K涨幅的比值ri_cal大于ri.
    bar1 = c.bars_raw[-di]
    bar2 = c.bars_raw[-di - 1]
    bar3 = c.bars_raw[-di - 2]

    if bar3.open < bar3.close and bar2.open < bar2.close and bar1.open < bar1.close \
        and bar3.open < bar2.open < bar1.open and bar3.close < bar2.close < bar1.close:
    # 如考虑条件4，可简化成下面判断条件
    # if bar3.open < bar2.open < bar3.close < bar2.close < bar1.close and bar2.open < bar1.open < bar2.close:
        v1 = "满足"
        v2 = "其他"
        th_cal = (bar1.high - bar1.close) / (bar1.close - bar1.open) * 100
        ri_cal = (bar1.close - bar2.close) / (bar2.close - bar3.close) * 100
        if ri_cal > ri:
            if th_cal < th:
                v2 = "挺进"
            else:
                v2 = "受阻"
        else:
            v2 = "停顿"
    else:
        v1 = "其他"
        v2 = "其他"

    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value

    return s
