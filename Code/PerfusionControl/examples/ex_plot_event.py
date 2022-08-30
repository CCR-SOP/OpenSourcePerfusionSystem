# -*- coding: utf-8 -*-
""" Demonstrate plotting events

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import logging

from pyPerfusion.plotting import SensorPlot, EventPlot, PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.SensorPoint import SensorPoint
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile
import pyPerfusion.utils as utils

# for testing, creating a streaming AI representing "flow"
acq = AI(100)
sensor = SensorStream('flow', 'ml/min', acq)

# create an event "insulin injection" which will trigger
# every 1 second.
evt_acq = AI(1000, read_period_ms=1000)
evt = SensorPoint('Insulin Injection', 'ml', evt_acq)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # create two plots: one a Sensor plot for streaming data
        # the other a EventPlot
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotevt = EventPlot(evt, self.panel.axes)
        self.plotraw = SensorPlot(sensor, self.panel.axes)

        # add the two plots to the main plotting panel
        # the two plots will be superimposed on each other
        self.panel.add_plot(self.plotevt)
        self.panel.add_plot(self.plotraw)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        self.panel.Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        self.configure_hw()
        frame = TestFrame(None, wx.ID_ANY, "")

        # this is where we associate the plots with the actual data
        # where this is done depends on the app design. This could also be
        # done in the frame class if the hw is passed through the constructor
        # or in function
        # the streaming data will be blue, the events will be a red line
        frame.plotevt.set_strategy(evt.get_file_strategy('Event'), color='r')
        frame.plotraw.set_strategy(sensor.get_file_strategy('Raw'), color='b')

        self.SetTopWindow(frame)
        frame.Show()

        return True

    def configure_hw(self):
        # for testing purposes, add the hardware here
        # in a more sophisticated app, this may done elsehwere
        sensor.hw.add_channel(0)
        sensor.set_ch_id(0)
        sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        evt.hw.add_channel(0)
        evt.set_ch_id(0)
        evt.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        # streaming to file is important as plotting gets it data
        # from the file, not a live stream
        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test', sensor.params)
        sensor.add_strategy(strategy)

        strategy = PointsToFile('Event', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test_event', evt.params)
        evt.add_strategy(strategy)

        sensor.open()
        evt.open()

        sensor.hw.open()
        evt.hw.open()
        sensor.hw.start()
        evt.hw.start()
        sensor.start()
        evt.start()


if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()
