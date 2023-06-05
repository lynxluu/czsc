from mylib import *

# bars = get_bars('000001', 'D')
bars = get_bars('000951#I', 'D')
n_bars = merge_bars(bars)
fxs = check_fxs(n_bars)
bi, bars_ubi = check_bi(n_bars, bars)
# for fx in fxs:
#     print(fx.dt,fx.mark,fx.high,fx.low)
# bhcnt = count_bars(n_bars)
# print(len(bars),len(n_bars))
