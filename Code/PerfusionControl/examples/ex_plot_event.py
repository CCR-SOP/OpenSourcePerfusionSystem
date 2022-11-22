# -*- coding: utf-8 -*-
""" Demonstrate plotting events

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging

from pyPerfusion.plotting import SensorPlot, EventPlot, PanelPlotting
import pyHardware.pyAI as pyAI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile
import pyPerfusion.utils as utils


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.hw = pyAI.AIDevice()
        dev_cfg = pyAI.AIDeviceConfig(name='Test', device_name='FakeDev',
                                      sampling_period_ms=25, read_period_ms=250)
        ch_cfg = pyAI.AIChannelConfig(name='flow', line=0)
        self.hw.open(dev_cfg)
        self.hw.add_channel(ch_cfg)
        self.sensor = SensorStream(self.hw.ai_channels[ch_cfg.name], 'ml/min')

        # create an event "insulin injection" which will trigger
        # every 1 second.
        evt_acq_cfg = pyAI.AIDeviceConfig(name='Test Events', device_name='FakeDevEvents',
                                          sampling_period_ms=1_000, read_period_ms=2_000)
        ch_cfg_evt = pyAI.AIChannelConfig(name='insulin injection', line=1)
        self.evt_acq = pyAI.AIDevice()
        self.evt_acq.open(evt_acq_cfg)
        self.evt_acq.add_channel(ch_cfg_evt)
        self.evt = SensorPoint(self.evt_acq.ai_channels[ch_cfg_evt.name], 'ml')

        # streaming to file is important as plotting gets it data
        # from the file, not a live stream
        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(self.sensor)
        self.sensor.add_strategy(strategy)

        strategy = StreamToFile('Event', 1, 10)
        strategy.open(self.sensor)
        self.evt.add_strategy(strategy)

        # create two plots: one a Sensor plot for streaming data
        # the other a EventPlot
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotevt = EventPlot(self.evt, self.panel.axes)
        self.plotraw = SensorPlot(self.sensor, self.panel.axes)

        # the streaming data will be blue, the events will be a red line
        self.plotevt.set_strategy(self.evt.get_file_strategy('Event'), color='r')
        self.plotraw.set_strategy(self.sensor.get_file_strategy('Raw'), color='b')

        # add the two plots to the main plotting panel
        # the two plots will be superimposed on each other
        self.panel.add_plot(self.plotevt)
        self.panel.add_plot(self.plotraw)

        self.sensor.open()
        self.evt.open()
        self.sensor.hw.device.start()
        self.evt.hw.device.start()
        self.sensor.start()
        self.evt.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
        self.sensor.hw.device.stop()
        self.sensor.close()
        self.sensor.hw.device.close()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp()
    app.MainLoop()
