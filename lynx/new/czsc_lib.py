import traceback
import tushare as ts
import pandas as pd

import datetime as dt
from czsc.data import TsDataCache, get_symbols
# from czsc.analyze import *
from czsc.data.ts import *
from czsc.enum import *

# 引入自定义包
from analyze import *
from display import *
from czsc_test import *


# logger.disable('czsc_lib')
dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)


def now():
    return dt.datetime.now()


def is_contained(k1, k2):
    if k1.high >= k2.high and k1.low <= k2.low or k1.high <= k2.high and k1.low >= k2.low:
        return k1.dt
    else:
        return None


# 输入一串原始k线，生成无包含关系的k线
def merge_bars(bars):
    # 1.若输入空列表或长度不大于2条，返回None
    if not bars or len(bars) <= 2:
        return []

    n = len(bars)
    print('开始处理%d条k线：' % n, end=' ')

    # 2. 从bars头部寻找两条不包含的k线 加入结果列表n_bars
    n_bars = []
    for i, bar in enumerate(bars):
        if len(n_bars) < 2:
            # k1,k2 需要是 NewBar 现在都是RawBar 要转换，k3不变
            n_bars.append(NewBar(symbol=bar.symbol, id=bar.id, freq=bar.freq, dt=bar.dt,
                                       open=bar.open, close=bar.close,
                                       high=bar.high, low=bar.low, vol=bar.vol, elements=[bar]))
        else:
            k1, k2 = n_bars[-2:]
            if is_contained(k1,k2):
                n_bars.pop(0)

            k3 = bar

            # 如果k3时间比k2大，判断后合并
            if k3.dt > k2.dt:
                # print(i, len(n_bars),k1.dt,k2.dt,k3.dt)
                has_include, k4 = remove_include(k1, k2, k3)
                if has_include:
                    # k2,k3包含，弹出k3,合并k4
                    n_bars.pop()
                    n_bars.append(k4)
                else:
                    # k2，k3不包含，直接合并k4
                    n_bars.append(k4)

    print("合并后得到%d条k线" % len(n_bars))
    return n_bars


def get_bars(dc, symbol, freq='D', limit=500):
    logger.warning(f"get_bars参数-{symbol,freq, limit}")
    symbol_ = symbol.split('#')
    if len(symbol_) == 1:
        ts_code, asset = symbol_[0], 'E'
    elif len(symbol_) == 2:
        ts_code, asset = symbol_

    # now = now()
    edt = now().strftime(dt_fmt)
    sdt = '20200101'

    if 'min' in freq:
        bars = dc.pro_bar_minutes(ts_code=ts_code, asset=asset, adj='qfq', freq=freq,
                                  sdt=sdt, edt=edt, raw_bar=True, limit=limit)

    else:
        bars = dc.pro_bar(ts_code=ts_code, asset=asset, adj='qfq', freq=freq,
                          start_date=sdt, end_date=edt, raw_bar=True, limit=limit)

    return bars


def single(symbol, freq, limit=None):

    # bars = get_bars(dc, symbol,)
    bars = get_bars(dc, symbol, freq, limit)
    if not bars:
        return
    logger.info(f"获取{len(bars)}条k线完成@{now()}")
    n_bars = merge_bars(bars)
    logger.info(f"合并k线完成，获得{len(n_bars)}条k线@{now()}")
    test_cdk(bars)
    logger.info(f"测试重叠k线完成@{now()}")
    test_bi(n_bars)
    logger.info(f"测试笔k线完成@{now()}")

    # 在echart中展示
    # show(n_bars)
    if bars:
        show(bars)
    logger.info(f"绘制k线完成@{now()}")
    # test_merge(n_bars)
    # test_fx(n_bars)

    # test_cdk(bars)


    # bi, bars_b = check_bi(n_bars[-40:])


    # 在streamlit中展示
    # displayD(symbol, bars)

    # for bar in n_bars[-20:]:
    #     print(bar.dt)


def single_3l(symbol):
    # 使用15f 批量生成 30f 日线 周线
    # symbol = '688111.SH#E'
    freqs = ['5min', '30min', 'D']

    for freq in freqs:
        bars = get_bars(dc, symbol,freq)
        n_bars = merge_bars(bars)
        show(n_bars)


# 展示k线
def show(bars):
    # 在echart中展示
    cs = CZSC(bars)
    cs.to_echarts(width='1400px', height='560px')
    cs.open_in_browser(width='1400px', height='560px')

