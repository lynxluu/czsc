from pyecharts.charts import Line
from pyecharts import options as opts

cdk_list = [
    {"dt1": "2021/1/1", "dt2": "2021/1/8", "low": 80, "high": 120},
    {"dt1": "2021/1/9", "dt2": "2021/1/15", "low": 50, "high": 100},
    {"dt1":"2021/1/20", "dt2": "2021/1/26", "low": 60, "high": 110},
]


line = Line()
for cdk in cdk_list:
    line1 = Line()
    x_data = [cdk['dt1'], cdk['dt2'], cdk['dt2'], cdk['dt1'], cdk['dt1']]
    y_data = [cdk['low'], cdk['low'], cdk['high'], cdk['high'], cdk['low']]
    line1.add_xaxis(x_data)
    line1.add_yaxis("价格", y_data, is_connect_nones=True, is_smooth=True)

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
line.render("cdk_chart.html")
