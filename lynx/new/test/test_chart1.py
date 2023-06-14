import os
import webbrowser

from pyecharts import options as opts
from pyecharts.charts import Line

# 定义包含四个长方形信息的列表
rectangles = [
    {"x": 10, "y": 10, "w": 50, "h": 30},
    {"x": 30, "y": 50, "w": 40, "h": 20},
    {"x": 60, "y": 20, "w": 30, "h": 40},
    {"x": 80, "y": 70, "w": 20, "h": 30},
]



# 创建Line对象
line = Line()

# 遍历长方形列表
for rect in rectangles:
    # 计算长方形的四个顶点坐标
    x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
    points = [
        [x, y],
        [x + w, y],
        [x + w, y + h],
        [x, y + h],
        [x, y]
    ]
    # 添加坐标点
    # print(points)
    line.add_xaxis([p[0] for p in points])
    line.add_yaxis("矩形图", [p[1] for p in points],linestyle_opts=opts.LineStyleOpts(color="red"),label_opts=opts.LabelOpts(is_show=False))

# 创建折线图
line1 = Line()
line1.add_xaxis([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
line1.add_yaxis("折线图", [20, 40, 60, 80, 100, 120, 140, 160, 180, 200],label_opts=opts.LabelOpts(is_show=False))


# 设置全局配置
line.set_global_opts(
    title_opts=opts.TitleOpts(title="全部图"),
    xaxis_opts=opts.AxisOpts(name='横坐标',min_=0, max_='dataMax', type_="value",axislabel_opts={"rotate":45}),
    yaxis_opts=opts.AxisOpts(name='纵坐标', min_=0, max_='dataMax',type_="value"),
)

# 叠加渲染图表
line.overlap(line1)
# line.render("rect1.html")

home_path = os.path.expanduser("~")
file_html = os.path.join(home_path, "test_cdk.html")
line.render(file_html)
webbrowser.open(file_html)