# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Panel class for plotting data
"""
import wx
from enum import Enum

import numpy as np
import matplotlib as mpl
from cycler import cycler
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx


class DummyPerfusionSensors:
    ha_flow = [1] * 100
    pv_flow = [4] * 100


class PanelPlotting(wx.Panel):
    def __init__(self, parent, perfusion_sensors):
        self.parent = parent
        self._sensors = perfusion_sensors
        wx.Panel.__init__(self, parent, -1)

        self.fig = mpl.figure.Figure()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.canvas.SetMinSize(wx.Size(1, 1))
        self.fig.tight_layout()
        self.plot_len = 1000
        self.lines = [None] * 8
        self.colors = ['red', 'green', 'blue', 'black',
                       'magenta', 'orange', 'brown', 'cyan', 'black',
                       'blue', 'red']
        self.linestyles = ['-', '-.']

        # self.toolbar = NavigationToolbar2Wx(self.canvas)
        # self.toolbar.Realize()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        parameters = ["HA Flow", "PV Flow", "HA Pressure", "PV Pressure"]
        self.choice_plot_parameter = wx.Choice(self, choices=parameters)
        self.choice_plot_parameter.SetSelection(1)
        font = self.choice_plot_parameter.GetFont()
        font.SetPointSize(20)
        self.choice_plot_parameter.SetFont(font)

        self.__do_layout()
        # self.__set_bindings()
        self.axes = self.fig.add_subplot(111)
        self.setup_plotlines()

    def __do_layout(self):

        self.sizer.Add(self.choice_plot_parameter, wx.SizerFlags().CenterHorizontal())
        # self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    # def __set_bindings(self):
        # set bindings if needed

    def setup_plotlines(self):
        self.axes.clear()
        self.lines = [[None] * 2 for i in range(11)]
        for i in range(11):
            for j in range(2):
                line = self.axes.plot([0]*self.plot_len,
                                      linestyle=self.linestyles[j],
                                      color=self.colors[i],
                                      visible=False)[0]
                self.lines[i][j] = line

    def plot_pos(self, pos, sector, data):
        self.canvas.draw()


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
