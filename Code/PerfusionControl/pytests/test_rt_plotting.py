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


acq = HWAcq(10, demo_amp = 20, demo_offset=60)
sensor = SensorStream('test', 'ml/min', acq, valid_range=[65, 75])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self)
        self.panel.add_sensor(sensor)
        sensor.start()
        sensor.open(Path('./__data__'), Path('2020-09-14'))


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

