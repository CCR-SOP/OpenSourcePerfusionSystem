# -*- coding: utf-8 -*-
"""

@author: John Kakareka

test real-time plotting
"""
import wx
import time
from pathlib import Path

from pyPerfusion.panel_plotting import PanelPlotting
from pyPerfusion.HWAcq import HWAcq
from pyPerfusion.SensorStream import SensorStream


sensors = []
sensors.append(SensorStream('HA Flow', 'ml/min', HWAcq(10)))
sensors.append(SensorStream('PV Flow', 'ml/min', HWAcq(20)))


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer_plots = wx.GridSizer(cols=2)
        for sensor in sensors:
            panel = PanelPlotting(self)
            panel.add_sensor(sensor)
            sensor.start()
            sensor.open(Path('./'), Path('2020-09-14'))
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        self.SetSizer(sizer_plots)
        self.Fit()
        self.Layout()


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


