# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for plotting data
"""
import wx

import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
# from matplotlib.backends.backend_wx import NavigationToolbar2Wx


class DummyPerfusionSensors:
    time = {}
    data = {}

    time['HA Flow'] = np.arange(0, 10, 0.001)
    data['HA Flow'] = np.sin(2 * np.pi * time['HA Flow'])

    time['PV Flow'] = np.arange(0, 10, 0.001)
    data['PV Flow'] = np.sin(0.1 * 2 * np.pi * time['PV Flow'])


class PanelPlotting(wx.Panel):
    def __init__(self, parent, perfusion_sensors):
        self.parent = parent
        self._sensors = perfusion_sensors
        self.sensor_name = ''
        wx.Panel.__init__(self, parent, -1)

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.canvas.SetMinSize(wx.Size(1, 1))
        self.fig.tight_layout()

        # self.toolbar = NavigationToolbar2Wx(self.canvas)
        # self.toolbar.Realize()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        parameters = list(self._sensors.time.keys())
        self.choice_plot_parameter = wx.Choice(self, choices=parameters)
        self.choice_plot_parameter.SetSelection(1)
        self.sensor_name = parameters[1]
        font = self.choice_plot_parameter.GetFont()
        font.SetPointSize(20)
        self.choice_plot_parameter.SetFont(font)

        self.__do_layout()
        self.__set_bindings()
        self.axes = self.fig.add_subplot(111)

        self.timer_plot = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer_plot.Start(100, wx.TIMER_CONTINUOUS)

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
        new_name = self.choice_plot_parameter.GetStringSelection()
        print(f'{new_name}')
        if not new_name == self.sensor_name:
            self.sensor_name = new_name
            self.axes.clear()

    def plot(self, sensor_name):
        self.axes.plot(self._sensors.time[sensor_name], self._sensors.data[sensor_name], color='green')
        self.canvas.draw()

    def OnTimer(self, event):
        if event.GetId() == self.timer_plot.GetId():
            self.plot(self.sensor_name)



class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self, DummyPerfusionSensors())


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
