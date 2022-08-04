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
from pyHardware.PHDserial import PHDserial
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils
from pyPerfusion.panel_AI import PanelAI, DEV_LIST

utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        self._logger = logging.getLogger(__name__)

        #Set device + channels and open
        dev = 'Dev2' #how do we set line 0?
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        # check these values - documentation just said sensitivity is 10 mV and I wasn't sure how to get this info
        # Want voltage calibration b/w 20-50C. Axes can be in this range. green should be 35-38C as our target temp
        self.sensor = SensorStream('BAT-12 Temperature', 'deg C', self.acq, valid_range=[35, 38])

        self.acq.open(dev)
        self.acq.add_channel(0)
        self.acq.start()

        self.sensor.hw.add_channel(0)
        self.sensor.set_ch_id(0)
        #sensor.hw.set_demo_properties(0, demo_amp=20, demo_offset=10)

        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)

        rms = RMSStrategy('RMS', 10, self.acq.buf_len)
        save_rms = StreamToFile('StreamRMS', None, self.acq.buf_len)
        save_rms.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_rms', {**self.sensor.params, **rms.params})
        self.sensor.add_strategy(rms)
        self.sensor.add_strategy(save_rms)

        section = LP_CFG.get_hwcfg_section(self._pumpname)
        self.dev = section['Device']
        self.line = section['LineName']
        self.desired = float(section['desired'])
        self.tolerance = float(section['tolerance'])
        self.increment = float(section['increment'])
        try:
            self.divisor = float(section['divisor'])
        except KeyError:
            self.divisor = None

        calpt1_target = float(section['CalPt1_Target'])
        calpt1_reading = section['CalPt1_Reading']
        calpt2_target = float(section['CalPt2_Target'])
        calpt2_reading = section['CalPt2_Reading']



        self.panel = PanelAI(self, self.sensor, self.sensor.name, strategy='Converted')
        section = LP_CFG.get_hwcfg_section(self.sensor.name)
        #sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, border=1)
        self.panel.force_device(dev)

        #This code is not in Panel_AI and is only in plotting
        #self.panel.plot_frame_ms = 10_000
        #self.plotraw = SensorPlot(self.sensor, self.panel.axes, readout=True)
        #self.plotrms = SensorPlot(self.sensor, self.panel.axes, readout=True)

        #self.plotraw.set_strategy(self.sensor.get_file_strategy('Raw'), color='b')
        #self.plotrms.set_strategy(self.sensor.get_file_strategy('StreamRMS'), color='k')

        #self.panel.add_plot(self.plotraw)
        #self.panel.add_plot(self.plotrms)
        #self.sensor.open()

        #self.sensor.hw.open()
        #self.sensor.hw.start()
        #self.sensor.start()

        #self.SetSizer(sizer)
        self.Fit()
        self.Layout()
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
#time.sleep(100)
#sensor.stop()
#acq.stop()