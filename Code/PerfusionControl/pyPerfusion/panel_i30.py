# -*- coding: utf-8 -*-
""" Panel class for controlling a Puraleve i30 centrifugal pump

@project: LiverPerfusion NIH
@author: John Kakareka NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyHardware.pyPuraLevi30 import PuraLevi30


class Paneli30(wx.Panel):
    def __init__(self, parent, name, hw):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.name = name

        self.panel_i30 = Paneli30Control(self, self.name, hw)

        font = wx.Font()
        font.SetPointSize(int(16))

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name + " Pump")
        static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):

        self.sizer.Add(self.panel_i30, wx.SizerFlags(1).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        self.panel_i30.Close()


class Paneli30Control(wx.Panel):
    def __init__(self, parent, name, hw):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.name = name
        self.hw = hw

        font = wx.Font()
        font.SetPointSize(int(12))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_speed = wx.StaticText(self, label='Set Speed (mL/min):')
        self.spin_speed = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5, initial=0)
        self.label_actual = wx.StaticText(self, label='Actual Speed (mL/min):')
        self.txt_actual = wx.TextCtrl(self, style=wx.TE_READONLY)

        self.btn_change_rate = wx.Button(self, label='Update Rate')
        self.btn_stop = wx.Button(self, label='Stop')

        self.label_speed.SetFont(font)
        self.spin_speed.SetFont(font)
        self.label_actual.SetFont(font)
        self.txt_actual.SetFont(font)
        self.btn_stop.SetFont(font)
        self.btn_change_rate.SetFont(font)

        self.timer_update = wx.Timer(self)
        self.timer_update.Start(1_000, wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center()
        sizer_cfg = wx.GridSizer(rows=3, cols=2, vgap=1, hgap=1)

        sizer_cfg.Add(self.label_speed, flags)
        sizer_cfg.Add(self.label_actual, flags)
        sizer_cfg.Add(self.spin_speed, flags)
        sizer_cfg.Add(self.txt_actual, flags)
        sizer_cfg.Add(self.btn_change_rate, flags)
        sizer_cfg.Add(self.btn_stop, flags)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.timer_update.Bind(wx.EVT_TIMER, self.update_controls_from_hardware)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_stop(self, evt):
        self.hw.set_output(int(0))

    def update_controls_from_hardware(self):
        value = self.hw.get_current_output()
        self.txt_actual.SetValue(f'{value}')

    def on_close(self, evt):
        self.timer_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.pump = PuraLevi30(pump_name)
        self.pump.read_config()
        self.panel = Paneli30(self, self.pump)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
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

    SYS_HW.load_hardware_from_config()

    pump_name = 'Test i30'

    app = MyTestApp(0)
    app.MainLoop()
