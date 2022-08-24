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

        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=1, volts_offset=0.5)
        self.sensor = SensorStream('BAT-12 Temperature', 'deg C', self.acq, valid_range=[35, 38])
        # check these values - documentation just said sensitivity is 10 mV and I wasn't sure how to get this info
        # Want voltage calibration b/w 0-50C. Axes can be in this range. green should be 35-38C as our target temp

        # Open device and channel
        section = LP_CFG.get_hwcfg_section(self.sensor.name)
        dev = DEV_LIST[1]
        line = LINE_LIST[0]

        self.acq.open(dev)
        self.sensor.hw.add_channel('0')
        self.sensor.set_ch_id('0')
        # Somehow Allen doesn't have these? --> must be because his buttons allow for opening. Ask John. Window is closing now

        # Raw streaming (RMS strategy removed)
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)


        #Calibration functionality
        panel = PanelAI(self, self.sensor, name=self.sensor.name, strategy='StreamRaw')
        calpt1_target = float(section['CalPt1_Target'])
        calpt1_reading = section['CalPt1_Reading']
        calpt2_target = float(section['CalPt2_Target'])
        calpt2_reading = section['CalPt2_Reading']
        panel._panel_cfg.choice_dev.SetStringSelection(dev)
        panel._panel_cfg.choice_line.SetSelection(int(line))
        panel._panel_cfg.choice_dev.Enable(False)
        panel._panel_cfg.choice_line.Enable(False)
        panel._panel_cfg.panel_cal.spin_cal_pt1.SetValue(calpt1_target)
        panel._panel_cfg.panel_cal.label_cal_pt1_val.SetLabel(calpt1_reading)
        panel._panel_cfg.panel_cal.spin_cal_pt2.SetValue(calpt2_target)
        panel._panel_cfg.panel_cal.label_cal_pt2_val.SetLabel(calpt2_reading)
        sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        panel.force_device(dev)

        self.sensor.hw.start()
        self.sensor.open()

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.sensor.stop()
        self.sensor.close()
        if self.sensor.hw._task:
            self.sensor.hw.stop()
            self.sensor.hw.close()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        #print('\a') this works as an alarm but very simple and obviously we need some kind of loop
        return True

app = MyTestApp(0)
app.MainLoop()

