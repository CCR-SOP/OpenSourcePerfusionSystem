# -*- coding: utf-8 -*-
""" Example to show how to create a calculated streams from 2 other streams

Assumes that the test configuration folder contains a config
"TestAnalogInputDevice.ini" with a 2 channels called "Flow" and a
config called "sensors.ini" with a section called "HA Flow" and a
section called "HA Pressure"

@project: Project NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging
import threading

from gui.plotting import SensorPlot, PanelPlotting
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        sensor_foverp = SYS_PERFUSION.get_sensor('HA Flow Over Pressure')
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plot = SensorPlot(sensor_foverp, self.panel.axes, readout=True)

        self.plot.set_reader(sensor_foverp.get_reader())

        self.panel.add_plot(self.plot)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('ex_flow_over_pressure', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system
        # close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()

    SYS_PERFUSION.close()
    for thread in threading.enumerate():
        print(thread.name)
