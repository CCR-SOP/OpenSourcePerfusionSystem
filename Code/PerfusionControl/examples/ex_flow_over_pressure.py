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

from gui.plotting import SensorPlot, PanelPlotting
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
import pyPerfusion.Sensor as Sensor


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._lgr = logging.getLogger(__name__)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plot = SensorPlot(sensor_foverp, self.panel.axes, readout=True)

        self.plot.set_reader(sensor_foverp.get_reader())

        self.panel.add_plot(self.plot)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor_foverp.stop()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_all()
    # SYS_HW.load_mocks()
    SYS_HW.start()

    sensor_foverp = Sensor.DivisionSensor(name='HA Flow Over Pressure')
    sensor_foverp.read_config()

    sensor_flow = Sensor.Sensor(name=sensor_foverp.cfg.dividend_name)
    sensor_flow.read_config()
    sensor_pressure = Sensor.Sensor(name=sensor_foverp.cfg.divisor_name)
    sensor_pressure.read_config()

    sensor_foverp.reader_dividend = sensor_flow.get_reader(name=sensor_foverp.cfg.dividend_strategy)
    sensor_foverp.reader_divisor = sensor_pressure.get_reader(name=sensor_foverp.cfg.divisor_strategy)
    sensor_foverp.hw = sensor_flow.hw

    sensor_flow.start()
    sensor_pressure.start()
    sensor_foverp.start()

    app = MyTestApp(0)
    app.MainLoop()
