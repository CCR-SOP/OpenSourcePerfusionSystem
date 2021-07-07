# -*- coding: utf-8 -*-
"""Test script for testing plotting of SensorStream

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import time
import logging

from pyPerfusion.plotting import PanelPlotting
from pyPerfusion.plotting import SensorPlot, PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.utils as utils


utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

acq = AI(100)
sensor = SensorStream('test', 'ml/min', acq)

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        sensor.hw.add_channel(0)
        sensor.set_ch_id(0)
        sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        strategy = StreamToFile('StreamToFileRaw', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test',
                      {'Sampling Period (ms)': acq.period_sampling_ms, 'Data Format': 'float32'})
        sensor.add_strategy(strategy)
        self.panel = PanelPlotting(self)
        self.plot = SensorPlot(sensor, self.panel.axes, frame_ms=2_000)
        self.plot.set_strategy(strategy)
        self.panel.add_plot(self.plot)

        sensor.open(LP_CFG.LP_PATH['stream'])

        sensor.hw.open()
        sensor.hw.start()
        sensor.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        self.panel.Destroy()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
time.sleep(100)
sensor.stop()

