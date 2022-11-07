from typing import List, Any
from collections import OrderedDict
from czsc import CZSC
from czsc.objects import Signal, RawBar


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


def jcc_san_xing_xian_V221023(c: CZSC, di=1, th=2) -> OrderedDict:
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

def jcc_bai_san_bing_V221030(c: CZSC, di=3, th=0.5) -> OrderedDict:
    """白三兵

    有效信号列表：
    * Signal('15分钟_D3TH50_白三兵_满足_挺进_任意_0')
    * Signal('15分钟_D3TH50_白三兵_满足_受阻_任意_0')
    * Signal('15分钟_D3TH50_白三兵_满足_停顿_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di跟K线 取倒数三根k线
    :param th: 可调阈值，上影线超过实体的倍数，保留两位小数
    :return: 白三兵识别结果
    """
    th = int(th * 100)
    k1, k2, k3 = f"{c.freq.value}_D{di}TH{th}_白三兵".split('_')

    # 取三根K线 判断是否满足基础形态
    RawBar = c.bars_raw
    bar1, bar2, bar3 = RawBar[-di+0],RawBar[-di+1],RawBar[-di+2]
    v1 = "满足" if (bar2.open > bar1.open and bar2.open < bar1.close and bar2.close > bar1.close) \
                   and (bar3.open > bar2.open and bar3.open < bar2.close and bar3.close > bar2.close) \
        else "其他"


    # 判断最后一根k线的上影线 是否小于实体0.5倍 x1 bar3上影线与bar3实体的比值,
    # 判断最后一根k线的收盘价,涨幅是否大于倒数第二根k线实体的0.2倍, x2 bar2到bar3的涨幅与bar2实体的比值,
    v2 = "其他"
    if v1 == "满足":
        x1 = (bar3.high - bar3.close)/(bar3.close - bar3.open)*100
        x2 = (bar3.close - bar2.close)/(bar3.close-bar3.open)*100
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