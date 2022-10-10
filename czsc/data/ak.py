# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/6/25 18:52
"""
from __future__  import division
import time
import pandas as pd
import tushare as ts
from deprecated import deprecated
from datetime import datetime, timedelta
from typing import List
from tqdm import tqdm
import akshare as ak
from ..analyze import RawBar
from ..enum import Freq
from tushare.pro import client
from tushare.util import upass
from tushare.util.formula import MA
from tushare.subs.ts_subs import Subs

PRICE_COLS = ['open', 'close', 'high', 'low', 'pre_close']
FORMAT = lambda x: '%.4f' % x
FREQS = {'D': '1DAY',
         'W': '1WEEK',
         'Y': '1YEAR',
         }
FACT_LIST = {
           'tor': 'turnover_rate',
           'turnover_rate': 'turnover_rate',
           'vr': 'volume_ratio',
           'volume_ratio': 'volume_ratio',
           'pe': 'pe',
           'pe_ttm': 'pe_ttm',
        }

# 数据频度 ：支持分钟(min)/日(D)/周(W)/月(M)K线，其中1min表示1分钟（类推1/5/15/30/60分钟）。
# 对于分钟数据有600积分用户可以试用（请求2次），正式权限请在QQ群私信群主或积分管理员。
freq_map = {Freq.F1: "1min", Freq.F5: '5min', Freq.F15: "15min", Freq.F30: '30min',
            Freq.F60: "60min", Freq.D: 'D', Freq.W: "W", Freq.M: "M"}
freq_cn_map = {"1分钟": Freq.F1, "5分钟": Freq.F5, "15分钟": Freq.F15, "30分钟": Freq.F30,
               "60分钟": Freq.F60, "日线": Freq.D}
exchanges = {
    "SSE": "上交所",
    "SZSE": "深交所",
    "CFFEX": "中金所",
    "SHFE": "上期所",
    "CZCE": "郑商所",
    "DCE": "大商所",
    "INE": "能源",
    "IB": "银行间",
    "XHKG": "港交所"
}

dt_fmt = "%Y-%m-%d %H:%M:%S"
date_fmt = "%Y%m%d"

try:
    ak.set_token("d2daaf22aaac92b5d55cd360406abd74755a5df6763aaa9bcf258030")
    pro = ts.pro_api()
except:
    print("Tushare Pro 初始化失败")



def format_kline(kline: pd.DataFrame, freq: Freq) -> List[RawBar]:
    """Tushare K线数据转换

    :param kline: Tushare 数据接口返回的K线数据
    :param freq: K线周期
    :return: 转换好的K线数据
    """
    bars = []
    dt_key = 'trade_time' if '分钟' in freq.value else 'trade_date'
    kline = kline.sort_values(dt_key, ascending=True, ignore_index=True)
    records = kline.to_dict('records')

    for i, record in enumerate(records):
        if freq == Freq.D:
            vol = int(record['vol']*100)
            amount = int(record.get('amount', 0)*1000)
        else:
            vol = int(record['vol'])
            amount = int(record.get('amount', 0))

        # 将每一根K线转换成 RawBar 对象
        bar = RawBar(symbol=record['ts_code'], dt=pd.to_datetime(record[dt_key]),
                     id=i, freq=freq, open=record['open'], close=record['close'],
                     high=record['high'], low=record['low'],
                     vol=vol,          # 成交量，单位：股
                     amount=amount,    # 成交额，单位：元
                     )
        bars.append(bar)
    return bars


def format_daily_ak(df: pd.DataFrame, ts_code: str):
    df.rename(columns={'日期': 'trade_date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
                       '成交量': 'vol', '成交额': 'amount', '振幅': 'amp', '涨跌幅': 'udrate', '涨跌额': 'udamt', '换手率': 'tor'},
              inplace=True)
    df['ts_code'] = ts_code

    # 日期转换
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y-%m-%d',errors='coerce')

    # 按要求排序
    order = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close','vol','amount']
    df = df[order]

    return df

def format_minute_ak(df: pd.DataFrame, ts_code: str):
    df.rename(columns={'时间': 'trade_time', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
                       '成交量': 'vol', '成交额': 'amount', '涨跌幅': 'udrate', '涨跌额': 'udamt', '最新价': 'new'},
              inplace=True)
    df['ts_code'] = ts_code

    # 日期转换格式
    df['trade_time'] = pd.to_datetime(df['trade_time'], format='%Y-%m-%d %H:%M:%S',errors='coerce')

    # 按要求排序
    order = ['ts_code', 'trade_time', 'open', 'high', 'low', 'close','vol','amount']
    df = df[order]

    return df


def ak_pro_bar(ts_code='', api=None, start_date='', end_date='', freq='D', asset='E',
               exchange='',
               adj=None,
               ma=[],
               factors=None,
               adjfactor=False,
               offset=None,
               limit=None,
               contract_type='',
               retry_count=3):
    """
    BAR数据
    Parameters:
    ------------
    ts_code:证券代码，支持股票,ETF/LOF,期货/期权,港股,数字货币
    start_date:开始日期  YYYYMMDD
    end_date:结束日期 YYYYMMDD
    freq:支持1/5/15/30/60分钟,周/月/季/年
    asset:证券类型 E:股票和交易所基金，I:沪深指数,C:数字货币,FT:期货 FD:基金/O期权/H港股/CB可转债
    exchange:市场代码，用户数字货币行情
    adj:复权类型,None不复权,qfq:前复权,hfq:后复权
    ma:均线,支持自定义均线频度，如：ma5/ma10/ma20/ma60/maN
    offset:开始行数（分页功能，从第几行开始取数据）
    limit: 本次提取数据行数
    factors因子数据，目前支持以下两种：
        vr:量比,默认不返回，返回需指定：factor=['vr']
        tor:换手率，默认不返回，返回需指定：factor=['tor']
                    以上两种都需要：factor=['vr', 'tor']
    retry_count:网络重试次数

    Return
    ----------
    DataFrame
    code:代码
    open：开盘close/high/low/vol成交量/amount成交额/maN均价/vr量比/tor换手率

         期货(asset='FT')
    code/open/close/high/low/avg_price：均价  position：持仓量  vol：成交总量
    """
    if (ts_code == '' or ts_code is None) and (adj is not None):
        print('提取复权行情必须输入ts_code参数')
        return
    if len(freq.strip()) >= 3:
        freq = freq.strip().lower()
    else:
        freq = freq.strip().upper() if asset != 'C' else freq.strip().lower()

    if 'min' not in freq:
        today = datetime.today().date()
        today = str(today)[0:10]
        start_date = '' if start_date is None else start_date
        end_date = today if end_date == '' or end_date is None else end_date
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')
    # tu中的分时周期类似 60min，ak的东财数据是 60
    period = freq.replace('min', '')

    # 对 股票代码进行处理 000001.SH 转换成 000001
    # ts_code = ts_code.strip().upper() if asset != 'C' else ts_code.strip().lower()
    if asset != 'C':
        ts_code = ts_code.split('.')[0]

    asset = asset.strip().upper()
    # api = api if api is not None else pro_api()
    for _ in range(retry_count):
        try:
            # 股票数据
            if asset == 'E':
                if freq == 'D':
                    data = ak.stock_zh_a_hist(symbol=ts_code, period="daily", start_date=start_date,
                                              end_date=end_date, adjust=adj)
                    # print("--------- Debug msg at ak.py Line 230 -----------\r\n", data.head(2))
                    # ak东财接口默认有量比换手率，此处可省略
                    # if factors is not None and len(factors) > 0:
                    #     ds = api.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)[
                    #         ['trade_date', 'turnover_rate', 'volume_ratio']]
                    #     ds = ds.set_index('trade_date')
                    #     data = data.set_index('trade_date')
                    #     data = data.merge(ds, left_index=True, right_index=True)
                    #     data = data.reset_index()
                    #     if ('tor' in factors) and ('vr' not in factors):
                    #         data = data.drop('volume_ratio', axis=1)
                    #     if ('vr' in factors) and ('tor' not in factors):
                    #         data = data.drop('turnover_rate', axis=1)
                elif freq == 'W':
                    data = ak.stock_zh_a_hist(symbol=ts_code, period="weekly", start_date=start_date,
                                       end_date=end_date, adjust=adj)
                elif freq == 'M':
                    data = ak.stock_zh_a_hist(symbol=ts_code, period="monthly", start_date=start_date,
                                       end_date=end_date, adjust=adj)
                elif 'min' in freq:
                    data = ak.index_zh_a_hist_min_em(symbol=ts_code, period=period, start_date=start_date,
                                                     end_date=end_date)
                    # print("--------- Debug msg at ak.py Line 268 -----------\r\n", data.head(2))

                # if adj is not None:
                #     fcts = api.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)[
                #         ['trade_date', 'adj_factor']]
                #     if fcts.shape[0] == 0:
                #         return None
                #     data = data.set_index('trade_date', drop=False).merge(fcts.set_index('trade_date'), left_index=True,
                #                                                           right_index=True, how='left')
                #     if 'min' in freq:
                #         data = data.sort_values('trade_time', ascending=False)
                #     data['adj_factor'] = data['adj_factor'].fillna(method='bfill')
                #     for col in PRICE_COLS:
                #         if adj == 'hfq':
                #             data[col] = data[col] * data['adj_factor']
                #         if adj == 'qfq':
                #             data[col] = data[col] * data['adj_factor'] / float(fcts['adj_factor'][0])
                #         data[col] = data[col].map(FORMAT)
                #         data[col] = data[col].astype(float)
                #     if adjfactor is False:
                #         data = data.drop('adj_factor', axis=1)
                #     if 'min' not in freq:
                #         data['change'] = data['close'] - data['pre_close']
                #         data['pct_chg'] = data['change'] / data['pre_close'] * 100
                #         data['pct_chg'] = data['pct_chg'].map(lambda x: FORMAT(x)).astype(float)
                #     else:
                #         data = data.drop(['trade_date', 'pre_close'], axis=1)
            # 股票指数
            elif asset == 'I':
                if freq == 'D':
                    data = ak.index_zh_a_hist(symbol=ts_code, period="daily", start_date=start_date,
                                               end_date=end_date)
                elif freq == 'W':
                    data = ak.index_zh_a_hist(symbol=ts_code, period="weekly", start_date=start_date,
                                               end_date=end_date)
                elif freq == 'M':
                    data = ak.index_zh_a_hist(symbol=ts_code, period="monthly", start_date=start_date,
                                               end_date=end_date)
                elif 'min' in freq:
                    data = ak.index_zh_a_hist_min_em(symbol=ts_code, period=period, start_date=start_date,
                                                     end_date=end_date)

            # 期货-暂未处理
            elif asset == 'FT':
                if freq == 'D':
                    data = api.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange,
                                         offset=offset, limit=limit)
                elif 'min' in freq:
                    data = api.ft_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq,
                                       offset=offset, limit=limit)
            elif asset == 'O':
                if freq == 'D':
                    data = api.opt_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange,
                                         offset=offset, limit=limit)
                elif 'min' in freq:
                    data = api.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq,
                                        offset=offset, limit=limit)
            elif asset == 'CB':
                if freq == 'D':
                    data = api.cb_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset,
                                        limit=limit)
            elif asset == 'FD':
                if freq == 'D':
                    data = api.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset,
                                          limit=limit)
                elif 'min' in freq:
                    data = api.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq,
                                        offset=offset, limit=limit)
            # 数字货币
            if asset == 'C':
                if freq == 'd':
                    freq = 'daily'
                elif freq == 'w':
                    freq = 'week'
                data = api.coinbar(
                    exchange=exchange, symbol=ts_code, freq=freq,
                    start_dae=start_date, end_date=end_date,
                    contract_type=contract_type
                )

            # 统一处理数据列名
            if asset in ('E','I'):
                if freq in ('D', 'W', 'M'):
                    data = format_daily_ak(data, ts_code)
                elif 'min' in freq:
                    data = format_minute_ak(data, ts_code)
                    # print("--------- Debug msg at ak.py Line 317 -----------\r\n", data.head(2))
                    # data['trade_date'] = data['trade_time'].map(lambda x: x.replace('-', '')[0:8])
                    data['trade_date'] = data['trade_time'].apply(lambda x: x.strftime('%Y%m%d'))
                    data['pre_close'] = data['close'].shift(-1)
                # print("--------- Debug msg at ak.py Line 320 -----------\r\n", data.head(2))

            # 处理均线
            if ma is not None and len(ma) > 0:
                for a in ma:
                    if isinstance(a, int):
                        data['ma%s' % a] = MA(data['close'], a).map(FORMAT).shift(-(a - 1))
                        data['ma%s' % a] = data['ma%s' % a].astype(float)
                        data['ma_v_%s' % a] = MA(data['vol'], a).map(FORMAT).shift(-(a - 1))
                        data['ma_v_%s' % a] = data['ma_v_%s' % a].astype(float)
            data = data.reset_index(drop=True)


        except Exception as e:
            print(e)
        else:
            return data
    raise IOError('ERROR.')


# def ak_daily_basic(ts_code=ts_code, start_date=start_date_, end_date="20300101"):
#     daily_basic = ak.stock_zh_a_spot_em()

# def ak_stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date'):
