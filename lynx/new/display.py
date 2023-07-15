# 引用已安装包
import os
import sys
import streamlit as st
from datetime import datetime
import streamlit_echarts as st_echarts

# 定位到项目根目录， 引用自己的代码
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(parent_dir)

from analyze import CZSC
# from czsc.analyze import CZSC
from czsc.traders.base import CzscSignals
from czsc.data import TsDataCache, get_symbols
from czsc.utils import BarGenerator



def displayD(symbol, bars):

    st.set_page_config(layout="wide")
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)

    with st.sidebar:
        st.title("使用 tushare 数据复盘K线行情")
        # symbol = st.selectbox("选择合约", options=get_symbols(dc, 'index'), index=0)
        # edt = st.date_input("结束时间", value=datetime.now())

    ts_code, asset = symbol.split('#')
    # bars = dc.pro_bar_minutes(ts_code=ts_code, asset=asset, freq='15min', sdt="20200101", edt=edt)
    st.success(f'{symbol} K线加载完成！', icon="✅")
    # freqs = ['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线']
    # freqs = ['30分钟', '日线', '周线']
    freqs = ['日线']


    # counts = 100
    # bg = BarGenerator(base_freq=freqs[0], freqs=freqs[1:], max_count=500)
    #
    # for bar in bars[:-counts]:
    #     bg.update(bar)
    # cs, remain_bars = CzscSignals(bg), bars[-counts:]
    # for bar in remain_bars:
    #     cs.update_signals(bar)

    cs = CZSC(bars)
    for freq in freqs:
        st.subheader(f"{freq} K线")
        # st_echarts.st_pyecharts(cs.kas[freq].to_echarts(), width='100%', height='600px')
        st_echarts.st_pyecharts(cs.to_echarts(), width='100%', height='600px')


def displayM():
    st.set_page_config(layout="wide")
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)

    with st.sidebar:
        st.title("使用 tushare 数据复盘K线行情")
        symbols = symbols = ['688111.SH#E','688981.SH#E','600436.SH#E','600129.SH#E','000999.SZ#E',\
                             '002624.SZ#E','300223.SZ#E','301308.SZ#E','515880.SH#FD', '512980.SH#FD']
        # symbol = st.selectbox("选择合约", options=get_symbols(dc, 'index'), index=0)
        symbol = st.selectbox("选择合约", options=symbols)
        edt = st.date_input("结束时间", value=datetime.now())

    ts_code, asset = symbol.split('#')
    bars = dc.pro_bar_minutes(ts_code=ts_code, asset=asset, freq='15min',adj='qfq', sdt="20200101", edt=edt)
    st.success(f'{symbol} K线加载完成！', icon="✅")
    # freqs = ['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线']
    freqs = ['15分钟', '30分钟', '日线', '周线']


    counts = 100
    bg = BarGenerator(base_freq=freqs[0], freqs=freqs[1:], max_count=500)

    for bar in bars[:-counts]:
        bg.update(bar)
    # 改了位置 from czsc.traders.base import CzscSignals, BarGenerator
    cs, remain_bars = CzscSignals(bg), bars[-counts:]
    for bar in remain_bars:
        cs.update_signals(bar)

    # cs = CZSC(bars)
    for freq in freqs:
        st.subheader(f"{freq} K线")
        # st_echarts.st_pyecharts(cs.kas[freq].to_echarts(), width='100%', height='600px')
        st_echarts.st_pyecharts(cs.kas[freq].to_echarts(), width='100%', height='600px')

def main():
    displayM()


if __name__ == '__main__':
    main()