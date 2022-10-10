import feather
import pandas as pd
import numpy as np

import os

data_path = r"E:\\usr\ts_data_czsc\TS_CACHE\pro_bar"
file_name = [r"pro_bar_002800.SZ#E_20220731_D_qfq.feather", r"pro_bar_689009.SH#E_20220731_D_qfq.feather"]

# 读取文件
for _ in file_name:
    df = feather.read_dataframe(os.path.join(data_path, _))

    # 写入文件
    # feather.write_dataframe(df, 'data2.feather')
    # df.to_feather('data.feather')

    print(df.head(5))