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

DEBUG = 0
dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)

def is_contained(k1, k2):
    if k1.high >= k2.high and k1.low <= k2.low or k1.high <= k2.high and k1.low >= k2.low:
        return k1.dt
    else:
        return None


def test_merge(bars) -> int:
    count = 0
    if len(bars) < 2:
        return 0
    for i in range(len(bars)-1):
        k1 = bars[i]
        k2 = bars[i+1]
        if is_contained(k1, k2) is not None:
            count += 1

    print("输入k线 %d根，发现未处理包含关系的k线 %d对" % (len(bars), count))
    return count


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
                if DEBUG >= 3:
                    print(type(k1), type(k2), type(k3))
                has_include, k4 = remove_include(k1, k2, k3)
                if has_include:
                    # k2,k3包含，弹出k3,合并k4
                    n_bars.pop()
                    n_bars.append(k4)
                else:
                    # k2，k3不包含，直接合并k4
                    n_bars.append(k4)

        # 结果列表取最后两个
        if DEBUG >= 5:
            print(i, len(n_bars))

    print("合并后得到%d条k线" % len(n_bars))
    return n_bars


def get_bars(dc, symbol, freq='D', limit=500):
    symbol_ = symbol.split('#')
    if len(symbol_) == 1:
        ts_code, asset = symbol_[0], 'E'
    elif len(symbol_) == 2:
        ts_code, asset = symbol_

    # now = dt.datetime.now()
    # edt = now.strftime(dt_fmt)
    sdt = '20200101'

    if 'min' in freq:
        bars = dc.pro_bar_minutes(ts_code=ts_code, asset=asset, adj='qfq', freq=freq,
                                  sdt=sdt, edt=None, raw_bar=True, limit=limit)

    else:
        bars = dc.pro_bar(ts_code=ts_code, asset=asset, adj='qfq', freq=freq,
                          start_date=sdt, end_date=None, raw_bar=True, limit=limit)

    return bars


def get_bars2(dc, symbol):
    symbol_ = symbol.split('#')
    if len(symbol_) == 1:
        ts_code, asset = symbol_[0], 'E'
    elif len(symbol_) == 2:
        ts_code, asset = symbol_

    adj = 'qfq'

    today = dt.datetime.now()
    edt = today.strftime('%Y%m%d')
    sdt = '20200101'

    bars = dc.pro_bar_minutes(ts_code=ts_code, asset=asset, freq='15min', adj='qfq', sdt=sdt, edt=edt)
    freqs = ['15分钟', '30分钟', '日线', '周线']

    counts = 100
    bg = BarGenerator(base_freq=freqs[0], freqs=freqs[1:], max_count=500)

    for bar in bars[:-counts]:
        bg.update(bar)

    return bars
def get_bars_list(dc, symbols):
    res = []
    for symbol in symbols:
        # symbol, asset = each.split('#')
        print(symbol, end=' ')
        res.append(get_bars(dc, symbol))
    return res


def get_bars_list2(dc, symbols):
    res = []
    for symbol in symbols:
        # symbol, asset = each.split('#')
        print(symbol, end=' ')
        res.append(get_bars2(dc, symbol))
    return res

def main():
    global DEBUG
    DEBUG = 2
    # 初始化 Tushare 数据缓存
    # dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)

    # # 处理单个代码
    # # 000905.SH  000016.SH  512880.SH 688981.SH  000999.SZ  002624.SZ
    ## 300649.SZ 杭州园林  000932.SH#I 全指消费 000858.SZ 五粮液
    # symbol = '688111.SH#E'
    symbol = '000001.SH#I'

    # single('600903.SH','15min')
    single('000001.SH','15min')
    # single_3l(symbol)

def single(symbol, freq):

    # bars = get_bars(dc, symbol,)
    bars = get_bars(dc, symbol, freq)
    n_bars = merge_bars(bars)

    # 在echart中展示
    # show(n_bars)
    if bars:
        show(bars)

    # test_merge(n_bars)
    # test_fx(n_bars)
    # test_bi(n_bars)
    # test_cdk(bars)
    test_cdk(n_bars)

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


def multi():
    # 处理批量代码
    # # symbols = get_symbols(dc, step='index')[:3]
    symbols = ['688111.SH','688981.SH','600436.SH','600129.SH','000999.SZ',\
                     '002624.SZ','300223.SZ','301308.SZ','515880.SH#FD', '512980.SH#FD']
    res2 = get_bars_list2(dc, symbols)
    print(len(res2))


def test_fx(bars: List[NewBar]) -> List[FX]:
    fxs = check_fxs(bars)

    gao, di = 0,0
    for fx in fxs:
        if fx.mark == Mark.G:
            gao += 1
            print(fx.dt, fx.mark,fx.high)
        elif fx.mark == Mark.D:
            di += 1
            print(fx.dt, fx.mark,fx.low)

    print('获得分型数量：%d，其中顶分型：%d个，底分型：%d个.' % (len(fxs),gao,di))
    # 查看发现5.12明显不是底分型
    return fxs

def test_bi(bars: List[NewBar]) -> List[BI]:
    bi_list=[]


def test_cdk(bars):
    print('开始测试重叠区计算函数')
    has_cd, cdks = check_cdk(bars)
    if has_cd:
        print('发现重叠区域%d组:' %len(cdks))
        for cdk in cdks:
            print("重叠k线数：",cdk.kcnt, "起止范围：",cdk.sdt, cdk.edt, "重叠区域：",cdk.low, cdk.high)
# 展示k线
def show(bars):
    # 在echart中展示
    cs = CZSC(bars)
    cs.to_echarts(width='1400px', height='560px')
    cs.open_in_browser(width='1400px', height='560px')

if __name__ == '__main__':
    main()


