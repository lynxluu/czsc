# -*- coding: utf-8 -*-
"""
author: lynxluu
email: lynxluu@gmail.com
create_dt: 2023/5/19
describe: 缠论分型、笔的识别
"""

import os
import webbrowser
import numpy as np
from loguru import logger
from typing import List, Callable
from collections import OrderedDict

from czsc.enum import Mark, Direction
# from czsc.objects import BI, FX, RawBar, NewBar
from objects import BI, FX, RawBar, NewBar,CDK
from czsc.utils.echarts_plot import kline_pro
from czsc import envs

# logger.disable('analyze')

def tostr(dt):
    date_str = dt.strftime('%Y-%m-%d')
    return date_str
def remove_include(k1: NewBar, k2: NewBar, k3: RawBar):
    """去除包含关系：输入三根k线，其中k1和k2为没有包含关系的K线，k3为原始K线"""
    if k1.high < k2.high:
        direction = Direction.Up
    elif k1.high > k2.high:
        direction = Direction.Down
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系，有则处理
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):
        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            dt = k2.dt if k2.high > k3.high else k3.dt
        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low < k3.low else k3.dt
        else:
            raise ValueError
        # # 合并后k线阴阳靠什么确定? 目前看是靠最后一根k线的阴阳确定 ，不合理
        # if k3.open > k3.close:
        #     open_ = high
        #     close = low
        # else:
        #     open_ = low
        #     close = high

        # 根据几根k线的合并涨跌幅来确定，如果累计涨幅是+，阳线，累计是- 阴线。
        # #不行 688111 3.28-3.31的高中取高，低中取高合并到3.31以后，low会比open高很多。导致绘图错误
        # open_ = k2.open
        # close = k3.close

        # 实际用k2的开盘和k3的收盘判断 k2，k3叠加起来是涨是跌，涨则开盘时low，收盘时high。
        # 其实这样貌似也不合理。 应该去遍历elements第一个的open和最后一个的close， 不过这个的用处不是很大。暂不处理
        if k2.open > k3.close:
            open_ = high
            close = low
        else:
            open_ = low
            close = high

        vol = k2.vol + k3.vol
        # 这里有一个隐藏Bug，len(k2.elements) 在一些及其特殊的场景下会有超大的数量，具体问题还没找到；
        # 临时解决方案是直接限定len(k2.elements)<=100
        elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, elements=elements)
        return True, k4
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4


def check_fx(k1: NewBar, k2: NewBar, k3: NewBar):
    """查找分型"""
    # Mark.G 顶分，Mark.D 底分；fx 分型的高低点。
    fx = None
    if k1.high < k2.high > k3.high and k1.low < k2.low > k3.low:
        # fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.G, high=k2.high,
        #         low=k2.low, fx=k2.high, elements=[k1, k2, k3])
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.G, high=k2.high,
                high_a=max(k1.high, k3.high), low_a=min(k1.low, k2.low),
                low=k2.low, fx=k2.high, elements=[k1, k2, k3])

    if k1.low > k2.low < k3.low and k1.high > k2.high < k3.high:
        # fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.D, high=k2.high,
        #         low=k2.low, fx=k2.low, elements=[k1, k2, k3])
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.D, high=k2.high,
                high_a=max(k1.high, k3.high), low_a=min(k1.low, k2.low),
                low=k2.low, fx=k2.low, elements=[k1, k2, k3])

    return fx


def check_fxs(bars: List[NewBar]) -> List[FX]:
    """输入一串无包含关系K线，查找其中所有分型"""
    fxs = []
    for i in range(1, len(bars)-1):
        fx: FX = check_fx(bars[i-1], bars[i], bars[i+1])
        if isinstance(fx, FX):
            # 这里可能隐含Bug，默认情况下，fxs本身是顶底交替的，但是对于一些特殊情况下不是这样，这是不对的。
            # 临时处理方案，强制要求fxs序列顶底交替
            # if len(fxs) >= 2 and fx.mark == fxs[-1].mark:
            #     if envs.get_verbose():
            #         logger.info(f"\n\ncheck_fxs: 输入数据错误{'+' * 100}")
            #         logger.info(f"当前：{fx.mark}, 上个：{fxs[-1].mark}")
            #         for bar in fx.raw_bars:
            #             logger.info(f"{bar}\n")
            #
            #         logger.info(f'last fx raw bars: \n')
            #         for bar in fxs[-1].raw_bars:
            #             logger.info(f"{bar}\n")
            # else:
            #     fxs.append(fx)
            fxs.append(fx)
    return fxs

def check_bi(bars: List[NewBar], benchmark: float = None):
    """输入一串无包含关系K线，查找其中的一笔

    :param bars: 无包含关系K线列表
    :param benchmark: 当下笔能量的比较基准
    :return:
    """
    # 这里get_min_bi_len()=6 是新笔，他从分型开始和结束计算
    # 我算法不同，从顶底的最高处计算k线数量，所以要减2
    # min_bi_len = envs.get_min_bi_len()-2
    min_bi_len = envs.get_min_bi_len()
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars

    fx_a = fxs[0]
    # 笔步骤1 找出两个相反的分型 fx_a fx_b
    try:
        if fxs[0].mark == Mark.D:
            # fx_a是底的话 朝上，求最高的顶分型 fx_b
            direction = Direction.Up
            fxs_b = [x for x in fxs if x.mark == Mark.G and x.dt > fx_a.dt and x.fx > fx_a.fx]
            if not fxs_b:
                return None, bars

            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.high >= fx_b.high:
                    fx_b = fx

        elif fxs[0].mark == Mark.G:
            # fx_a是顶的话 朝下，求最低的底分型 fx_b
            direction = Direction.Down
            fxs_b = [x for x in fxs if x.mark == Mark.D and x.dt > fx_a.dt and x.fx < fx_a.fx]
            if not fxs_b:
                return None, bars

            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.low <= fx_b.low:
                    fx_b = fx
        else:
            raise ValueError
    except:
        logger.exception("笔识别错误")
        return None, bars

    logger.info(f"-------笔步骤1a- K线范围-{tostr(bars[0].dt),tostr(bars[-1].dt)}")
    # logger.info(f"-------笔步骤1b- 分型范围{tostr(fx_a.dt), tostr(fx_b.dt)}")
    # 打印 找出的 fx_a和 fx_b
    # logger.info(f"{len(fxs),fx_a.dt, fx_b.dt}")

    # 笔步骤2 计算nk和重叠k
    # bars是合并过的k线，bars_a 计算fx_a左侧--fx_b右侧 范围内的合并k线
    # bars_ar 计算fx_a左侧--fx_b右侧的未合并k线
    # bars_b fx_b左侧开始的合并k线
    bars_a = [x for x in bars if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
    bars_ar = []
    for x in bars_a:
        for y in x.elements:
            if fx_a.elements[0].dt <= y.dt <= fx_b.elements[2].dt:
                bars_ar.append(y)
    bars_b = [x for x in bars if x.dt >= fx_b.elements[0].dt]

    # 判断fx_a和fx_b价格区间是否存在包含关系
    ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) \
                 or (fx_a.high < fx_b.high and fx_a.low > fx_b.low)


    # 判断fx_a的区间和fx_b的区间是否存在包含关系
    # area_include = (fx_a.high_a > fx_b.high_a and fx_a.low_a < fx_b.low_a) \
    #                or (fx_a.high_a < fx_b.high_a and fx_a.low_a > fx_b.low_a)

    area_include = None

    # 计算重叠k线
    has_cdk, cdk_list = check_cdk(bars_a[1:-1])

    # # 判断当前笔的涨跌幅是否超过benchmark的一定比例
    # if benchmark and abs(fx_a.fx - fx_b.fx) > benchmark * envs.get_bi_change_th():
    #     power_enough = True
    # else:
    #     power_enough = False
    power_enough = False

    # 成笔的条件：
    # 1）顶底分型之间没有包含关系；
    # 2) 分型区间之间没有包含关系
    # 3a）笔长度 大于 min_bi_len6
    # 3b) or笔长度 = min_bi_len6,未合并k线>=7
    # 3c）or笔长度 <= min_bi_len6, 笔之间有3K或以上重叠 check_cdk,参数用bars_a去头去尾=bars_a[1:-1],
    # (len(bars_a) <= min_bi_len 这里必须用 <= 不能用 < 不满足大于6k的反面是 <= 否则会报错
    # 或 当前笔的涨跌幅已经够大,不使用
    # flag1 = (len(bars_a) > min_bi_len)
    # flag2 = (len(bars_a) == min_bi_len and len(bars_ar) >= 7)
    # flag3 = (len(bars_a) <= min_bi_len and has_cdk)
    flag_bi = (len(bars_a) > min_bi_len) or \
            (len(bars_a) == min_bi_len and len(bars_ar) >= 7) or \
              (len(bars_a) <= min_bi_len and has_cdk)

    condition = (not ab_include) and (not area_include) and flag_bi
    # condition = (not ab_include) and (len(bars_a) >= min_bi_len)
    # 笔步骤3 条件满足，生成笔对象实例bi，将两端分型中包含的所有分型放入笔的fxs，所有k线放入笔的bars，根据起点分型设置笔方向
    if condition:
    # if (not ab_include) and (len(bars_a) >= min_bi_len or power_enough):
        logger.info(f"笔步骤3-笔范围{tostr(fx_a.dt), tostr(fx_b.dt)}, 笔识别{not ab_include, not area_include, flag_bi, len(bars_a), len(bars_ar), has_cdk}")
        # logger.info(f"笔步骤3-k线范围{bars[0].dt, bars[-1].dt}, 分型范围{fx_a.dt, fx_b.dt}")
        fxs_ = [x for x in fxs if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
        bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_, direction=direction, bars=bars_a)

        # 笔步骤3a bi后k线低中低 低于bi的最低点，和 高中高 高于bi的最高点，则笔不成立
        # 为什么会出现：fx_a fx_b 出现后，k还在上涨或下跌，但是未出现新的分型 导致目前的笔失败，但是未来可能会出现新的分型。
        low_ubi = min([x.low for x in bars_b])
        high_ubi = max([x.high for x in bars_b])
        if (bi.direction == Direction.Up and high_ubi > bi.high) \
                or (bi.direction == Direction.Down and low_ubi < bi.low):
            logger.info(f"笔步骤3a 笔被破坏-{tostr(bars[-1].dt)} ,高点：{high_ubi, bi.high}, 低点：{low_ubi, bi.low}")
            return None, bars
        else:
            return bi, bars_b
        # return bi, bars_b
    else:
        return None, bars

def check_cdk(bars: List[RawBar]):
    cdk_list = []
    pre_bar = None
    pre_cdk = None

    for bar in bars:
        if not pre_bar:     # 第一个bar的时候pre_bar为空，向下取
            pre_bar = bar
        else:
            # if isinstance(pre, RawBar):   # 这个无法判断，不知道原因；如果pre是RawBar，说明重叠已经断开，或者还没有重叠
            if not pre_cdk: # pre_bar有值，pre_cdk 没有值，循环比较2k，找出重叠的k，写入 pre_cdk
                minh = min(pre_bar.high, bar.high)
                maxl = max(pre_bar.low, bar.low)
                if minh >= maxl:
                    pre_cdk = CDK(sdt=pre_bar.dt, edt=bar.dt, high=minh, low=maxl, kcnt=2, elements=(pre_bar, bar))
                    # logger.info(f"发现2k重叠{pre_cdk.kcnt,pre_cdk.sdt,pre_cdk.edt}")
                else:
                    pre_bar = bar
            # elif isinstance(pre, CDK):    # 这个无法判断，不知道原因 如果pre是CDK，说明已经有重叠了，重叠和bar比较
            elif pre_cdk:   # pre_cdk 有值，循环比较pre_cdk和bar，找出重叠的k，更新 pre_cdk
                minh = min(pre_cdk.high, bar.high)
                maxl = max(pre_cdk.low, bar.low)
                if minh >= maxl:
                    pre_cdk.edt = bar.dt
                    pre_cdk.high = minh
                    pre_cdk.low = maxl
                    pre_cdk.kcnt += 1
                    pre_cdk.elements += (bar,)
                    # logger.info(f"发现nk重叠{pre_cdk.kcnt, pre_cdk.sdt, pre_cdk.edt}")
                else:   # 如果找不出重叠，且kcnt>=3 pre_cdk加入列表； 然后清空pre_cdk，赋值pre_bar 寻找新的重叠
                    if pre_cdk.kcnt >= 3:
                        cdk_list.append(pre_cdk)
                        # logger.info(f"记录nk重叠{pre_cdk.kcnt, pre_cdk.sdt, pre_cdk.edt}")
                    pre_cdk = None
                    pre_bar = bar

    if len(cdk_list)>0:
        return True, cdk_list
    else:
        return False, []

class CZSC:
    def __init__(self,
                 bars: List[RawBar],
                 get_signals: Callable = None,
                 max_bi_num=envs.get_max_bi_num(),
                 ):
        """

        :param bars: K线数据
        :param max_bi_num: 最大允许保留的笔数量
        :param get_signals: 自定义的信号计算函数
        """
        self.verbose = envs.get_verbose()
        self.max_bi_num = max_bi_num
        self.bars_raw: List[RawBar] = []  # 原始K线序列
        self.bars_ubi: List[NewBar] = []  # 未完成笔的无包含K线序列
        self.bi_list: List[BI] = []
        self.cdk_list: List[CDK] = []
        self.symbol = bars[0].symbol
        self.freq = bars[0].freq
        self.get_signals = get_signals
        self.signals = None

        for bar in bars:
            self.update(bar)

    def __repr__(self):
        return "<CZSC~{}~{}>".format(self.symbol, self.freq.value)

    def __update_bi(self):
        bars_ubi = self.bars_ubi
        if len(bars_ubi) < 3:
            return

        # 查找笔
        if not self.bi_list:
            # 全笔步骤1 获取目前 k线中的所有分型，找出跟第一个分型同类型的极值，作为起点（极大或极小）
            fxs = check_fxs(bars_ubi)

            if not fxs:
                return

            fx_a = fxs[0]
            fxs_a = [x for x in fxs if x.mark == fx_a.mark]
            # 取分型列表fxs中的第一个分型fx_a，然后把跟fx_a相同类型的分型存入 fxs_a
            # fx_a=顶分，就取所有顶分，fx_a=底分，就取所有底分。
            # 循环 fxs_a，找到同类型，最高或最低的分型
            for fx in fxs_a:
                if (fx_a.mark == Mark.D and fx.low <= fx_a.low) \
                        or (fx_a.mark == Mark.G and fx.high >= fx_a.high):
                    fx_a = fx

            # logger.info(f"全笔步骤1a-起始k线为{bars_ubi[-1].dt},起始分型为{fx_a.dt}")
            # 从分型最高或最低点开始获取k线
            bars_ubi = [x for x in bars_ubi if x.dt >= fx_a.elements[0].dt]

            # 全笔步骤2 从 fx_a开始找到第一笔，成笔则更新 self.bars_ubi
            bi, bars_ubi_ = check_bi(bars_ubi)
            if isinstance(bi, BI):
                self.bi_list.append(bi)
                # logger.info(f"找到一笔:{bi.fx_a.dt, bi.fx_b.dt},剩余k线{bars_ubi_[0].dt}")
            # 成笔以后 bars_ubi去掉笔的k线
            self.bars_ubi = bars_ubi_
            return

        # 打印未完成笔的k线数
        if self.verbose and len(bars_ubi) > 100:
            logger.info(f"{self.symbol} - {self.freq} - {bars_ubi[-1].dt} 未完成笔延伸数量: {len(bars_ubi)}")

        # if envs.get_bi_change_th() > 0.5 and len(self.bi_list) >= 5:
        #     benchmark = min(self.bi_list[-1].power_price, np.mean([x.power_price for x in self.bi_list[-5:]]))
        # else:
        #     benchmark = None

        benchmark = None

        # 全笔步骤3 再找下一笔，成笔则加入笔列表；更新self.bars_ubi
        bi, bars_ubi_ = check_bi(bars_ubi, benchmark)
        self.bars_ubi = bars_ubi_
        if isinstance(bi, BI):
            self.bi_list.append(bi)
            # logger.info(f"找到一笔:{bi.fx_a.dt, bi.fx_b.dt},剩余k线{bars_ubi_[0].dt}")

        # 全笔步骤4：如果当前笔被破坏，丢弃当前bi，将当前笔的bars与bars_ubi进行合并
        last_bi = self.bi_list[-1]
        bars_ubi = self.bars_ubi
        if (last_bi.direction == Direction.Up and bars_ubi[-1].high > last_bi.high) \
                or (last_bi.direction == Direction.Down and bars_ubi[-1].low < last_bi.low):
            logger.info(f"全笔步骤4-笔范围{tostr(last_bi.fx_a.dt), tostr(last_bi.fx_b.dt)} 被k线-{tostr(self.bars_ubi[-1].dt)}-破坏")
            # logger.info(f"k线范围{tostr(bars_ubi[0].dt),tostr(bars_ubi[-1].dt)},bars_ubi的k线从{tostr(last_bi.bars[1].dt),tostr(last_bi.bars[-2].dt)}开始加回来")
            self.bars_ubi = last_bi.bars[:-1] + [x for x in bars_ubi if x.dt >= last_bi.bars[-1].dt]
            self.bi_list.pop(-1)


    def update(self, bar: RawBar):
        """更新分析结果

        :param bar: 单根K线对象
        """
        # 更新K线序列
        if not self.bars_raw or bar.dt != self.bars_raw[-1].dt:
            self.bars_raw.append(bar)
            last_bars = [bar]
        else:
            # 当前 bar 是上一根 bar 的时间延伸
            self.bars_raw[-1] = bar
            if len(self.bars_ubi) >= 3:
                edt = self.bars_ubi[-2].dt
                self.bars_ubi = [x for x in self.bars_ubi if x.dt <= edt]
                last_bars = [x for x in self.bars_raw[-50:] if x.dt > edt]
            else:
                last_bars = self.bars_ubi[-1].elements
                last_bars[-1] = bar
                self.bars_ubi.pop(-1)
        # if self.bars_ubi:
        #     logger.info(f"处理完的k线{len(self.bars_raw),self.bars_raw[0].dt,self.bars_raw[-1].dt}")

        # 去除包含关系
        bars_ubi = self.bars_ubi
        for bar in last_bars:
            if len(bars_ubi) < 2:
                bars_ubi.append(NewBar(symbol=bar.symbol, id=bar.id, freq=bar.freq, dt=bar.dt,
                                       open=bar.open, close=bar.close,
                                       high=bar.high, low=bar.low, vol=bar.vol, elements=[bar]))
            else:
                k1, k2 = bars_ubi[-2:]
                has_include, k3 = remove_include(k1, k2, bar)
                if has_include:
                    bars_ubi[-1] = k3
                else:
                    bars_ubi.append(k3)
        self.bars_ubi = bars_ubi
        # if self.bars_ubi:
        #     logger.info(f"处理完包含的k线{len(self.bars_ubi),self.bars_ubi[0].dt, self.bars_ubi[-1].dt}")

        # 更新笔
        self.__update_bi()

        # 根据最大笔数量限制完成 bi_list, bars_raw 序列的数量控制
        self.bi_list = self.bi_list[-self.max_bi_num:]
        if self.bi_list:
            sdt = self.bi_list[0].fx_a.elements[0].dt
            s_index = 0
            for i, bar in enumerate(self.bars_raw):
                if bar.dt >= sdt:
                    s_index = i
                    break
            self.bars_raw = self.bars_raw[s_index:]

        # 如果有信号计算函数，则进行信号计算
        if self.get_signals:
            self.signals = self.get_signals(c=self)
        else:
            self.signals = OrderedDict()

    def to_echarts(self, width: str = "1400px", height: str = '580px', bs=None):
        """绘制K线分析图

        :param width: 宽
        :param height: 高
        :param bs: 交易标记，默认为空
        :return:
        """
        kline = [x.__dict__ for x in self.bars_raw]
        if len(self.bi_list) > 0:
            bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in self.bi_list] + \
                 [{'dt': self.bi_list[-1].fx_b.dt, "bi": self.bi_list[-1].fx_b.fx}]
            fx = [{'dt': x.dt, "fx": x.fx} for x in self.fx_list]
        else:
            bi = None
            fx = None
        chart = kline_pro(kline, bi=bi, fx=fx, width=width, height=height, bs=bs,
                          title="{}-{}".format(self.symbol, self.freq.value))
        return chart

    def open_in_browser(self, width: str = "1400px", height: str = '580px'):
        """直接在浏览器中打开分析结果

        :param width: 图表宽度
        :param height: 图表高度
        :return:
        """
        home_path = os.path.expanduser("~")
        file_html = os.path.join(home_path, "temp_czsc.html")
        chart = self.to_echarts(width, height)
        chart.render(file_html)
        webbrowser.open(file_html)

    @property
    def last_bi_extend(self):
        """判断最后一笔是否在延伸中，True 表示延伸中"""
        if self.bi_list[-1].direction == Direction.Up \
                and max([x.high for x in self.bars_ubi]) > self.bi_list[-1].high:
            return True

        if self.bi_list[-1].direction == Direction.Down \
                and min([x.low for x in self.bars_ubi]) < self.bi_list[-1].low:
            return True

        return False

    @property
    def finished_bis(self) -> List[BI]:
        """返回当下基本确认完成的笔列表"""
        if not self.bi_list:
            return []
        else:
            if self.last_bi_extend:
                return self.bi_list[:-1]
        return self.bi_list

    @property
    def ubi_fxs(self) -> List[FX]:
        """返回当下基本确认完成的笔列表"""
        if not self.bars_ubi:
            return []
        else:
            return check_fxs(self.bars_ubi)

    @property
    def fx_list(self) -> List[FX]:
        """返回当下基本确认完成的笔列表"""
        fxs = []
        for bi_ in self.bi_list:
            fxs.extend(bi_.fxs[1:])
        ubi = self.ubi_fxs
        for x in ubi:
            if not fxs or x.dt > fxs[-1].dt:
                fxs.append(x)
        return fxs