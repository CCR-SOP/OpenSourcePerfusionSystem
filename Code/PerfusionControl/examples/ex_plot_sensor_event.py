# -*- coding: utf-8 -*-
""" Demonstrate plotting events

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting, EventPlot
import pyPerfusion.Sensor as Sensor
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # create two plots: one a Sensor plot for streaming data
        # the other a EventPlot
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotevt = EventPlot(sensor_event, self.panel.axes)
        self.plotraw = SensorPlot(sensor, self.panel.axes)

        # the streaming data will be blue, the events will be a red line
        self.plotevt.set_reader(sensor_event.get_reader('RawPoints'), color='r')
        self.plotraw.set_reader(sensor.get_reader('Raw'), color='b')

        # add the two plots to the main plotting panel
        # the two plots will be superimposed on each other
        self.panel.add_plot(self.plotevt)
        self.panel.add_plot(self.plotraw)

        sensor.open()
        sensor_event.open()
        sensor.start()
        sensor_event.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        sensor_event.stop()
        SYS_HW.stop()
        self.panel.Destroy()
        self.Destroy()



class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()
    SYS_HW.load_mocks()
    SYS_HW.start()

    sensor = Sensor.Sensor(name='Hepatic Artery Flow')
    sensor.read_config()

    sensor_event = Sensor.Sensor(name='Mock Second Event')
    sensor_event.read_config()

    app = MyTestApp(0)
    app.MainLoop()
