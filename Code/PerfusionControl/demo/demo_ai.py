# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots created with real data
"""
import logging

import wx

from pyPerfusion.panel_AI import PanelAI, DEV_LIST
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.FileStrategy import StreamToFile


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()

        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensors = [
            SensorStream('HA Flow', 'Volts', self.acq),
            SensorStream('PV Flow', 'Volts', self.acq),
            SensorStream('IVC Flow', 'Volts', self.acq),
            SensorStream('HA Pressure', 'Volts', self.acq),
            SensorStream('PV Pressure', 'Volts', self.acq),
            SensorStream('IVC Pressure', 'Volts', self.acq)
        ]
        for sensor in self.sensors:
            raw = StreamToFile('Raw', None, self.acq.buf_len)
            raw.open(PerfusionConfig.get_date_folder(), f'{sensor.name}_raw', sensor.params)
            sensor.add_strategy(raw)

        dlg = wx.SingleChoiceDialog(self, 'Choose NI Device', 'Device', DEV_LIST)
        if dlg.ShowModal() == wx.ID_OK:
            dev = dlg.GetStringSelection()
        dlg.Destroy()

        self.panel = {}
        for sensor in self.sensors:
            self.panel[sensor.name] = PanelAI(self, sensor, sensor.name, 'Raw')
            sizer.Add(self.panel[sensor.name], 1, wx.ALL | wx.EXPAND, border=1)
            self.panel[sensor.name].force_device(dev)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        for panel in self.panel.keys():
            self.panel[panel].Destroy()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    app = MyTestApp(0)
    app.MainLoop()
