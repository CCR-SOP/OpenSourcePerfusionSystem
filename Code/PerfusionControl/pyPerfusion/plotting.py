# -*- coding: utf-8 -*-
"""Panel class for plotting data real-time

Based on wx.Panel, this plots data real-time using SensorStream
and/or SensorPoint objects

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import matplotlib.transforms as mtransforms
# from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
from pyHardware.PHDserial import PHDserial

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as LP_CFG
from pyHardware.PHDserial import PHDserial

class SensorPlot:
    def __init__(self, sensor, axes, frame_ms=200, plot_len=200):
        self._lgr = logging.getLogger(__name__)
        self._sensor = sensor
        self._strategy = None
        self._axes = axes
        self._line = None
        self._invalid = None
        self._display = None
        self._shaded = None
        self._frame_ms = frame_ms
        self._plot_len = plot_len

    def plot(self):
        color = 'black'
        data_time, data = self._strategy.retrieve_buffer(self._frame_ms, self._plot_len)
        if data is None or len(data) == 0:
            return
        if self._sensor.valid_range is not None:
            low_range = self._axes.fill_between(data_time, data, self._sensor.valid_range[0],
                                                where=data < self._sensor.valid_range[0], color='r')
            high_range = self._axes.fill_between(data_time, data, self._sensor.valid_range[1],
                                                 where=data > self._sensor.valid_range[1], color='r')
            self._invalid = [low_range, high_range]

        self._line.set_data(data_time, data)
        try:
            self._axes.collections.remove(self._invalid)
        except ValueError:
            pass

    def set_strategy(self, strategy, color='r'):
        self._strategy = strategy
        self._line, = self._axes.plot([0] * self._plot_len)
        if self._sensor.valid_range is not None:
            rng = self._sensor.valid_range
            self._shaded['normal'] = self._axes.axhspan(rng[0], rng[1], color='g', alpha=0.2)
        self._axes.set_title(self._sensor.name)
        self._axes.set_ylabel(self._sensor.unit_str)


class PanelPlotting(wx.Panel):
    def __init__(self, parent, with_readout=True):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.__parent = parent
        self.__sensors = []
        self._with_readout = with_readout

        self.__plot_len = 200
        self._valid_range = None
        self._plot_frame_ms = 5_000

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self._axes = self.fig.add_subplot(111)
        self._plots = []

        self.list_strategy = wx.ListBox(self, wx.ID_ANY)

        self.__do_layout()
        self.__set_bindings()

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_plot.Start(200, wx.TIMER_CONTINUOUS)

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
        sizer.Add(self.list_strategy, 1, wx.ALL)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        pass

    def plot(self):
        for plot in self._plots:
            plot.plot()

        self._axes.relim()
        self._axes.autoscale_view()
        self.canvas.draw()

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def show_legend(self):
        self._axes.legend(loc='lower left', bbox_to_anchor=(0.0, 1.01, 1.0, .102), ncol=2, mode="expand",
                         borderaxespad=0, framealpha=0.0, fontsize='x-small')

    def add_plot(self, plot):
        self._plots.append(plot)

class PanelPlotLT(PanelPlotting):
    def __init__(self, parent):
        PanelPlotting.__init__(self, parent, with_readout=False)

    def _configure_plot(self, sensor):
        self.axes.set_yticklabels([])
        self.axes.set_xticklabels([])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()
