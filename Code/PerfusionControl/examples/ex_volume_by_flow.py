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
        self.plotvol = SensorPlot(sensor_volume, self.panel.axes, readout=True)
        self.plotflow = SensorPlot(sensor_flow, self.panel.axes, readout=True)

        self.plotflow.set_strategy(sensor_flow.get_reader('RMS_11pt'))
        self.plotvol.set_strategy(sensor_volume.get_reader('VolumeByFlow'), color='y')

        self.panel.add_plot(self.plotflow)
        self.panel.add_plot(self.plotvol)

        sensor_flow.open()
        sensor_flow.start()
        sensor_volume.open()
        sensor_volume.start()

        # example of calibrating the zero flow, normally this would
        # be done using a button on a panel
        print('Calibrating in 2 seconds')
        time.sleep(2.0)
        sensor_volume.get_writer('VolumeByFlow').reset()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor_volume.stop()
        sensor_flow.stop()
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

    SYS_HW.load_hardware_from_config()
    SYS_HW.start()
    sensor_flow = Sensor.Sensor(name='Hepatic Artery Flow')
    sensor_flow.read_config()

    sensor_volume = Sensor.CalculatedSensor(name='Hepatic Artery Volume')
    sensor_volume.read_config()
    sensor_volume.reader = sensor_flow.get_reader(sensor_volume.cfg.sensor_strategy)

    app = MyTestApp(0)
    app.MainLoop()

