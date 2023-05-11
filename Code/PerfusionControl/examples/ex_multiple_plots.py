# -*- coding: utf-8 -*-
""" Demonstrate plotting to multiple plots

@project: LiverPerfusion NIH
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
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self._plots = []

        sensors = [SYS_PERFUSION.get_sensor('Hepatic Artery Pressure'),
                   SYS_PERFUSION.get_sensor('Portal Vein Flow')]

        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(sensors):
            panel = PanelPlotting(self)
            self._plots.append(panel)
            plot = SensorPlot(sensor, panel.axes, readout=True)
            plot.set_reader(sensor.get_reader())
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            panel.add_plot(plot)
            sensor.start()

        self.SetSizer(sizer_plots)
        self.Fit()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for plot in self._plots:
            plot.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()

        return True


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('ex_multiple_plots', logging.DEBUG)
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

