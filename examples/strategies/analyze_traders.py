# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/9/12 16:37
describe: 请描述文件用途
"""
from czsc.traders.performance import *


class DummyTradersPerformance:
    """Trader Strategy 的效果评估"""
    def __init__(self, traders_pat):
        self.file_traders = glob.glob(traders_pat)

    def get_pairs(self, sdt, edt):
        """获取一段时间内的所有交易对

        :param sdt: 开始时间
        :param edt: 结束时间
        :return:
        """
        sdt = pd.to_datetime(sdt)
        edt = pd.to_datetime(edt)
        _results = []
        for file in tqdm(self.file_traders, desc=f"get_pairs | {sdt} | {edt}"):
            try:
                trader = dill_load(file)
                _pairs = [x for x in trader.long_pos.pairs if edt >= x['平仓时间'] > x['开仓时间'] >= sdt]
                _results.extend(_pairs)
            except:
                print(file)
                traceback.print_exc()
        df = pd.DataFrame(_results)
        return df

    def get_holds(self, sdt, edt):
        """获取一段时间内的所有持仓信号

        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 返回数据样例如下
                    dt               symbol     long_pos   n1b
            0 2020-01-02 09:45:00  000001.SH         0  0.004154
            1 2020-01-02 10:00:00  000001.SH         0  0.001472
            2 2020-01-02 10:15:00  000001.SH         0  0.001291
            3 2020-01-02 10:30:00  000001.SH         0  0.001558
            4 2020-01-02 10:45:00  000001.SH         0 -0.001355
        """
        sdt = pd.to_datetime(sdt)
        edt = pd.to_datetime(edt)
        _results = []
        for file in tqdm(self.file_traders, desc=f"get_holds | {sdt} | {edt}"):
            try:
                trader = dill_load(file)
                _lh = [x for x in trader.long_holds if edt >= x['dt'] >= sdt]
                _results.extend(_lh)
            except:
                logger.exception(f"分析失败：{file}")
        df = pd.DataFrame(_results)
        return df


tp = DummyTradersPerformance(r"D:\ts_data\f60_macd_zb\DEXP202301012209\*E.cdt")

pairs = tp.get_pairs('20150101', '20221201')
ppf = PairsPerformance(pairs)
print(ppf.basic_info)
print(ppf.agg_statistics('平仓年'))
# holds = tp.get_holds('20210101', '20220101')

