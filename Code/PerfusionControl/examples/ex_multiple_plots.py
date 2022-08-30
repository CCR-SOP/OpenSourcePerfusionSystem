# -*- coding: utf-8 -*-
""" Demonstrate plotting to multiple plots

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import time

from pyPerfusion.plotting import PanelPlotting, SensorPlot
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile
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
        for sensor in self.sensors:
            strategy = StreamToFile('Raw', 1, 10)
            strategy.open(LP_CFG.LP_PATH['stream'], sensor.name, sensor.params)
            sensor.add_strategy(strategy)
            sensor.open()

        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(self.sensors):
            panel = PanelPlotting(self)
            self._plots.append(panel)
            sensor.hw.add_channel(idx)
            sensor.set_ch_id(idx)
            plot = SensorPlot(sensor, panel.axes, readout=True)
            plot.set_strategy(sensor.get_file_strategy('Raw'))
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            panel.add_plot(plot)
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
