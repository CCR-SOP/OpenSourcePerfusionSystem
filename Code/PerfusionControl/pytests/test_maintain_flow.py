# -*- coding: utf-8 -*-
"""

@author: John Kakareka

Test app for testing how to maintain flow
"""
from pathlib import Path

from configparser import ConfigParser
import wx

from pyHardware.pyAO_NIDAQ import NIDAQ_AO
from pyHardware.pyAI_NIDAQ import NIDAQ_AI
import pyPerfusion.PerfusionConfig as LP_CFG


class PanelTestMaintainFlow(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)

        self._ai = NIDAQ_AI(line=1, period_ms=100, volts_p2p=5, volts_offset=2.5, dev='Dev1')
        self._ao = NIDAQ_AO()
        self._ao.open(line=1, period_ms=100, dev='Dev1')

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_ai = wx.StaticText(self, label =  f'Using Analog Input {self._ai.devname}')
        self.label_ao = wx.StaticText(self, label=f'Using Analog Output {self._ao.devname}')

        self.label_desired_output = wx.StaticText(self, label='Desired Output')
        self.spin_desired_output = wx.SpinCtrlDouble(self, min=0.0, max=5.0, initial=2.5, inc=0.1)
        self.spin_desired_output.Digits = 3

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        self.sizer.Add(self.label_ai)
        self.sizer.Add(self.label_ao)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_desired_output, flags)
        sizer.Add(self.spin_desired_output, flags)

        self.sizer.Add(sizer)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.ao = NIDAQ_AO()
        ao_name = 'Analog Output'
        self.panel = PanelTestMaintainFlow(self)


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyTestApp(0)
    app.MainLoop()
