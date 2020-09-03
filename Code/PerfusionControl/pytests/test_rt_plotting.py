# -*- coding: utf-8 -*-
"""

@author: John Kakareka

test real-time plotting
"""
import wx

from pyPerfusion.panel_plotting import PanelPlotting
from pytests.MockSensorModule import MockSensorModule


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPlotting(self, MockSensorModule("mod1"))


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


app = MyTestApp(0)
app.MainLoop()

