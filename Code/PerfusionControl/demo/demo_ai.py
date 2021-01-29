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
import pyPerfusion.PerfusionConfig as LP_CFG

sensors = [
          SensorStream('Analog Input 1', 'Volts', NIDAQ_AI(0, 10, volts_p2p=5, volts_offset=2.5, dev='Dev3'))
         ]


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        for sensor in sensors:
            panel = PanelPlotting(self)
            panel.add_sensor(sensor)

            sensor.open(LP_CFG.LP_PATH['stream'])
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        for sensor in sensors:
            sensor.start()
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in sensors:
            sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
