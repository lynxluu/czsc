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
            return


# 输入一串k线，返回所有3k或3k以上的重叠列表
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