import os
import webbrowser

from math import fabs
from pyecharts.charts import Line
from pyecharts import options as opts

cdk_list = [
    {"dt1": "2021/1/1", "dt2": "2021/1/8", "low": 80, "high": 120},
    {"dt1": "2021/1/9", "dt2": "2021/1/15", "low": 50, "high": 100},
    {"dt1":"2021/1/20", "dt2": "2021/1/26", "low": 60, "high": 110},
]




line = Line()

# 计算线条宽度的比例系数
x_data = [10, 10]
y_data = [10, 20]
line.add_xaxis(x_data)
line.add_yaxis("", y_data, is_connect_nones=True, is_smooth=True,
               linestyle_opts=opts.LineStyleOpts(color="blue", width=2))

# 计算两个坐标之间的 y 轴像素差
opt = line.get_options()
print(opt)

y_axis = line.options['yAxis'][0]
y_min = y_axis['min']
y_max = y_axis['max']
pix_diff = fabs(y_axis['dataToCoord'](y_max) - y_axis['dataToCoord'](y_min))

height_diff = y_data[1]-y_data[0]
# pix_diff = 0
scale = pix_diff / height_diff

for x in cdk_list:
    mid = (x['high'] + x['low']) / 2
    width = (x['high'] - x['low'])*scale
    cdk_dts = [x['dt1'], x['dt2']]
    cdk_val = [mid, mid]

    line1 = Line()
    line1.add_xaxis(cdk_dts)
    line1.add_yaxis(series_name="CDK", y_axis=cdk_val, is_selected=True,
                        label_opts=opts.LabelOpts(is_show=False),
                        linestyle_opts=opts.LineStyleOpts(color="yellow", width=width, opacity=0.5))

# for cdk in cdk_list:
#     line1 = Line()
#     x_data = [cdk['dt1'], cdk['dt2'], cdk['dt2'], cdk['dt1'], cdk['dt1']]
#     y_data = [cdk['low'], cdk['low'], cdk['high'], cdk['high'], cdk['low']]
#     line1.add_xaxis(x_data)
#     line1.add_yaxis("价格", y_data, is_connect_nones=True, is_smooth=True)

    line.overlap(line1)

# line = Line()
# for cdk in cdk_list:
#     x_data = [cdk['dt1'], cdk['dt2'], cdk['dt2'], cdk['dt1'], cdk['dt1']]
#     y_data = [cdk['low'], cdk['low'], cdk['high'], cdk['high'], cdk['low']]
#     line.add_xaxis(x_data)
#     line.add_yaxis("价格", y_data, is_connect_nones=True, is_smooth=True)
#
line.set_global_opts(
    xaxis_opts=opts.AxisOpts(type_="category"),
    yaxis_opts=opts.AxisOpts(type_="value"),
    title_opts=opts.TitleOpts(title="CDK Chart"),
)

line2 = Line()
x_data = ["2021/1/1", "2021/3/31"]
y_data = [0, 120]
line2.add_xaxis(x_data)
line2.add_yaxis("", y_data, is_connect_nones=True, is_smooth=True)


line.overlap(line2)
# line.render("cdk_chart.html")

home_path = os.path.expanduser("~")
file_html = os.path.join(home_path, "test_cdk.html")
line.render(file_html)
webbrowser.open(file_html)

