# -*- coding: utf-8 -*-
""" Demonstrate plotting to multiple plots

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
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
        self._plots = []

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
        SYS_HW.stop()
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

    SYS_HW.load_hardware_from_config()
    SYS_HW.start()
    sensor_haflow = Sensor.Sensor(name='Hepatic Artery Pressure')
    sensor_haflow.read_config()
    sensor_pvflow = Sensor.Sensor(name='Portal Vein Flow')
    sensor_pvflow.read_config()

    sensors = [sensor_haflow, sensor_pvflow]

    app = MyTestApp(0)
    app.MainLoop()
