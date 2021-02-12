# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of plots created with real data
"""
import wx
import time
from pathlib import Path

from pyPerfusion.panel_AI import PanelAI, DEV_LIST
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)
        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensors = [
            SensorStream('Analog Input 1', 'Volts', self.acq),
            SensorStream('Analog Input 2', 'Volts', self.acq),
            SensorStream('Analog Input 3', 'Volts', self.acq)
        ]
        dlg = wx.SingleChoiceDialog(self, 'Choose NI Device', 'Device', DEV_LIST)
        if dlg.ShowModal() == wx.ID_OK:
            dev = dlg.GetStringSelection()
            print(dev)

        for sensor in self.sensors:
            panel = PanelAI(self, sensor, name=sensor.name)
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for sensor in self.sensors:
            sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
