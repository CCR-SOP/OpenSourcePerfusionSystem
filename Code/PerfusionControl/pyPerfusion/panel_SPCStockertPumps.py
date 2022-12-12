# -*- coding: utf-8 -*-
""" Application to display SPC Stockert centrifugal pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class StockertPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):  # need to add in pump code
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Mock Stockert Pump")
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_pump_speed = wx.StaticText(self, label='Input pump speed (rpm):')
        self.input_pump_speed = wx.TextCtrl(self, wx.ID_ANY, value='100')

        self.start_btn = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=3)

        sizer_cfg.Add(self.label_pump_speed, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.input_pump_speed, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.start_btn, flags)
        sizer_cfg.AddSpacer(2)

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

class SinusoidalPumpPanel(wx.Panel):
    def __init__(self, parent, **kwds):  # need to add in pump code
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
        utils.configure_matplotlib_logging()
        self.parent = parent

        static_box = wx.StaticBox(self, wx.ID_ANY, label="Sinusoidal Pump")
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.label_trough_speed = wx.StaticText(self, label='Minimum speed (rpm):')
        self.input_trough_speed = wx.TextCtrl(self, wx.ID_ANY, value='100')

        self.label_peak_speed = wx.StaticText(self, label='Maximum speed (rpm):')
        self.input_peak_speed = wx.TextCtrl(self, wx.ID_ANY, value='200')

        self.start_btn = wx.ToggleButton(self, label='Start')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=4)

        sizer_cfg.Add(self.label_trough_speed, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.input_trough_speed, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.label_peak_speed, flags)
        sizer_cfg.AddSpacer(2)
        sizer_cfg.Add(self.input_peak_speed, flags)
        sizer_cfg.AddSpacer(2)

        sizer_cfg.Add(self.start_btn, flags)
        sizer_cfg.AddSpacer(2)

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
        # define pumps

        self.panel = StockertPumpPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        # write something to close
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