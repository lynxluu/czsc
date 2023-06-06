from mylib import *

# bars = get_bars('000001', 'D')
# bars = get_bars('500017.SH#FD', 'D')
symbol = '000001.SH#I'
freq = '30min'
api = 2

bars = get_bars(symbol, freq, api=api)
# bars = get_bars_4l(symbol, api=api)
# bars = get_bars_4lx(symbol, api=api)
# bars = get_4bars('000685.SH#I')
# bars = get_4bars('688981.SH#E')
bars.to_csv(f"data_{symbol}_{api}.csv")
# n_bars = merge_bars(bars)
# fxs = check_fxs(n_bars)
# bi, bars_ubi = check_bi(n_bars, bars)
# for fx in fxs:
#     print(fx.dt,fx.mark,fx.high,fx.low)
# bhcnt = count_bars(n_bars)
# print(len(bars),len(n_bars))
