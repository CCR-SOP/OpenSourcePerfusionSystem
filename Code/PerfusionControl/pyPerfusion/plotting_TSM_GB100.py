# -*- coding: utf-8 -*-
"""Panel class for plotting data from TSM in real-time

Based on wx.Panel, this plots data real-time using TSMSerial object

@project: LiverPerfusion NIH
@author: Allen Luna, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

class TSMPanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.__parent = parent
        self._with_readout = with_readout

        self.__plot_len = 200
        self._valid_range = None
        self._plot_frame_ms = 5_000

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        # self._axes = self.fig.add_subplot(111)
        self._axes = self.fig.add_axes([0.05, 0.05, 0.9, 0.85])
        self._plots = []
        self._leg = []

        self.__do_layout()
        self.__set_bindings()

    @property
    def axes(self):
        return self._axes

    @property
    def plot_frame_ms(self):
        return self._plot_frame_ms

    @plot_frame_ms.setter
    def plot_frame_ms(self, ms):
        self._plot_frame_ms = ms

    def __do_layout(self):
        self.canvas.SetMinSize(wx.Size(1, 1))
        self.fig.tight_layout()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.canvas, 10, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        pass

    def plot(self, data, data_time):
        for plot in self._plots:
            plot.plot(data, data_time)

        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()

    def add_plot(self, plot):
        self._plots.append(plot)
        self.Fit()
        self.__parent.Fit()

class TSMPanelPlotLT(TSMPanelPlotting):
    def __init__(self, parent):
        TSMPanelPlotting.__init__(self, parent, with_readout=False)

    def _configure_plot(self, sensor):
        self.axes.set_yticklabels([])
        self.axes.set_xticklabels([])

class TSMSensorPlot:
    def __init__(self, plot_name, axes, unit):
        self._lgr = logging.getLogger(__name__)
        self._plot_name = plot_name
        self._axes = axes
        self._unit = unit
        self._configure_plot()

    @property
    def full_name(self):
        return self._plot_name

    def plot(self, data, data_time):
        if data is None:
            return
        if data_time is None:
            return
        self._axes.plot(data_time, data, 'ko')

    def _configure_plot(self):
        self._axes.set_title(self._plot_name)
        self._axes.set_ylabel(self._unit)
