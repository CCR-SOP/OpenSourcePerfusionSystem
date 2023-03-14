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
import time
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting
import pyPerfusion.Sensor as Sensor
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.CalculatedSensor import FlowOverPressure


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plot = SensorPlot(flow_over_pressure, self.panel.axes, readout=True)

        self.plot.set_strategy(flow_over_pressure.get_file_strategy('Stream2File'))

        self.panel.add_plot(self.plot)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor_flow.stop()
        sensor_pressure.stop()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    logger = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    SYS_HW.load_mocks()
    SYS_HW.start()
    sensor_flow = Sensor.Sensor(name='Hepatic Artery Flow')
    sensor_flow.read_config()
    sensor_pressure = Sensor.Sensor(name='Hepatic Artery Pressure')
    sensor_pressure.read_config()

    f_over_p = FlowOverPressure(name='Flow Over Pressure',
                                flow=sensor_flow.get_reader(),
                                pressure=sensor_pressure.get_reader())
    flow_over_pressure = SensorStream(f_over_p, '')
    flow_over_pressure.add_strategy(Strategies.get_strategy('Stream2File'))
    flow_over_pressure.open()
    flow_over_pressure.start()

    app = MyTestApp(0)
    app.MainLoop()
