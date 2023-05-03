# -*- coding: utf-8 -*-
""" Demonstrate plotting events

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging
import threading

from gui.plotting import SensorPlot, PanelPlotting, EventPlot
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        sensor = SYS_PERFUSION.get_sensor('Hepatic Artery Flow')
        sensor_event = SYS_PERFUSION.get_sensor('Hepatic Artery Pressure')
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

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == '__main__':
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, 'ex_plot_sensor_event')
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
    for thread in threading.enumerate():
        print(thread.name)
