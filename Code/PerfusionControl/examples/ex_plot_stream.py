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

from pyPerfusion.plotting import SensorPlot, PanelPlotting
import pyHardware.pyAI as pyAI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.FileStrategy import StreamToFile, FileStrategyConfig
from pyPerfusion.ProcessingStrategy import RMSStrategy, ProcessingStrategyConfig
import pyPerfusion.utils as utils


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        cfg = FileStrategyConfig(name='Raw', window_len=1, buf_len=10, version=1)
        strategy = StreamToFile(cfg)
        strategy.open(sensor)
        sensor.add_strategy(strategy)

        cfg = ProcessingStrategyConfig(name='RMS', window_len=10, buf_len=hw.buf_len)
        rms = RMSStrategy(cfg)
        cfg = FileStrategyConfig(name='StreamRMS', window_len=1, buf_len=10, version=1)
        save_rms = StreamToFile(cfg)

        sensor.add_strategy(rms)
        sensor.add_strategy(save_rms)
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotraw = SensorPlot(sensor, self.panel.axes, readout=True)
        self.plotrms = SensorPlot(sensor, self.panel.axes, readout=True)

        self.plotraw.set_strategy(sensor.get_file_strategy('Raw'))
        self.plotrms.set_strategy(sensor.get_file_strategy('StreamRMS'), color='y')

        self.panel.add_plot(self.plotraw)
        self.panel.add_plot(self.plotrms)

        sensor.open()

        sensor.hw.device.start()
        sensor.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        hw.stop()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

    hw = pyAI.AIDevice()
    hw_cfg = pyAI.AIDeviceConfig(name='Example', device_name='FakeDev',
                                 sampling_period_ms=25, read_period_ms=250)
    ch_cfg = pyAI.AIChannelConfig(name='test', line=0)
    hw.open(hw_cfg)
    hw.add_channel(ch_cfg)

    sensor = SensorStream(hw.ai_channels[ch_cfg.name], 'ml/min', valid_range=[15, 20])

    app = MyTestApp(0)
    app.MainLoop()
