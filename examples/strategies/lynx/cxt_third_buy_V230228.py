import sys

import pandas as pd

from czsc.data import freq_cn2ts

sys.path.insert(0, '..')
import os
import numpy as np
from loguru import logger
from collections import OrderedDict
from czsc.data.ts_cache import TsDataCache
from czsc import CZSC, Signal
from czsc.objects import Mark, Freq, Operate, Signal, Factor, Event, Position
from czsc.traders.base import CzscTrader, check_signals_acc
from czsc.signals.tas import update_ma_cache
from czsc.utils import get_sub_elements, create_single_signal, BarGenerator
from czsc import signals
from czsc.enum import Mark, Direction


def cxt_third_buy_V230228(c: CZSC, di=1, **kwargs) -> OrderedDict:
    """笔三买辅助

    **信号逻辑：**

    1. 定义大于前一个向上笔的高点的笔为向上突破笔，最近所有向上突破笔有价格重叠
    2. 当下笔的最低点在任一向上突破笔的高点上，且当下笔的最低点离笔序列最低点的距离不超过向上突破笔列表均值的1.618倍

    **信号列表：**

    - Signal('15分钟_D1三买辅助_V230228_三买_14笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_10笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_6笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_8笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_12笔_任意_0')

    :param c: CZSC对象
    :param di: 倒数第几笔
    :param kwargs:
    :return: 信号识别结果
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}三买辅助_V230228".split('_')
    v1, v2 = '其他', '其他'
    if len(c.bi_list) < di + 11:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)

    def check_third_buy(bis):
        """检查 bis 是否是三买的结束

        :param bis: 笔序列，按时间升序
        :return:
        """
        res = {"match": False, "v1": "三买", "v2": f"{len(bis)}笔", 'v3': "任意"}
        if bis[-1].direction == Direction.Up or bis[0].direction == bis[-1].direction:
            return res

        # 检查三买：获取向上突破的笔列表
        key_bis = []
        for i in range(0, len(bis) - 2, 2):
            if i == 0:
                key_bis.append(bis[i])
            else:
                b1, _, b3 = bis[i - 2:i + 1]
                if b3.high > b1.high:
                    key_bis.append(b3)
        if len(key_bis) < 2:
            return res

        tb_break = bis[-1].low > min([x.high for x in key_bis]) > max([x.low for x in key_bis])
        tb_price = bis[-1].low < min([x.low for x in bis]) + 1.618 * np.mean([x.power_price for x in key_bis])

        if tb_break and tb_price:
            res['match'] = True
        return res

    for n in (13, 11, 9, 7, 5):
        _bis = get_sub_elements(c.bi_list, di=di, n=n+1)
        if len(_bis) != n + 1:
            continue

        _res = check_third_buy(_bis)
        if _res['match']:
            v1 = _res['v1']
            v2 = _res['v2']
            break

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)

def get_signals(cat: CzscTrader) -> OrderedDict:
    s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
    # 使用缓存来更新信号的方法
    s.update(cxt_third_buy_V230228(cat.kas['15分钟']))
    return s



# os.environ['czsc_verbose'] = '1'

# data_path 是 TS_CACHE 缓存数据文件夹所在目录
dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=False, sdt="20120101", edt="20221001")

sdt = '20181101'
mdt = '20220101'
edt = '20230306'

symbol = '002234.SZ'

# 获取单个品种的基础周期K线
bars = dc.pro_bar_minutes(ts_code=symbol, asset='E', freq='15min',
                          sdt=sdt, edt=edt, adj='qfq', raw_bar=True)

# 设置回放快照文件保存目录
res_path = r"D:\ts_data\replay_cxt3_v2"


# 拆分基础周期K线，一部分用来初始化BarGenerator，随后的K线是回放区间
start_date = pd.to_datetime(mdt)
bg = BarGenerator('15分钟', freqs=['日线','周线'], max_count=500)
bars1 = [x for x in bars if x.dt <= start_date]
bars2 = [x for x in bars if x.dt > start_date]
for bar in bars1:
    bg.update(bar)


if __name__ == '__main__':
    check_signals_acc(bars2, get_signals)
    # trade_replay(bg, bars2, trader_strategy, res_path)
    # signals.utils.check_cross_info()