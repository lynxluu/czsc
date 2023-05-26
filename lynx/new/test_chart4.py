from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode

cdk_list = [
    {"dt1": "2021/1/1", "dt2": "2021/1/8", "low": 80, "high": 120},
    {"dt1": "2021/1/9", "dt2": "2021/1/15", "low": 50, "high": 100},
    {"dt1": "2021/1/20", "dt2": "2021/1/26", "low": 60, "high": 110},
]

graphic_items = []
for item in cdk_list:
    rect = opts.GraphicRect(
        graphic_item={
            "id": f"rect_{item['dt1']}",
            "width": (item["high"] - item["low"]) * 10,
            "height": 20,
            "x": JsCode(f"{item['low']} * 10"),
            "y": JsCode("60"),
        },
        graphic_basicstyle_opts={
            "fill": "red",
            "stroke": "blue",
            "lineWidth": 2,
            "shadowBlur": 10,
        },
    )
    graphic_items.append(rect)

line = (
    Line()
    .add_xaxis(xaxis_data=[item["dt1"] for item in cdk_list])
    .add_yaxis(series_name="", y_axis=[])
    .set_global_opts(
        title_opts=opts.TitleOpts(title="绘制矩形"),
        tooltip_opts=opts.TooltipOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(is_show=False),
        yaxis_opts=opts.AxisOpts(is_show=False),
        legend_opts=opts.LegendOpts(is_show=False),
        graphic_opts=graphic_items,
    )
)

line.render("rect4.html")
