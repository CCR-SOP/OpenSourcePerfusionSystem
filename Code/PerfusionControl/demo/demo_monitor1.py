# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots screen with full array of different sensors
"""
import wx
import time
from pathlib import Path

from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.panel_readout import PanelReadout
from pyPerfusion.HWAcq import HWAcq
from pyPerfusion.SensorStream import SensorStream

sensors = [
          SensorStream('HA Flow', 'ml/min', HWAcq(10, demo_amp=80, demo_offset=0), valid_range=[20, 60]),
          SensorStream('PV Flow', 'ml/min', HWAcq(10, demo_amp=40, demo_offset=20), valid_range=[25, 35]),
          SensorStream('HA Pressure', 'mmHg', HWAcq(10, demo_amp=100, demo_offset=0), valid_range=[40, 60]),
          SensorStream('PV Pressure', 'mmHg', HWAcq(10, demo_amp=10, demo_offset=0), valid_range=[3, 7])
         ]


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer_main = wx.BoxSizer(wx.HORIZONTAL)

        sizer_plots = wx.GridSizer(cols=2)
        for sensor in sensors:
            panel = PanelPlotting(self)
            panel.add_sensor(sensor)

            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        sizer_readout = wx.GridSizer(cols=1)
        for sensor in sensors:
            panel = PanelReadout(self, sensor)
            sizer_readout.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        sizer_main.Add(sizer_plots, 1, wx.ALL | wx.EXPAND)
        sizer_main.Add(sizer_readout)
        self.SetSizer(sizer_main)
        self.Fit()
        self.Layout()
        self.Maximize(True)

        [sensor.open(Path('./__data__'), Path('yyyy-mm-dd')) for sensor in sensors]
        [sensor.start() for sensor in sensors]


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
time.sleep(10)
[sensor.stop() for sensor in sensors]


