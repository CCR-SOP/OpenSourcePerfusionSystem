# -*- coding: utf-8 -*-
"""Test script for testing plotting of LeviFlow sensor

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
import pyHardware.pyLeviFlow as pyLeviFlow


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotraw = SensorPlot(sensor, self.panel.axes, readout=True)

        self.plotraw.set_reader(sensor.get_reader())

        self.panel.add_plot(self.plotraw)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        leviflow.stop()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.configure_matplotlib_logging()

    leviflow = pyLeviFlow.LeviFlow(name='LeviFlow1')
    try:
        leviflow.read_config()
    except pyLeviFlow.LeviFlowException:
        lgr.warning(f'LeviFlow1 not found. Loading mock')
        SYS_HW.mocks_enabled = True
        leviflow.hw = pyLeviFlow.MockLeviFlow()
        SYS_HW.leviflow1 = leviflow

    leviflow.start()
    sensor = Sensor.Sensor(name='Test LeviFlow')
    sensor.read_config()
    sensor.start()

    app = MyTestApp(0)
    app.MainLoop()
