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
from pyPerfusion.PerfusionSystem import PerfusionSystem


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self._lgr = logging.getLogger('ex_volume_by_flow')


        sensors = [SYS_PERFUSION.get_sensor('Hepatic Artery Flow'),
                   SYS_PERFUSION.get_sensor('Hepatic Artery Volume')]


        self._plots = []
        sizer_plots = wx.GridSizer(cols=2)
        for idx, sensor in enumerate(sensors):
            panel = PanelPlotting(self)
            self._plots.append(panel)
            plot = SensorPlot(sensor, panel.axes, readout=True)
            plot.set_reader(sensor.get_reader())
            self._lgr.debug(f'reader fqpn = {sensor.get_reader().fqpn}')
            sizer_plots.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
            panel.add_plot(plot)
            sensor.start()

        self.SetSizer(sizer_plots)

        # example of calibrating the zero flow, normally this would
        # be done using a button on a panel
        print('Calibrating in 2 seconds')
        time.sleep(2.0)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for plot in self._plots:
            plot.Close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()

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
