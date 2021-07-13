# -*- coding: utf-8 -*-
"""

@author: John Kakareka

test real-time plotting
"""
import wx
import time

from pyPerfusion.plotting import SensorPlot, EventPlot, PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils


acq = AI(100)
sensor = SensorStream('test', 'ml/min', acq)

evt_acq = AI(1000, read_period_ms=1000)
evt = SensorPoint('Insulin Injection', 'ml', evt_acq)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotevt = EventPlot(evt, self.panel.axes)
        self.plotraw = SensorPlot(sensor, self.panel.axes)

        sensor.hw.add_channel(0)
        sensor.set_ch_id(0)
        sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        evt.hw.add_channel(0)
        evt.set_ch_id(0)
        evt.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test', sensor.params)
        sensor.add_strategy(strategy)

        strategy = PointsToFile('Event', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test_event', evt.params)
        evt.add_strategy(strategy)

        self.plotevt.set_strategy(evt.get_file_strategy('Event'), color='r')
        self.plotraw.set_strategy(sensor.get_file_strategy('Raw'), color='b')

        self.panel.add_plot(self.plotevt)
        self.panel.add_plot(self.plotraw)

        sensor.open()
        evt.open()

        sensor.hw.open()
        evt.hw.open()
        sensor.hw.start()
        evt.hw.start()
        sensor.start()
        evt.start()

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

