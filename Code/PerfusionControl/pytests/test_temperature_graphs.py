"""
@author: Stephie Lux
Panel to introduce temperature graph

Immediate needs: figure out input information for temperature sensor, decide on processing strategy for temperature
"""

import wx
import time
import logging

from pyPerfusion.plotting import SensorPlot, PanelPlotting
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

#acq = AI(100)
acq = NIDAQ_AI(period_ms=100, volts_p2p=0.3, volts_offset=0.15) #check these values - documentation just said sensitivity is 10 mV
#going from range of 20C to 50C
sensor = SensorStream('BAT-12 Temperature', 'deg C', acq, valid_range=[35, 38])

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        sensor.hw.add_channel(2)
        sensor.set_ch_id(2)
        sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        strategy = StreamToFile('Raw', 1, 10)
        strategy.open(LP_CFG.LP_PATH['stream'], 'test', sensor.params)
        sensor.add_strategy(strategy)

        rms = RMSStrategy('RMS', 10, acq.buf_len)
        save_rms = StreamToFile('StreamRMS', None, acq.buf_len)
        save_rms.open(LP_CFG.LP_PATH['stream'], f'{sensor.name}_rms', {**sensor.params, **rms.params})
        sensor.add_strategy(rms)
        sensor.add_strategy(save_rms)
        self.panel = PanelPlotting(self)
        self.panel.plot_frame_ms = 10_000
        self.plotraw = SensorPlot(sensor, self.panel.axes, readout=True)
        self.plotrms = SensorPlot(sensor, self.panel.axes, readout=True)

        self.plotraw.set_strategy(sensor.get_file_strategy('Raw'), color='b')
        self.plotrms.set_strategy(sensor.get_file_strategy('StreamRMS'), color='k')

        self.panel.add_plot(self.plotraw)
        self.panel.add_plot(self.plotrms)

        sensor.open()

        sensor.hw.open()
        sensor.hw.start()
        sensor.start()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
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
sensor.stop()
acq.stop()