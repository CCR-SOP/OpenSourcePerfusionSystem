# -*- coding: utf-8 -*-
"""Test script for testing plotting of Sensor

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging
import threading

from gui.panel_plotting import  PanelPlotting
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        sensor = SYS_PERFUSION.get_sensor('Hepatic Artery Flow')

        self.panel = PanelPlotting(self, seconds_to_display=10)
        self.panel.plot_frame_ms = 10_000
        # self.panel.add_reader(sensor.get_reader('Raw'))
        self.panel.add_reader(sensor.get_reader('MovAvg_11pt'))

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
    utils.setup_default_logging('ex_plot_sensor', logging.DEBUG)
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
