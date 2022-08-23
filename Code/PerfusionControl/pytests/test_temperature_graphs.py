"""
@author: Stephie Lux
Panel to introduce temperature graph

Immediate needs: figure out input information for temperature sensor, decide on processing strategy for temperature
"""

import wx
import time
import logging

# from pyPerfusion.plotting import SensorPlot, PanelPlotting
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
# from pyHardware.pyAI import AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils
from pyPerfusion.panel_AI import PanelAI, DEV_LIST, LINE_LIST

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        self._logger = logging.getLogger(__name__)

        # Set device + channel and print
        dev = DEV_LIST[1]
        self._logger.info(f'{dev}')
        line = LINE_LIST[0]
        self._logger.info(f'{line}')
        # Not in Allen code

        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('BAT-12 Temperature', 'deg C', self.acq, valid_range=[35, 38])
        # check these values - documentation just said sensitivity is 10 mV and I wasn't sure how to get this info
        # Want voltage calibration b/w 0-50C. Axes can be in this range. green should be 35-38C as our target temp

        # Open device and channel
        self.acq.open(dev)
        self.sensor.hw.add_channel('0')
        self.sensor.set_ch_id('0')
        # Somehow Allen doesn't have these?

        # Raw streaming + RMS strategy
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)
        rms = RMSStrategy('RMS', 50, self.acq.buf_len)
        save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
        save_rms.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_rms', {**self.sensor.params, **rms.params})
        self.sensor.add_strategy(rms)
        self.sensor.add_strategy(save_rms)

        self.panel = PanelAI(self, self.sensor, self.sensor.name, strategy='StreamRaw')
        section = LP_CFG.get_hwcfg_section(self.sensor.name)
        sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, border=1)
        self.panel.force_device(dev)

        self.sensor.hw.start()
        self.sensor.open()

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
        self.panel.Destroy()
        self.Destroy()
        self.acq.stop()
        time.sleep(100)

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

app = MyTestApp(0)
app.MainLoop()

