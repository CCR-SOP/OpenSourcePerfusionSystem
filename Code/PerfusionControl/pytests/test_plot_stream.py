# -*- coding: utf-8 -*-
"""Test script for testing plotting of SensorStream

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import wx
import time
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI_Config

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

#acq = AI(100)
#sensor = SensorStream('test', 'ml/min', acq, valid_range=[15, 20])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('BAT-12 Temperature', 'deg C', self.acq, valid_range=[35, 38])

        self.sensor.hw.add_channel(0)
        self.sensor.set_ch_id(0)
        self.sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test', self.sensor.params)
        self.sensor.add_strategy(strategy)

        rms = RMSStrategy('RMS', 10, self.acq.buf_len)
        save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
        save_rms.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_rms', {**self.sensor.params, **rms.params})
        self.sensor.add_strategy(rms)
        self.sensor.add_strategy(save_rms)
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotraw = SensorPlot(self.sensor, self.panel.axes, readout=True)
        self.plotrms = SensorPlot(self.sensor, self.panel.axes, readout=True)

        self.plotraw.set_strategy(self.sensor.get_file_strategy('Raw'))
        self.plotrms.set_strategy(self.sensor.get_file_strategy('StreamRMS'), color='y')

        self.panel.add_plot(self.plotraw)
        self.panel.add_plot(self.plotrms)

        self.sensor.open()

        self.sensor.hw.open()
        self.sensor.hw.start()
        self.sensor.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
        self.panel.Destroy()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

app = MyTestApp(0)
app.MainLoop()
time.sleep(100)
#sensor.stop()
#acq.stop()

