# -*- coding: utf-8 -*-
""" Application to display all sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

from pyPerfusion.panel_AI import PanelAI
import pyHardware.pyAI_NIDAQ as NIDAQAI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint


class SensorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        self.acq = NIDAQAI.NIDAQAIDevice()
        self.acq.cfg = NIDAQAI.AINIDAQDeviceConfig(name='Dev1')
        self.acq.read_config()

        self.sensors = []
        for ch in self.acq.ai_channels.values():
            sensor = SensorStream(ch, '')
            raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
            sensor.add_strategy(raw)
            self.sensors.append(sensor)
            sensor.start()

        self.acq.start()

        self.panel = {}
        for sensor in self.sensors:
            self.panel[sensor.name] = PanelAI(self, sensor, strategy='StreamRaw')
            sizer.Add(self.panel[sensor.name], 1, wx.ALL | wx.EXPAND, border=1)

        self.acq.start()

        self.cdi = pyCDI.CDIStreaming('CDI')
        self.cdi.read_config()
        self.cdi_sensor = SensorPoint(self.cdi, 'na')
        self.cdi_sensor.add_strategy(strategy=MultiVarToFile('write', 1, 17))
        self.cdi_sensor.start()
        self.cdi.start()

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()
        self.cdi.stop()
        self.cdi_sensor.stop()
        self.Destroy()


class MySensorApp(wx.App):
    def OnInit(self):
        frame = SensorFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    app = MySensorApp(0)
    app.MainLoop()
