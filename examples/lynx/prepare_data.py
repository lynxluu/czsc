from czsc.data import TsDataCache
from loguru import logger
from tqdm import tqdm
import pandas as pd

# 此函数的目的是把缓存导出到data_path,以便共享给别人使用; 使用时,直接指定该目录即可使用
def prepare_data():
    dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=False, sdt="20120101", edt="20221001")

    # 基础数据缓存
    dc.trade_cal()
    dc.stock_basic()

    # 全部股票行情，统一采用后复权
    stocks = dc.stock_basic().to_dict("records")
    logger.info(f"全部股票数量：{len(stocks)}")
    for row in tqdm(stocks, desc="获取全部股票行情，统一采用后复权"):
        try:
            dc.pro_bar(row['ts_code'], freq='D', asset="E", adj='hfq')
            dc.pro_bar_minutes(row['ts_code'], freq='15min', asset="E", adj='hfq')
        except:
            logger.exception(f"fail on: {row}")

    # 同花顺概念
    dc.get_all_ths_members(type_="I")
    dc.get_all_ths_members(type_="N")
    concepts = pd.concat([dc.ths_index(type_='N'), dc.ths_index(type_='I')])
    concepts = concepts.to_dict('records')
    for concept in tqdm(concepts, desc="同花顺概念日线"):
        try:
            dc.ths_daily(ts_code=concept['ts_code'])
        except:
            logger.exception(f"fail on: {concept}")


# if __name__=='__main__':
#     prepare_data()