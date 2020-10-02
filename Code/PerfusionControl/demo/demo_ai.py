# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots created with real data
"""
import wx
import time
from pathlib import Path

from pyPerfusion.panel_plotting import PanelPlotting
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream

sensors = [
          SensorStream('Analog Input 1', 'Volts', NIDAQ_AI(0, 10, volts_p2p=5, volts_offset=2.5, dev='Dev1'))
         ]


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)

        for sensor in sensors:
            panel = PanelPlotting(self)
            panel.add_sensor(sensor)
            sensor.open(Path('./__data__'), Path('yyyy-mm-dd'))
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

