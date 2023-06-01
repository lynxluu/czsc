from typing import List

from czsc.enum import Mark
from lynx.new.analyze import check_fxs, check_cdk
from lynx.new.merge_czsc import is_contained
from lynx.new.objects import FX, NewBar


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

def test_bi(bars: List[NewBar]):
    bi_list=[]
    if len(bars) < 3:
        return

def test_cdk(bars):
    print('测试重叠计算函数', end='')
    cdks = check_cdk(bars)[0]
    if cdks:
        print('发现重叠区%d组:' %len(cdks))
        for cdk in cdks[-3:]:
            print("重叠k线数：",cdk.kcnt, "起止范围：",cdk.sdt, cdk.edt, "重叠区域：",cdk.low, cdk.high)