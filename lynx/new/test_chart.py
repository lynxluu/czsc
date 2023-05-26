
cdk_list = [
    {"dt1": "2021/1/1", "dt2": "2021/1/8", "low": 80, "high": 120},
    {"dt1": "2021/1/9", "dt2": "2021/1/15", "low": 50, "high": 100},
    {"dt1": "2021/1/20", "dt2": "2021/1/26", "low": 60, "high": 110},
]


import pyecharts.options as opts
from pyecharts.charts import Line
from datetime import datetime


from pyecharts.charts.chart import RectChart
from pyecharts import options as opts


class CustomRectChart(RectChart):
    def __init__(self):
        super().__init__()
        self.js_dependencies.add('echarts/lib/draw/rect')

    def add(self, *args, **kwargs):
        """
        添加矩形。用法与其他Chart类似。
        :param args:
        :param kwargs:
        :return:
        """
        self.__rect_args_check(kwargs)

        # 定义矩形默认样式
        item_style = {}
        item_style.update(color='rgba(255,0,0,0.4)')
        item_style.update(**kwargs.get('itemstyle_opts', {}))

        # 定义默认的z轴参数
        z_level = kwargs.pop('z_level', 0)

        # 定义矩形位置和大小
        rect_info = {}
        rect_info.update(x=kwargs.pop('x', ''))
        rect_info.update(y=kwargs.pop('y', ''))
        rect_info.update(width=kwargs.pop('width', ''))
        rect_info.update(height=kwargs.pop('height', ''))
        rect_info.update(itemStyle=item_style)

        self.options.get('series').append(
            {
                "type": "rect",
                "zlevel": z_level,
                # "label": self._get_all_options_label(kwargs),
                # "tooltip": self._get_all_options_tooltip(kwargs),
                "symbol": 'circle',
                "symbolSize": 10,
                "data": [rect_info]
            }
        )

        if kwargs.get("is_selected") is not False:
            self.selected_mode = kwargs.get("selected_mode") or True
        return self


    def __rect_args_check(self, kwargs):
        """
        矩形参数有效性校验。
        """
        if 'x' not in kwargs:
            raise TypeError('添加矩形必须指定x轴坐标')
        if 'y' not in kwargs:
            raise TypeError('添加矩形必须指定y轴坐标')
        if 'width' not in kwargs:
            raise TypeError('添加矩形必须指定矩形宽度')
        if 'height' not in kwargs:
            raise TypeError('添加矩形必须指定矩形高度')



def draw_rectangles(cdk_list):
    """Draw rectangles using pyechart."""

    line = CustomRectChart()
    date_format = "%Y/%m/%d"


    # Iterate through the elements of cdk_list to draw all the rectangles.
    for item in cdk_list:
        # 解析日期
        dt1 = datetime.strptime(item['dt1'], date_format)
        dt2 = datetime.strptime(item['dt2'], date_format)
        x_coordinate = dt1
        y_coordinate = item["low"]
        length = dt2-dt1
        width = item["high"] - item["low"]

        # Draw a rectangle with x-coordinate dt1 and y-coordinate low,
        # with a length of dt2-dt1 and a width of high-low.
        line.add(
            x=x_coordinate,
            y=y_coordinate,
            width=width,
            height=length,
            color="#0000FF",
        )

    return line


if __name__ == "__main__":
    cdk_list = [
        {"dt1": "2021/1/1", "dt2": "2021/1/8", "low": 80, "high": 120},
        {"dt1": "2021/1/9", "dt2": "2021/1/15", "low": 50, "high": 100},
        {"dt1": "2021/1/20", "dt2": "2021/1/26", "low": 60, "high": 110},
    ]

    line = draw_rectangles(cdk_list)
    line.render("rectangles.html")
