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
    def __init__(self, perfusion_system, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.sys = perfusion_system
        self._panels = []

        sensors = [self.sys.get_sensor('Hepatic Artery Pressure'),
                   self.sys.get_sensor('Portal Vein Flow')]

        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(sensors):
            panel = PanelPlotting(self)
            self._panels.append(panel)
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
        for panel in self._panels:
            panel.Close()
        for child in self.GetChildren():
            child.Close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(sys, None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('ex_multiple_plots', logging.DEBUG)
    utils.only_show_logs_from(['pyHardware.pyGeneric.MCC_Brd0'])
    sys = PerfusionSystem()
    sys.open()
    sys.load_all()

    app = MyTestApp(0)
    app.MainLoop()
    print('MyTestApp closed')
    sys.close()
    for thread in threading.enumerate():
        print(thread.name)

