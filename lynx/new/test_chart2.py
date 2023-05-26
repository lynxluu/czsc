from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode
from pyecharts.options.charts_options import GraphicItemOpts

line = (
    Line()
    .add_xaxis(xaxis_data=[1])
    .add_yaxis(
        series_name="",
        y_axis=[],
        markline_opts=opts.MarkLineOpts(
            symbol=["none", "none"],
            # data=[opts.MarkLineItem(x="50%", name="矩形", symbol_size=20, label_opts=None)],
            data=[opts.MarkLineItem(x="50%", name="矩形", symbol_size=20)],
            linestyle_opts=opts.LineStyleOpts(color="red", width=1, type_="dashed"),
        ),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="绘制矩形"),
        tooltip_opts=opts.TooltipOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(is_show=False),
        yaxis_opts=opts.AxisOpts(is_show=False),
        legend_opts=opts.LegendOpts(is_show=False),
        graphic_opts=[
            opts.GraphicGroup(
                graphic_item=opts.GraphicRect(
                # graphic_item=opts.charts_options.GraphicRect(
                    graphic_item_opts=opts.GraphicItemOpts(
                        id_="rect", width=100, height=100, x=JsCode("190"), y=JsCode("60")
                    ),
                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                        fill="red", stroke="blue", line_width=2, shadow_blur=10
                    ),
                )
            )
        ],
    )
)

line.render("custom_rect_chart.html")