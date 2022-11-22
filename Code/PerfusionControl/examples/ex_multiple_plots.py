# -*- coding: utf-8 -*-
""" Demonstrate plotting to multiple plots

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging

from pyPerfusion.plotting import PanelPlotting, SensorPlot
import pyHardware.pyAI as pyAI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self._plots = []

        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(sensors):
            panel = PanelPlotting(self)
            self._plots.append(panel)
            plot = SensorPlot(sensor, panel.axes, readout=True)
            plot.set_strategy(sensor.get_file_strategy('Raw'))
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            panel.add_plot(plot)
            sensor.start()

        hw.start()

        self.SetSizer(sizer_plots)
        self.Fit()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in sensors:
            sensor.stop()
        hw.close()
        for plot in self._plots:
            plot.Destroy()
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
    dev_cfg = pyAI.AIDeviceConfig(name='HighSpeed',
                                  device_name='FakeDev',
                                  sampling_period_ms=25,
                                  read_period_ms=250)
    ha_cfg = pyAI.AIChannelConfig(name='HA Flow', line=0)
    pv_cfg = pyAI.AIChannelConfig(name='PV Flow', line=2)
    hw.open(dev_cfg)
    hw.add_channel(ha_cfg)
    hw.add_channel(pv_cfg)
    sensors = [
        SensorStream(hw.ai_channels[ha_cfg.name], 'ml/min'),
        SensorStream(hw.ai_channels[pv_cfg.name], 'ml/min')
    ]
    for sensor in sensors:
        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(sensor)
        sensor.add_strategy(strategy)
        sensor.open()

    app = MyTestApp(0)
    app.MainLoop()
