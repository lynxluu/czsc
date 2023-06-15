from mylib import *


def get_one():
    symbol, freq, adj, api = '002624.SZ#E', '30min', 'qfq', 2
    # symbol, freq, adj, api = '000001.SH#I', 'D', 'qfq', 2
    # symbol = '000001.SH#I'
    # symbol = 'I2309.DCE#FT'
    # api = 1
    file_dir = rf"data\{symbol}_{freq}_{adj}_{api}.csv"
    # file_dir = f"{symbol}_{freq}_{adj}_{api}.csv"
    print(symbol, freq, adj, api, file_dir)

    bars = get_bars(symbol, freq, adj, api=api)
    bars.to_csv(file_dir)
    # print(bars.dtypes, bars.tail(1).to_string())

    # 读完文件后，要修改数据类型
    df = pd.read_csv(file_dir)
    # print(df.dtypes)
    if not df.empty:
        bars = format_csv(df)

    n_bars = merge_bars(bars)
    # 打印包含 NaN 值的行
    nan_rows = n_bars[n_bars['amount'].isna()]
    print(nan_rows)
    # bi, bars_ubi = check_bi(n_bars)

    # l_bars, bis = get_bis(n_bars)

    # fxs = get_fxs(n_bars)
    # for fx in fxs:
    #     print(fx.dt,fx.mark,fx.high,fx.low)
    # bhcnt = count_bars(n_bars)

    print(f"------输入k线：{len(bars)},合并后K线：{len(n_bars)}, 找出笔：{len(bis)}，剩余K线：{len(l_bars)}")


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
