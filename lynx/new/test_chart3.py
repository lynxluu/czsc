from pyecharts.charts.chart import RectChart
from pyecharts.options import GraphicItem, GraphicRect

class CustomRectChart(RectChart):
    def add_rectangle(self, x, y, width, height, color, border_width):
        rect = GraphicRect(
            # shape_opts={"x": x, "y": y, "width": width, "height": height},
            # style_opts={"fill": color, "stroke": color, "lineWidth": border_width},
            graphic_shape_opts={"x": x, "y": y, "width": width, "height": height},
            graphic_basicstyle_opts={"fill": color, "stroke": color, "lineWidth": border_width},
        )
        self.options.update({"graphic": [rect]})
        return self

chart = CustomRectChart()
chart.add_rectangle(10, 60, 50, 150, "red", 2)
chart.render('rect3.html')
