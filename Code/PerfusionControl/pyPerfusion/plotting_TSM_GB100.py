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

    def plot(self, value, time):
        for plot in self._plots:
            plot.plot(value, time)

        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()
        self.show_legend()

    def show_legend(self):
        total_plots = len(self._plots)
        ncols = total_plots if total_plots % 2 == 0 else total_plots + 1
        if self._axes.lines:
            self._axes.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=ncols, mode="expand",
                              borderaxespad=0, framealpha=0.0, fontsize='x-small')

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
    def __init__(self, plot_name, axes, readout=True):
        self._lgr = logging.getLogger(__name__)
        self._plot_name = plot_name
        self._axes = axes
        self._line = None
        self._invalid = None
        self._display = None
        self._color = None
        self._with_readout = readout

    @property
    def full_name(self):
        return self._plot_name

    def plot(self, value, time):
        readout_color = 'black'
        if value is None or len(value) == 0:
            return
        if time is None or len(time) == 0:
            return
        if self._line is None:
            self._line, = self._axes.plot(value, time, color='black', marker='o', xdate=True)