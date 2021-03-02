# -*- coding: utf-8 -*-
"""

@author: John Kakareka

test real-time plotting
"""
import wx
import time

from pyPerfusion.panel_plotting import PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG



class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self._plots = []

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        self.hw = AI(period_sample_ms=10)
        self.sensors = [
            SensorStream('HA Flow', 'ml/min', self.hw),
            SensorStream('PV Flow', 'ml/min', self.hw)
        ]

        [sensor.open(LP_CFG.LP_PATH['stream']) for sensor in self.sensors]

        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(self.sensors):
            panel = PanelPlotting(self)
            self._plots.append(panel)
            sensor.hw.add_channel(idx)
            sensor.set_ch_id(idx)
            panel.add_sensor(sensor)
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            sensor.start()

        self.sensors[0].hw.set_demo_properties(0, demo_amp=80, demo_offset=0)
        self.sensors[1].hw.set_demo_properties(1, demo_amp=40, demo_offset=20)

        self.hw.open()
        self.hw.start()

        self.SetSizer(sizer_plots)
        self.Fit()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        self.hw.close()
        for plot in self._plots:
            plot.Destroy()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()

        return True


app = MyTestApp(0)
app.MainLoop()
