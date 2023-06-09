from mylib import *


def get_one():
    symbol, freq, adj, api = '002624.SZ#E', '30min', 'qfq', 1
    symbol = '000001.SH#I'
    # symbol = '801983.SI#I'
    print(symbol, freq, adj, api)

    # bars = get_bars(symbol, freq, adj, api=api)
    # print(bars.dtypes)
    # bars.to_csv(f"data_{symbol}_{adj}_{api}.csv")

    # 读完文件后，要修改数据类型
    df = pd.read_csv(f"data_{symbol}_{adj}_{api}.csv")
    # print(df.dtypes)
    bars = format_csv(df)

    n_bars = merge_bars(bars)

    # bi, bars_ubi = check_bi(n_bars)
    bis, l_bars = get_bis(n_bars)

    # fxs = get_fxs(n_bars)
    # for fx in fxs:
    #     print(fx.dt,fx.mark,fx.high,fx.low)
    # bhcnt = count_bars(n_bars)

    print(len(bars),len(n_bars), bis, l_bars)


def get_list():
    df = pd.read_csv('code.csv')[:3]
    adj, api='qfq', 1
    for index, row in df.iterrows():
        symbol = row['symbol']
        bars = get_bars_4l(symbol, api=api)
        bars.to_csv(f"data_{symbol}_{adj}_{api}.csv")

        # for api in (1, 2):
        #     bars = get_bars_4l(symbol, api=api)
        #     bars.to_csv(f"data_{symbol}_{adj}_{api}.csv")


def main():
    get_one()


if __name__ == '__main__':
    main()
