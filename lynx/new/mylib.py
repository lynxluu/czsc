import tushare as ts
import pandas as pd


# 检查包含关系
def is_contained(k1, k2) -> int:
    if k1['high'] >= k2['high'] and k1['low'] <= k2['low'] or \
         k1['high'] <= k2['high'] and k1['low'] >= k2['low']:
        return True
    else:
        return False


# 检查存在包含关系的数量
def count_klines(klines:pd.DataFrame) -> int:
    count = 0
    if len(klines) < 2:
        return 0
    for i in range(len(klines)-1):
        k1 = klines.iloc[i]
        k2 = klines.iloc[i+1]
        if is_contained(k1, k2) is not None:
            count += 1
    return count


# 输入一串原始k线，生成无包含关系的k线
def merge_klines(klines: pd.DataFrame) -> pd.DataFrame:
    # 1.若输入空列表或长度不大于2条，返回None
    if not klines or len(klines) <= 2:
        return []

    n = len(klines)
    print('开始处理%d条k线：' % n, end=' ')

    # 2. 从klines头部寻找两条不包含的k线 加入结果列表n_klines
    n_klines = []
    for kline in klines:
        if len(n_klines) < 2:
            n_klines.append(kline)
        else:
            k1, k2 = klines.tail(2)
            if is_contained(k1, k2):
                n_klines.drop(0)

        k3 = kline

        # 如果k3时间比k2大，判断后合并
        if k3.dt > k2.dt: