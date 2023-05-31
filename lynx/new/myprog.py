from mylib import *

bars = get_bars('600359','15')
n_bars = merge_bars(bars)
print(len(bars),len(n_bars))