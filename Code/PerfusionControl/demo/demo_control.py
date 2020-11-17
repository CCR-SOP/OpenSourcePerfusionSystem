# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Demonstration of basic Analog Output controls
"""
import wx
import time
from pathlib import Path

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyPerfusion.panel_AO import PanelAO

devices = ['Centrifugal Pump 1', 'Centrifugal Pump 2', 'Peristaltic Pump 1']


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=2)

        for device in devices:
            panel = PanelAO(self, NIDAQ_AO(), device)
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()
