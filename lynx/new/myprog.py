from mylib import *

def get_one():
    # bars = get_bars('000001', 'D')
    # bars = get_bars('500017.SH#FD', 'D')
    # symbol = '515880.SH#FD'
    # symbol = '002555.SZ'
    # freq = '30min'
    # # freq = 'W'
    # adj='qfq'
    # api = 1
    symbol, freq, adj, api = '002624.SZ#E', '30min', 'qfq', 1
    # symbol = '000001.SH#I'
    symbol = '801983.SI#I'
    print(symbol, freq, adj, api)

    # ts.get_k_data(code=code, ktype=ktype, index=index, autype=adj).iloc[-limit:]

    # bars = get_bars(symbol, freq, adj, api=api)
    bars = get_bars_4l(symbol, adj=adj,api=api)
    # bars = get_bars_4lx(symbol, api=api)
    print(len(bars))

    bars.to_csv(f"data_{symbol}_{adj}_{api}.csv")

    # n_bars = merge_bars(bars)
    # fxs = check_fxs(n_bars)
    # bi, bars_ubi = check_bi(n_bars, bars)
    # for fx in fxs:
    #     print(fx.dt,fx.mark,fx.high,fx.low)
    # bhcnt = count_bars(n_bars)
    # print(len(bars),len(n_bars))


def get_list():
    df = pd.read_csv('code.csv')[:3]
    adj='qfq'
    for index, row in df.iterrows():
        symbol = row['symbol']
        for api in (1, 2):
            bars = get_bars_4l(symbol, api=api)
            bars.to_csv(f"data_{symbol}_{adj}_{api}.csv")




def tst_get_bars():
    df = pd.read_csv('code.csv')[-10:]
    # print(df)
    adj='qfq'
    # api = 2
    for index, row in df.iterrows():
        symbol = row['symbol']
        assert len(get_bars_4l(symbol, api=1)) == 800, "res的长度不等于800"
        assert len(get_bars_4l(symbol, api=2)) == 800, "res的长度不等于800"

def main():
    # tst_get_bars()
    get_one()

if __name__ == '__main__':
    main()