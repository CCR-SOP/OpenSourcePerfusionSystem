# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots screen with full array of different sensors
"""
import wx
import time
from pathlib import Path

from pyPerfusion.panel_plotting import PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream

sensors = [
          SensorStream('HA Flow', 'ml/min', AI(10, demo_amp=80, demo_offset=0)),
          SensorStream('PV Flow', 'ml/min', AI(10, demo_amp=40, demo_offset=20)),
          SensorStream('HA Pressure', 'mmHg', AI(10, demo_amp=100, demo_offset=0)),
          SensorStream('PV Pressure', 'mmHg', AI(10, demo_amp=10, demo_offset=0))
         ]


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)

        for sensor in sensors:
            panel = PanelPlotting(self)
            panel.add_sensor(sensor)
            sensor.open(Path('./__data__'), Path('2020-09-14'))
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        for sensor in sensors:
            sensor.start()
        self.SetSizer(sizer)
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
sensor.stop()

