# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/5/10 15:19
describe: 请描述文件用途
"""
import os
import glob
import traceback
import pandas as pd
from tqdm import tqdm
from loguru import logger
from deprecated import deprecated
from czsc.traders.base import CzscAdvancedTrader
from czsc.utils import dill_load
from czsc.objects import cal_break_even_point


class PairsPerformance:
    """交易对效果评估"""

    def __init__(self, df_pairs: pd.DataFrame, ):
        """

        :param df_pairs: 全部交易对，数据样例如下
                标的代码   交易方向 最大仓位  开仓时间         累计开仓                平仓时间  \
            0  000001.SH   多头     1 2020-02-06 09:45:00  2820.014893 2020-02-10 13:15:00
            1  000001.SH   多头     1 2020-03-20 14:15:00  2733.164062 2020-03-27 14:15:00
            2  000001.SH   多头     1 2020-03-30 13:30:00  2747.813965 2020-03-31 13:15:00
            3  000001.SH   多头     1 2020-04-01 10:45:00  2765.350098 2020-04-02 09:45:00
            4  000001.SH   多头     1 2020-04-02 14:15:00  2757.827881 2020-04-09 11:15:00
               累计平仓     累计换手  持仓K线数       事件序列           持仓天数    盈亏金额    交易盈亏  \
            0  2872.166992     2     40  开多@低吸 > 平多@60分钟顶背驰  4.145833  52.152100  0.0184
            1  2786.754883     2     80  开多@低吸 > 平多@60分钟顶背驰  7.000000  53.590820  0.0196
            2  2752.198975     2     15     开多@低吸 > 平多@持有资金  0.989583   4.385010  0.0015
            3  2721.335938     2     12     开多@低吸 > 平多@持有资金  0.958333 -44.014160 -0.0159
            4  2821.693115     2     58  开多@低吸 > 平多@60分钟顶背驰  6.875000  63.865234  0.0231
               盈亏比例
            0  0.0184
            1  0.0196
            2  0.0015
            3 -0.0159
            4  0.0231

        """
        time_convert = lambda x: (x.strftime("%Y年"), x.strftime("%Y年%m月"), x.strftime("%Y-%m-%d"),
                                  f"{x.year}年第{x.weekofyear}周" if x.weekofyear >= 10 else f"{x.year}年第0{x.weekofyear}周",
                                  )
        df_pairs[['开仓年', '开仓月', '开仓日', '开仓周']] = list(df_pairs['开仓时间'].apply(time_convert))
        df_pairs[['平仓年', '平仓月', '平仓日', '平仓周']] = list(df_pairs['平仓时间'].apply(time_convert))

        self.df_pairs = df_pairs
        # 指定哪些列可以用来进行聚合分析
        self.agg_columns = ['标的代码', '交易方向', '平仓年', '平仓月', '平仓周', '平仓日', '开仓年', '开仓月', '开仓日', '开仓周']

    @staticmethod
    def get_pairs_statistics(df_pairs: pd.DataFrame):
        """统计一组交易的基本信息

        :param df_pairs:
        :return:
        """
        if len(df_pairs) == 0:
            info = {
                "开始时间": None,
                "结束时间": None,
                "交易标的数量": 0,
                "总体交易次数": 0,
                "平均持仓天数": 0,

                "平均单笔收益": 0,
                "单笔收益标准差": 0,
                "最大单笔收益": 0,
                "最小单笔收益": 0,

                "交易胜率": 0,
                "累计盈亏比": 0,
                "单笔盈亏比": 0,
                "交易得分": 0,
                "赢面": 0,
                "每自然日收益": 0,
                "每根K线收益": 0,
                "盈亏平衡点": 0,
            }
            return info

        win_pct = round(len(df_pairs[df_pairs['盈亏比例'] > 0]) / len(df_pairs), 4)
        df_gain = df_pairs[df_pairs['盈亏比例'] > 0]
        df_loss = df_pairs[df_pairs['盈亏比例'] <= 0]

        # 限制盈亏比最大有效值为 5
        single_gain_loss_rate = min(round(df_gain['盈亏比例'].mean() / (abs(df_loss['盈亏比例'].mean()) + 1e-8), 2), 5)
        total_gain_loss_rate = min(round(df_gain['盈亏比例'].sum() / (abs(df_loss['盈亏比例'].sum()) + 1e-8), 2), 5)

        info = {
            "开始时间": df_pairs['开仓时间'].min(),
            "结束时间": df_pairs['平仓时间'].max(),

            "交易标的数量": df_pairs['标的代码'].nunique(),
            "总体交易次数": len(df_pairs),
            "平均持仓天数": round(df_pairs['持仓天数'].mean(), 2),
            "平均持仓K线数": round(df_pairs['持仓K线数'].mean(), 2),

            "平均单笔收益": round(df_pairs['盈亏比例'].mean() * 10000, 2),
            "单笔收益标准差": round(df_pairs['盈亏比例'].std() * 10000, 2),
            "最大单笔收益": round(df_pairs['盈亏比例'].max() * 10000, 2),
            "最小单笔收益": round(df_pairs['盈亏比例'].min() * 10000, 2),

            "交易胜率": win_pct,
            "单笔盈亏比": single_gain_loss_rate,
            "累计盈亏比": total_gain_loss_rate,
            "交易得分": round(total_gain_loss_rate * win_pct, 4),
            "赢面": round(single_gain_loss_rate * win_pct - (1 - win_pct), 4),
            "盈亏平衡点": round(cal_break_even_point(df_pairs['盈亏比例'].to_list()), 4),
        }

        info['每自然日收益'] = round(info['平均单笔收益'] / info['平均持仓天数'], 2)
        info['每根K线收益'] = round(info['平均单笔收益'] / info['平均持仓K线数'], 2)
        return info

    def agg_statistics(self, col: str):
        """按列聚合进行交易对评价"""
        df_pairs = self.df_pairs.copy()
        assert col in self.agg_columns, f"{col} 不是支持聚合的列，参考：{self.agg_columns}"

        results = []
        for name, dfg in df_pairs.groupby(col):
            if dfg.empty:
                continue

            res = {col: name}
            res.update(self.get_pairs_statistics(dfg))
            results.append(res)
        df = pd.DataFrame(results)
        return df

    @property
    def basic_info(self):
        """写入基础信息"""
        df_pairs = self.df_pairs.copy()
        return self.get_pairs_statistics(df_pairs)

    def agg_to_excel(self, file_xlsx):
        """遍历聚合列，保存结果到 Excel 文件中"""
        f = pd.ExcelWriter(file_xlsx)
        for col in ['标的代码', '交易方向', '平仓年', '平仓月', '平仓周', '平仓日']:
            df_ = self.agg_statistics(col)
            df_.to_excel(f, sheet_name=f"{col}聚合", index=False)
        f.close()
        logger.info(f"交易次数：{len(self.df_pairs)}; 聚合分析结果文件：{file_xlsx}")


@deprecated(reason="择时策略将使用 Position + CzscTrader 代替")
class TradersPerformance:
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
                trader: CzscAdvancedTrader = dill_load(file)
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
                trader: CzscAdvancedTrader = dill_load(file)
                _lh = [x for x in trader.long_holds if edt >= x['dt'] >= sdt]
                _results.extend(_lh)
            except:
                logger.exception(f"分析失败：{file}")
        df = pd.DataFrame(_results)
        return df


def combine_holds_and_pairs(holds, pairs, results_path):
    """结合股票池和择时策略开平交易进行分析

    :param holds: 组合股票池数据，样例：
                 成分日期    证券代码       n1b      持仓权重
            0  2020-01-02  000001.SZ  183.758194  0.001232
            1  2020-01-02  000002.SZ -156.633896  0.001232
            2  2020-01-02  000063.SZ  310.296204  0.001232
            3  2020-01-02  000066.SZ -131.824997  0.001232
            4  2020-01-02  000069.SZ  -38.561699  0.001232

    :param pairs: 择时策略开平交易数据，数据格式如下
                标的代码 交易方向  最大仓位   开仓时间         累计开仓       平仓时间  \
            0  002698.SZ   多头     1 2015-01-12 13:30:00  24.02790 2015-01-13 09:45:00
            1  300031.SZ   多头     1 2015-01-12 10:30:00  53.87420 2015-01-13 09:45:00
            2  300046.SZ   多头     1 2015-01-12 10:15:00  41.35824 2015-01-13 09:45:00
            3  300076.SZ   多头     1 2015-01-12 10:30:00  57.84800 2015-01-13 09:45:00
            4  300099.SZ   多头     1 2015-01-12 10:15:00  62.57308 2015-01-13 09:45:00
                累计平仓  累计换手 持仓K线数 持仓天数  盈亏金额  交易盈亏  盈亏比例
            0  23.38150     2      7  0.843750 -0.64640 -0.0269 -0.0269
            1  52.71284     2     13  0.968750 -1.16136 -0.0215 -0.0215
            2  40.72068     2     14  0.979167 -0.63756 -0.0154 -0.0154
            3  55.45144     2     13  0.968750 -2.39656 -0.0414 -0.0414
            4  61.50528     2     14  0.979167 -1.06780 -0.0170 -0.0170

    :param results_path: 分析结果目录
    :return:
    """
    dfh = holds.copy()
    dfh['开仓日期'] = pd.to_datetime(dfh['成分日期'])
    dfh['标的代码'] = dfh['证券代码']

    dfp = pairs.copy()
    dfp['开仓日期'] = pd.to_datetime(dfp['开仓时间'].apply(lambda x: x.date()))

    # 合并，选择组合持仓权重大于 0 的交易对
    dfp_ = dfp.merge(dfh[['开仓日期', '标的代码', '持仓权重']], on=['开仓日期', '标的代码'], how='left')
    df_pairs = dfp_[dfp_['持仓权重'] > 0]

    # 按筛选出的交易对时间范围过滤原始交易对
    dfp_sub = dfp[(dfp['开仓时间'] >= df_pairs['开仓时间'].min()) & (dfp['开仓时间'] <= df_pairs['开仓时间'].max())]

    tp_old = PairsPerformance(dfp_sub)
    tp_new = PairsPerformance(df_pairs)
    print(f"原始交易：{tp_old.basic_info}，\n{tp_old.agg_statistics('平仓年')}\n")
    print(f"组合过滤：{tp_new.basic_info}，\n{tp_new.agg_statistics('平仓年')}")

    os.makedirs(results_path, exist_ok=True)
    tp_old.agg_to_excel(os.path.join(results_path, "原始交易评价.xlsx"))
    tp_new.agg_to_excel(os.path.join(results_path, "组合过滤评价.xlsx"))
    df_pairs.reset_index(drop=True, inplace=True)
    df_pairs.to_feather(os.path.join(results_path, "组合过滤交易.feather"))
    return tp_old, tp_new


def combine_dates_and_pairs(dates: list, pairs: pd.DataFrame, results_path):
    """结合大盘日期择时和择时策略开平交易进行分析

    :param dates: 大盘日期择时日期数据，数据样例 ['2020-01-02', ..., '2022-01-06']
    :param pairs: 择时策略开平交易数据，数据格式如下
                标的代码 交易方向  最大仓位   开仓时间         累计开仓       平仓时间  \
            0  002698.SZ   多头     1 2015-01-12 13:30:00  24.02790 2015-01-13 09:45:00
            1  300031.SZ   多头     1 2015-01-12 10:30:00  53.87420 2015-01-13 09:45:00
            2  300046.SZ   多头     1 2015-01-12 10:15:00  41.35824 2015-01-13 09:45:00
            3  300076.SZ   多头     1 2015-01-12 10:30:00  57.84800 2015-01-13 09:45:00
            4  300099.SZ   多头     1 2015-01-12 10:15:00  62.57308 2015-01-13 09:45:00
                累计平仓  累计换手 持仓K线数 持仓天数  盈亏金额  交易盈亏  盈亏比例
            0  23.38150     2      7  0.843750 -0.64640 -0.0269 -0.0269
            1  52.71284     2     13  0.968750 -1.16136 -0.0215 -0.0215
            2  40.72068     2     14  0.979167 -0.63756 -0.0154 -0.0154
            3  55.45144     2     13  0.968750 -2.39656 -0.0414 -0.0414
            4  61.50528     2     14  0.979167 -1.06780 -0.0170 -0.0170

    :param results_path: 分析结果目录
    :return:
    """
    dates = [pd.to_datetime(x) for x in dates]
    dfp = pairs.copy()
    dfp['开仓日期'] = pd.to_datetime(dfp['开仓时间'].apply(lambda x: x.date()))
    df_pairs = dfp[dfp['开仓日期'].isin(dates)]

    # 按筛选出的交易对时间范围过滤原始交易对
    dfp_sub = dfp[(dfp['开仓时间'] >= df_pairs['开仓时间'].min()) & (dfp['开仓时间'] <= df_pairs['开仓时间'].max())]

    tp_old = PairsPerformance(dfp_sub)
    tp_new = PairsPerformance(df_pairs)
    print(f"原始交易：{tp_old.basic_info}，\n{tp_old.agg_statistics('平仓年')}\n")
    print(f"组合过滤：{tp_new.basic_info}，\n{tp_new.agg_statistics('平仓年')}")

    os.makedirs(results_path, exist_ok=True)
    tp_old.agg_to_excel(os.path.join(results_path, "原始交易评价.xlsx"))
    tp_new.agg_to_excel(os.path.join(results_path, "组合过滤评价.xlsx"))
    return tp_old, tp_new


