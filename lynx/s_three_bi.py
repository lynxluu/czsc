from typing import List, Union
from collections import OrderedDict
from czsc import analyze
from czsc.objects import Direction, BI, FakeBI, Signal, Freq


def check_three_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别由远及近的三笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的三笔形态
    :param di: 最近一笔为倒数第i笔
    :return:
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='其他', v2='其他', v3='其他')

    if len(bis) != 3:
        return v

    bi1, bi2, bi3 = bis
    if not (bi1.direction == bi3.direction):
        print(f"1,3 的 direction 不一致，无法识别三笔形态，{bi3}")
        return v

    assert bi3.direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if bi3.direction == Direction.Down:
        # 向下不重合
        if bi3.low > bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下不重合')

        # 向下奔走型
        if bi2.low < bi3.low < bi1.high < bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下奔走型')

        # 向下收敛
        if bi1.high > bi3.high and bi1.low < bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下收敛')

        if bi1.high < bi3.high and bi1.low > bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下扩张')

        if bi3.low < bi1.low and bi3.high < bi1.high:
            if bi3.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下盘背')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下无背')

    if bi3.direction == Direction.Up:
        if bi3.high < bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上不重合')

        if bi2.low < bi1.low < bi3.high < bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上奔走型')

        if bi1.high > bi3.high and bi1.low < bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上收敛')

        if bi1.high < bi3.high and bi1.low > bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上扩张')

        if bi3.low > bi1.low and bi3.high > bi1.high:
            if bi3.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上盘背')

            else:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上无背')
    return v


def get_s_three_bi(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的三笔形态信号

    信号完全分类：
        Signal('日线_倒1笔_三笔形态_向上收敛_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下收敛_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下无背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上不重合_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下盘背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上扩张_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下不重合_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上盘背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下扩张_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上奔走型_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上无背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下奔走型_任意_任意_0')

    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1
    bis = c.finished_bis
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2=f"倒{di}笔", k3="三笔形态", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if not bis:
        return s

    if di == 1:
        three_bi = bis[-3:]
    else:
        three_bi = bis[-3 - di + 1: -di + 1]

    v = check_three_bi(three_bi, freq, di)
    s[v.key] = v.value
    return s