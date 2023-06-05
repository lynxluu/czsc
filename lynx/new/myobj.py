from typing import List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Mark(Enum):
    D = "底分型"
    G = "顶分型"


class Direction(Enum):
    Up = "向上"
    Down = "向下"


class Freq(Enum):
    Tick = "Tick"
    F1 = "1分钟"
    F5 = "5分钟"
    F15 = "15分钟"
    F30 = "30分钟"
    F60 = "60分钟"
    D = "日线"
    W = "周线"
    M = "月线"
    S = "季线"
    Y = "年线"


@dataclass
class RawBar:
    """原始K线元素"""
    symbol: str
    id: int  # id 必须是升序
    dt: datetime
    freq: Freq
    open: [float, int]
    close: [float, int]
    high: [float, int]
    low: [float, int]
    vol: [float, int]
    amount: [float, int] = None
    cache: dict = None  # cache 用户缓存，一个最常见的场景是缓存技术指标计算结果


class NewBar:
    """去除包含关系后的K线元素"""
    symbol: str
    id: int  # id 必须是升序
    dt: datetime
    freq: Freq
    open: [float, int]
    close: [float, int]
    high: [float, int]
    low: [float, int]
    vol: [float, int]
    amount: [float, int] = None
    elements: List = None  # 存入具有包含关系的原始K线
    cache: dict = None  # cache 用户缓存


@dataclass
class FX:
    symbol: str
    dt: datetime
    mark: Mark
    high: [float, int]
    low: [float, int]
    fx: [float, int]
    elements: List = None
    cache: dict = None  # cache 用户缓存

@dataclass
class CDK:
    sdt: datetime
    edt: datetime
    high: [float, int]
    low: [float, int]
    kcnt: int
    elements: List = None

@dataclass
class BI:
    symbol: str
    fx_a: FX = None  # 笔开始的分型
    fx_b: FX = None  # 笔结束的分型
    fxs: List = None  # 笔内部的分型列表
    direction: Direction = None
    bars: List[NewBar] = None
    cache: dict = None  # cache 用户缓存

    def __post_init__(self):
        self.sdt = self.fx_a.dt
        self.edt = self.fx_b.dt

    def __repr__(self):
        return f"BI(symbol={self.symbol}, sdt={self.sdt}, edt={self.edt}, " \
               f"direction={self.direction}, high={self.high}, low={self.low})"

    @property
    def high(self):
        # def __default(): return max(self.fx_a.high, self.fx_b.high)
        #
        # return self.get_cache_with_default('high', __default)

        return max(self.fx_a.high, self.fx_b.high)

    @property
    def low(self):
        return min(self.fx_a.low, self.fx_b.low)