"""QtCharts 封装：柱状图 / 折线图 / 饼图，全部由真实聚合结果驱动。"""

from PySide6.QtCharts import (QBarCategoryAxis, QBarSeries, QBarSet, QCategoryAxis, QChart,
                              QChartView, QLineSeries, QPieSeries, QValueAxis)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter

PALETTE = ["#2563EB", "#0F766E", "#D97706", "#7C3AED", "#DC2626", "#0891B2"]


def _finish(chart, view):
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.legend().setVisible(False)
    chart.setBackgroundRoundness(8)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(260)
    return view


def bar_chart(title, labels, values, color="#2563EB"):
    series = QBarSeries()
    bar_set = QBarSet("数值")
    bar_set.setColor(QColor(color))
    bar_set.append([float(value or 0) for value in values])
    series.append(bar_set)
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    axis_x = QBarCategoryAxis()
    axis_x.append([str(label) for label in labels] or [""])
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)
    axis_y = QValueAxis()
    top = max([float(value or 0) for value in values] or [1])
    axis_y.setRange(0, top * 1.2 if top else 1)
    axis_y.setLabelFormat("%.0f")
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)
    view = QChartView(chart)
    return _finish(chart, view)


def line_chart(title, labels, values, color="#2563EB"):
    series = QLineSeries()
    series.setColor(QColor(color))
    for index, value in enumerate(values):
        series.append(index, float(value or 0))
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    axis_y = QValueAxis()
    top = max([float(value or 0) for value in values] or [1])
    axis_y.setRange(0, top * 1.2 if top else 1)
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_y)
    axis_x = QCategoryAxis()
    axis_x.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
    for index, label in enumerate(labels):
        axis_x.append(str(label), index)
    axis_x.setRange(0, max(1, len(labels) - 1))
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)
    view = QChartView(chart)
    return _finish(chart, view)


def pie_chart(title, labels, values):
    series = QPieSeries()
    for index, (label, value) in enumerate(zip(labels, values)):
        slice_ = series.append(f"{label} ({value})", float(value or 0))
        slice_.setLabelVisible(True)
        slice_.setBrush(QColor(PALETTE[index % len(PALETTE)]))
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.legend().setVisible(True)
    view = QChartView(chart)
    return _finish(chart, view)
