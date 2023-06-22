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
from pyHardware.pyPuraLevi30 import PuraLevi30, Mocki30, i30Exception


class Paneli30(wx.Panel):
    def __init__(self, parent, hw):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.name = hw.name

        self.panel_i30 = Paneli30Control(self, self.name, hw)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        static_box.SetFont(utils.get_header_font())
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
        self.label_speed = wx.StaticText(self, label='Set Speed (rpm):')
        self.spin_speed = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5, initial=0)
        self.label_actual = wx.StaticText(self, label='Actual Speed (rpm):')
        self.txt_actual = wx.TextCtrl(self, style=wx.TE_READONLY)

        self.chk_flow = wx.CheckBox(self, label='Flow control')

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
        sizer_cfg = wx.GridSizer(rows=4, cols=2, vgap=1, hgap=1)

        sizer_cfg.Add(self.label_speed, flags)
        sizer_cfg.Add(self.label_actual, flags)
        sizer_cfg.Add(self.spin_speed, flags)
        sizer_cfg.Add(self.txt_actual, flags)
        sizer_cfg.Add(self.btn_change_rate, flags)
        sizer_cfg.Add(self.btn_stop, flags)

        sizer_cfg.Add(self.chk_flow, flags)
        sizer_cfg.AddSpacer(1)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_rate_change)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer_update)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.chk_flow.Bind(wx.EVT_CHECKBOX, self.on_flow)

    def on_rate_change(self, evt):
        value = self.spin_speed.GetValue()
        if self.chk_flow.IsChecked():
            self.hw.set_flow(value)
        else:
            self.hw.set_speed(value)

    def on_stop(self, evt):
        if self.chk_flow.IsChecked():
            self.hw.set_flow(0)
        else:
            self.hw.set_speed(0)

    def on_timer(self, evt):
        self.update_controls_from_hardware()

    def update_controls_from_hardware(self):
        if self.chk_flow.IsChecked():
            value = self.hw.get_flow()
        else:
            value = self.hw.get_speed()
        self.txt_actual.SetValue(f'{value}')

    def on_flow(self, evt):
        if self.chk_flow.IsChecked():
            self.label_actual.SetLabel('Set Flow (ml/min):')
            self.label_speed.SetLabel('Actual Flow (ml/min):')
        else:
            self.label_actual.SetLabel('Set Speed (rpm):')
            self.label_speed.SetLabel('Actual Speed (rpm):')

    def on_close(self, evt):
        self.timer_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = Paneli30(self, pump)

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
    lgr = logging.getLogger()
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(lgr, logging.DEBUG)
    utils.setup_file_logger(lgr, logging.DEBUG, filename='panel_i30_debug')
    utils.configure_matplotlib_logging()

    SYS_HW.load_hardware_from_config()

    pump = PuraLevi30('Pump 1')
    try:
        pump.read_config()
    except i30Exception:
        lgr.warning(f'{pump.name} not found. Loading mock')
        pump.hw = Mocki30()
        SYS_HW.pump1 = pump

    app = MyTestApp(0)
    app.MainLoop()
