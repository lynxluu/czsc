from czsc_lib import *

def main():
    global DEBUG
    DEBUG = 2
    # 初始化 Tushare 数据缓存
    # dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)
    # # 处理单个代码
    # #  512880.SH

    # single('000001.SH#I', 'D')
    # single('000001.SH#I', '30min')
    single('002624.SZ', 'D', 100)
    # single_3l(symbol)

if __name__ == '__main__':
    main()
