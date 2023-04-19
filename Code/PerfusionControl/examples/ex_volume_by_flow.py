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

        sensor_volume = SYS_PERFUSION.get_sensor('Hepatic Artery Volume')
        sensor_flow = SYS_PERFUSION.get_sensor('Hepatic Artery Flow')
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotvol = SensorPlot(sensor_volume, self.panel.axes, readout=True)
        self.plotflow = SensorPlot(sensor_flow, self.panel.axes, readout=True)

        self.plotflow.set_reader(sensor_flow.get_reader())
        self.plotvol.set_reader(sensor_volume.get_reader(), color='y')

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
        self.panel.Destroy()
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
