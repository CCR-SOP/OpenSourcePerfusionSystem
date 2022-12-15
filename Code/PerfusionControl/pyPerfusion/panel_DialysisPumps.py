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
    def __init__(self, parent, **kwds):  # add pump as an argument - just skeletonized right now
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent
        # self.pump = pump

        static_box = wx.StaticBox(self, wx.ID_ANY, label='Dialysis Pumps')
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_inflow = wx.StaticText(self, label='Dialysate inflow pump flow rate (mL/min):')
        self.input_inflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.label_outflow = wx.StaticText(self, label='Dialysate outflow pump flow rate (mL/min):')
        self.input_outflow_rate = wx.TextCtrl(self, wx.ID_ANY, value='5')

        self.start_btn_inflow = wx.ToggleButton(self, label='Start')
        self.start_btn_outflow = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=3)

        sizer_cfg.Add(self.label_inflow, flags)
        sizer_cfg.Add(self.input_inflow_rate, flags)
        sizer_cfg.Add(self.start_btn_inflow, flags)

        sizer_cfg.Add(self.label_outflow, flags)
        sizer_cfg.Add(self.input_outflow_rate, flags)
        sizer_cfg.Add(self.start_btn_outflow, flags)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.start_btn_inflow.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartInflow)
        self.start_btn_outflow.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartOutflow)
        # do we need something to accept the text input?

    def OnStartInflow(self, evt):
        # write something to open
        self.start_btn_inflow.SetLabel('Stop')

    def OnStartOutflow(self, evt):
        # write something to open
        self.start_btn_outflow.SetLabel('Stop')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        # self.pump = DialysatePumps('Mock Pump')

        self.panel = DialysisPumpPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        # self.pump.close()  # need method for this
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