from czsc import signals
from czsc.objects import Freq, Operate, Signal, Factor, Event
from collections import OrderedDict
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar


import pandas as pd
from czsc.data import TsDataCache, freq_cn2ts
from czsc.utils import BarGenerator
from czsc.traders.utils import trade_replay
# 选择策略
from czsc.strategies import trader_strategy_sjx as strategy

# 解决 strftime(dt_fmt) 编码报错
import locale
locale.setlocale(locale.LC_CTYPE, 'Chinese')


# data_path 是 TS_CACHE 缓存数据文件夹所在目录
dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=False, sdt="20120101", edt="20221001")

# 获取单个品种的基础周期K线
tactic = strategy("600438.SH")
base_freq = tactic['base_freq']
bars = dc.pro_bar_minutes('600438.SH', "20150101", "20221001", freq=freq_cn2ts[base_freq], asset="E", adj="hfq")

# 设置回放快照文件保存目录
res_path = r"D:\ts_data\replay_trader_sjx"


# 拆分基础周期K线，一部分用来初始化BarGenerator，随后的K线是回放区间
start_date = pd.to_datetime("20200101")
bg = BarGenerator(base_freq, freqs=tactic['freqs'])
bars1 = [x for x in bars if x.dt <= start_date]
bars2 = [x for x in bars if x.dt > start_date]
for bar in bars1:
    bg.update(bar)


if __name__ == '__main__':
    trade_replay(bg, bars2, strategy, res_path)
    # signals.utils.check_cross_info()