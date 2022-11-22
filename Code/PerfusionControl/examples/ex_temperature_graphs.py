"""
@author: Stephie Lux
Panel to introduce temperature graph

Immediate needs: figure out input information for temperature sensor, decide on processing strategy for temperature
"""

import wx
import logging

from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
import pyHardware.pyAI as pyAI
from pyPerfusion.SensorStream import SensorStream
from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.ProcessingStrategy import RMSStrategy
import pyPerfusion.utils as utils
from pyPerfusion.panel_AI import PanelAI
import pyPerfusion.PerfusionConfig as PerfusionConfig


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        self._logger = logging.getLogger(__name__)

        # Calibration functionality
        panel = PanelAI(self, sensor=sensor, strategy='StreamRaw')
        sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        sensor.hw.device.start()
        sensor.start()
        sensor.open()

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        sensor.stop()
        sensor.close()
        sensor.hw.device.stop()
        sensor.hw.device.close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    PerfusionConfig.set_test_config()

    hw = NIDAQAIDevice()
    hw.cfg = AINIDAQDeviceConfig(name='Dev2')
    hw.read_config()

    sensor = SensorStream(hw.ai_channels['BAT-12 Temperature'], 'deg C')

    # Raw streaming and RMS strategy
    raw = StreamToFile('StreamRaw', None, hw.buf_len)
    raw.open(sensor)
    sensor.add_strategy(raw)
    rms = RMSStrategy('RMS', 50, hw.buf_len)
    save_rms = StreamToFile('StreamRMS', None, hw.buf_len)
    save_rms.open(sensor)
    sensor.add_strategy(rms)
    sensor.add_strategy(save_rms)

    app = MyTestApp(0)
    app.MainLoop()
