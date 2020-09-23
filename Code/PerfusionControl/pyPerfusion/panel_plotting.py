# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for plotting data
"""
from enum import Enum
import wx
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
# from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint


class PlotFrame(Enum):
    FROM_START = 0
    LAST_SECOND = 1_000
    LAST_5_SECONDS = 5_000
    LAST_MINUTE = 60_000


class PanelPlotting(wx.Panel):
    def __init__(self, parent):
        self.__parent = parent
        self.__sensors = []
        wx.Panel.__init__(self, parent, -1)
        self.__plot_frame = PlotFrame.LAST_5_SECONDS
        self.__plot_len = 200

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.canvas.SetMinSize(wx.Size(1, 1))
        self.fig.tight_layout()

        # self.toolbar = NavigationToolbar2Wx(self.canvas)
        # self.toolbar.Realize()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        parameters = [item.name for item in PlotFrame]
        self.choice_plot_parameter = wx.Choice(self, choices=parameters)
        self.choice_plot_parameter.SetStringSelection(self.__plot_frame.name)
        font = self.choice_plot_parameter.GetFont()
        font.SetPointSize(20)
        self.choice_plot_parameter.SetFont(font)

        self.__do_layout()
        self.__set_bindings()
        self.axes = self.fig.add_subplot(6, 1, (1, 4))
        self.axes_lt = self.fig.add_subplot(6, 1, 6)
        self.__line = {}
        self.__line_lt = {}

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_plot.Start(200, wx.TIMER_CONTINUOUS)

    def __do_layout(self):
        self.sizer.Add(self.choice_plot_parameter, wx.SizerFlags().CenterHorizontal())
        # self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def __set_bindings(self):
        self.choice_plot_parameter.Bind(wx.EVT_CHOICE, self.OnPlotChoiceChange)

    def OnPlotChoiceChange(self, event):
        self.__plot_frame = PlotFrame[self.choice_plot_parameter.GetStringSelection()]
        # self.axes.clear()

    def plot(self):
        min_x = []
        max_x = []
        min_y = []
        max_y = []
        for sensor in self.__sensors:
            data_time, data = sensor.get_data(self.__plot_frame.value, self.__plot_len)
            if data is not None and len(data) > 0:
                if type(sensor) is SensorStream:
                    self.plot_stream(self.__line[sensor.name], data_time, data)
                    min_y.append(np.min(data))
                    max_y.append(np.max(data))
                    min_x.append(data_time[0])
                    max_x.append(data_time[-1])
                elif type(sensor) is SensorPoint:
                    self.plot_event(sensor, data_time, data)
            lt_t, lt = sensor.get_data(PlotFrame.FROM_START.value, self.__plot_len)
            if lt is not None and len(lt) > 0:
                if type(sensor) is SensorStream:
                    self.plot_stream(self.__line_lt[sensor.name], lt_t, lt)
                    self.axes_lt.set_ylim(min(lt) * 0.9, max(lt) * 1.1)
                    self.axes_lt.set_xlim(lt_t[0], lt_t[-1])
                    # self.canvas.draw()
        if len(min_y) > 0:
            self.axes.set_ylim(min(min_y) * 0.9, max(max_y) * 1.1)
            self.axes.set_xlim(min(min_x), max(max_x))
            self.canvas.draw()

    def plot_stream(self, line, data_time, data):
        if line is not None:
            line.set_data(data_time, data)

    def plot_event(self, sensor, data_time, data):
        # del self.__line[sensor.name]
        self.__line[sensor.name] = self.axes.vlines(data_time, ymin=0, ymax=100, color='red')

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot()

    def add_sensor(self, sensor):
        assert isinstance(sensor, SensorStream)
        self.__sensors.append(sensor)
        if type(sensor) is SensorStream:
            self.__line[sensor.name], = self.axes.plot([0] * self.__plot_len)
            self.__line_lt[sensor.name], = self.axes_lt.plot([0] * self.__plot_len)
            self.axes_lt.set_yticklabels([])
            self.axes_lt.set_xticklabels([])
            self.axes.set_title(sensor.name)
            self.axes.set_ylabel(sensor.unit_str)

        elif type(sensor) is SensorPoint:
            # self.__line[sensor.name], = self.axes.plot([0] * sensor.buf_len, 's')
            self.__line[sensor.name] = self.axes.vlines(0, ymin=0, ymax=100, color='red')


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
    app = MyTestApp(0)
    app.MainLoop()
