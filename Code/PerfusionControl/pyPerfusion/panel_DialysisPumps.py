# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.pyDialysatePumps import DialysatePumps
from pyHardware.pyAO_NIDAQ import NIDAQ_AO


class DialysisPumpPanel(wx.Panel):
    def __init__(self, parent, pump: DialysatePumps, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent
        self.pump = pump

        self.sizer = wx.StaticBoxSizer(wx.VERTICAL)

        self.label_inflow = wx.StaticText(self, label='Dialysate Inflow Pump Flow Rate')
        self.input_inflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.label_outflow = wx.StaticText(self, label='Dialysate Outflow Pump Flow Rate')
        self.input_outflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.start_btn = wx.ToggleButton(self, label='Start')
        self.unit_label = wx.StaticText(self, label='mL/min')  # connect this to the hardware instead

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=4)

        sizer_cfg.Add(self.label_inflow, flags)
        sizer_cfg.Add(self.input_inflow_rate, flags)
        sizer_cfg.Add(self.start_btn, flags)
        sizer_cfg.Add(self.unit_label, flags)

        sizer_cfg.Add(self.label_outflow, flags)
        sizer_cfg.Add(self.input_outflow_rate, flags)
        sizer_cfg.Add(self.start_btn, flags)
        sizer_cfg.Add(self.unit_label, flags)

        sizer_cfg.AddSpacer(2)

        sizer_cfg.Add(self.start_btn, flags)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)
        # do we need something to accept the text input?

    def OnStart(self, evt):
        # write something to open
        self.start_btn.SetLabel('Stop')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        # see if there are any available com ports, if not
        # use a mock for testing.
        self.pump = DialysatePumps('Mock Pump')

        self.panel = DialysisPumpPanel(self, self.pump)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.pump.close()  # need method for this
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()