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
from pyPerfusion.SensorPoint import SensorPoint


acq = HWAcq(100)
sensor = SensorStream('test', 'ml/min', acq)

evt_acq = HWAcq(500)
evt = SensorPoint('Insulin Injection', 'ml', evt_acq)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self)
        self.panel.add_sensor(sensor)
        self.panel.add_sensor(evt)
        sensor.start()
        sensor.open(Path('./__data__'), Path('2020-09-14'))
        evt.start()
        evt.open(Path('./__data__'), Path('2020-09-14'))


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

