from czsc_lib import *

def main():
    global DEBUG
    DEBUG = 2
    # 初始化 Tushare 数据缓存
    # dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)

    # # 处理单个代码
    # # 000905.SH  000016.SH  512880.SH 688981.SH  000999.SZ  002624.SZ
    ## 300649.SZ 杭州园林  000932.SH#I 全指消费 000858.SZ 五粮液
    # symbol = '688111.SH#E'
    # symbol = '000001.SH#I'

    # single('600903.SH','15min')
    # single('000001.SH','15min')
    # single('000001.SH','D')
    single('002624.SZ','D')
    # single_3l(symbol)

if __name__ == '__main__':
    main()
