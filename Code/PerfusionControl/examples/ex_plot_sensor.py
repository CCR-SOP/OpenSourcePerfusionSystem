# -*- coding: utf-8 -*-
"""Test script for testing plotting of Sensor

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import time
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting
import pyPerfusion.Sensor as Sensor
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotraw = SensorPlot(sensor, self.panel.axes, readout=True)
        self.plotrms = SensorPlot(sensor, self.panel.axes, readout=True)

        self.plotraw.set_reader(sensor.get_reader('Raw'))
        self.plotrms.set_reader(sensor.get_reader('RMS_11pt'), color='y')

        self.panel.add_plot(self.plotraw)
        self.panel.add_plot(self.plotrms)

        sensor.open()
        sensor.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        SYS_HW.stop()
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

    SYS_HW.load_all()
    SYS_HW.start()
    sensor = Sensor.Sensor(name='Hepatic Artery Flow')
    sensor.read_config()

    app = MyTestApp(0)
    app.MainLoop()
