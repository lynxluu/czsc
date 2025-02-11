# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/5/27 22:42
describe: CTA研究模块
"""
import os
import czsc
import glob
import pandas as pd
from loguru import logger
from tqdm import tqdm
from czsc.traders.dummy import DummyBacktest
from concurrent.futures import ProcessPoolExecutor

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)


class CTAResearch:

    def __init__(self, strategy, read_bars, results_path, **kwargs):
        """CTA 策略研究统一入口

        :param strategy: 策略类，必须是 CzscStrategyBase 的子类
        :param read_bars: 读取K线数据的函数，返回数据为 List[RawBar]
             (symbol, freq, sdt, edt, fq='前复权', **kwargs) -> List[RawBar]
        :param results_path: 回测结果保存路径
        :param kwargs:
        """
        self.version = '0.1.0'
        self.strategy = strategy
        from czsc import CzscStrategyBase
        assert issubclass(strategy, CzscStrategyBase), "strategy 必须是 CzscStrategyBase 的子类"
        self.read_bars = read_bars

        self.results_path = results_path
        self.traders_path = os.path.join(self.results_path, "traders")
        os.makedirs(self.traders_path, exist_ok=True)

        self.kwargs = kwargs
        self.signals_module_name = kwargs.get('signals_module_name', 'czsc.signals')
        tactic = self.strategy(symbol='symbol', signals_module_name=self.signals_module_name, **self.kwargs)
        tactic.save_positions(os.path.join(self.results_path, 'positions'))

    def replay(self, symbol, sdt='20200101', edt='20220101', refresh=True):
        """单品种交易回放

        :param symbol: 标的代码
        :param sdt: 开始时间
        :param edt: 结束时间
        :param refresh: 是否刷新
        :return: None
        """
        tactic = self.strategy(symbol=symbol, signals_module_name=self.signals_module_name, **self.kwargs)
        bars = self.read_bars(symbol, tactic.base_freq, '20100101', edt, fq='后复权')
        res_path = os.path.join(self.results_path, f"{symbol}_replay")
        tactic.replay(bars, sdt=sdt, res_path=res_path, refresh=refresh, **self.kwargs)

    def check_signals(self, symbol, sdt='20200101', edt='20220101'):
        """在单个品种上检查信号

        :param symbol: 标的代码
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: None
        """
        tactic = self.strategy(symbol=symbol, signals_module_name=self.signals_module_name, **self.kwargs)
        bars = self.read_bars(symbol, tactic.base_freq, '20100101', edt, fq='后复权')
        res_path = os.path.join(self.results_path, f"{symbol}_check_signals")
        tactic.check(bars, sdt=sdt, res_path=res_path, **self.kwargs)

    def dummy(self, symbols, sdt='20200101', edt='20220101', **kwargs):
        """使用 DummyBacktest 进行 on sig 回测

        :param symbols: 品种列表
        :param sdt: 回测开始时间
        :param edt: 回测结束时间
        :param kwargs:
        :return:
        """
        bot = DummyBacktest(results_path=os.path.join(self.results_path, 'dummy_results'),
                            signals_path=os.path.join(self.results_path, 'dummy_signals'),
                            signals_module_name=self.signals_module_name,
                            strategy=self.strategy, read_bars=self.read_bars, sdt=sdt, edt=edt)
        bot.execute(symbols=symbols, n_jobs=kwargs.get('n_jobs', 1), **kwargs)

    def backtest(self, symbols, max_workers=3, **kwargs):
        """多进程执行 on bar 回测

        :param symbols: 标的代码列表
        :param max_workers: 最大进程数
        :return: None
        """
        sdt = kwargs.get('sdt', '20170101')
        edt = kwargs.get('edt', '20220101')
        bar_sdt = kwargs.get('bar_sdt', sdt)

        def symbol_backtest(symbol):
            try:
                tactic = self.strategy(symbol=symbol, signals_module_name=self.signals_module_name, **self.kwargs)
                bars = self.read_bars(symbol, tactic.base_freq, bar_sdt, edt, fq='后复权')
                _trader = tactic.backtest(bars, sdt=sdt)
                for _pos in _trader.positions:
                    logger.info(f"{symbol} {_pos.name} {_pos.evaluate()}")
                czsc.dill_dump(_trader, os.path.join(self.traders_path, f"{symbol}.trader"))
            except Exception as e:
                logger.exception(e)

        if max_workers <= 1:
            for _symbol in tqdm(symbols, desc="On Bar 回测进度"):
                symbol_backtest(_symbol)
        else:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                executor.map(symbol_backtest, symbols)

        stats = []
        for file in glob.glob(f"{self.traders_path}/*.trader"):
            trader = czsc.dill_load(file)
            for pos in trader.positions:
                stats.append(pos.evaluate())

        dfs = pd.DataFrame(stats)
        file_stats = os.path.join(self.results_path, f"{self.strategy.__name__}回测绩效汇总.xlsx")
        dfs.to_excel(file_stats, index=False)
        logger.info(f"回测绩效汇总已保存到 {file_stats}")
