import streamlit as st
from datetime import datetime
import streamlit_echarts as st_echarts

# from czsc import CzscSignals, CZSC
# from czsc import CZSC
from analyze import CZSC
from czsc.data import TsDataCache, get_symbols
from czsc.utils import BarGenerator


def display(symbol, bars):

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