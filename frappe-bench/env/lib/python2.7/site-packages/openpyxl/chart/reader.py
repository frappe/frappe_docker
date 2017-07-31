from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""
Read a chart
"""

from .chartspace import ChartSpace, PlotArea
from openpyxl.xml.functions import fromstring

_types = ('areaChart', 'area3DChart', 'lineChart', 'line3DChart',
         'stockChart', 'radarChart', 'scatterChart', 'pieChart', 'pie3DChart',
         'doughnutChart', 'barChart', 'bar3DChart', 'ofPieChart', 'surfaceChart',
         'surface3DChart', 'bubbleChart',)

_axes = ('valAx', 'catAx', 'dateAx', 'serAx',)


def reader(src):
    node = fromstring(src)
    cs = ChartSpace.from_tree(node)
    plot = cs.chart.plotArea
    for t in _types:
        chart = getattr(plot, t, None)
        if chart is not None:
            break # this ignores multiple charts

    chart.title = cs.chart.title
    chart.layout = plot.layout
    chart.legend = cs.chart.legend

    for x in _axes:
        ax = getattr(plot, x)
        if ax:
            if x == 'valAx':
                chart.y_axis = ax[0]
            elif x == 'serAx':
                chart.z_axis = ax[0]
            else:
                chart.x_axis = ax[0]
    return chart
