# -*- coding: utf-8 -*-
""" Panel class for controlling pumps

@project: LiverPerfusion NIH
@author: John Kakareka NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import sleep
import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.pyPump import Pump


class PanelPump(wx.Panel):
    def __init__(self, parent, name, pump):
        wx.Panel.__init__(self, parent, -1)
        self.name = name
        self._logger = utils.get_object_logger(__name__, self.name)
        self.parent = parent
        self.pump = pump

        self.panel_ctrl = PanelPumpControl(self, self.name, self.pump)

        font = wx.Font()
        font.SetPointSize(int(16))

        static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        self.pump.stop()

    def __do_layout(self):

        self.sizer.Add(self.panel_ctrl, wx.SizerFlags(1).Expand())

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class PanelPumpControl(wx.Panel):
    def __init__(self, parent, name, pump):
        wx.Panel.__init__(self, parent, -1)
        self._lgr = logging.getLogger(__name__)
        self.parent = parent
        self.name = name
        self.pump = pump

        font = wx.Font()
        font.SetPointSize(int(12))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_offset = wx.StaticText(self, label='Set Speed (mL/min):')
        self.entered_offset = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5, initial=0)
        self.label_real = wx.StaticText(self, label='Actual Speed (mL/min):')
        self.text_real = wx.TextCtrl(self, style=wx.TE_READONLY, value=str(0))
        self.label_offset.SetFont(font)
        self.entered_offset.SetFont(font)
        self.label_real.SetFont(font)
        self.text_real.SetFont(font)

        self.btn_change_rate = wx.Button(self, label='Update Rate')
        self.btn_change_rate.SetFont(font)
        self.btn_stop = wx.Button(self, label='Stop')
        self.btn_stop.SetFont(font)

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center()
        sizer_cfg = wx.GridSizer(rows=3, cols=2, vgap=1, hgap=1)

        sizer_cfg.Add(self.label_offset, flags)
        sizer_cfg.Add(self.label_real, flags)
        sizer_cfg.Add(self.entered_offset, flags)
        sizer_cfg.Add(self.text_real, flags)
        sizer_cfg.Add(self.btn_change_rate, flags)
        sizer_cfg.Add(self.btn_stop, flags)

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_update(self, evt):
        new_flow = self.entered_offset.GetValue()
        # TODO this should be done in a calibration, not a hard-coded value
        self.pump.set_flow(new_flow)

    def on_stop(self, evt):
        self.pump.set_flow(0)

    def update_controls_from_hardware(self, evt=None):
        if self.pump:
            self.text_real.SetValue(f'{self.pump.last_flow:.3f}')

    def on_close(self, evt):
        self.timer_gui_update.Stop()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = PanelPump(self, pump_name, pump)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        SYS_HW.stop()
        pump.stop()
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

    SYS_HW.load_all()

    pump_name = 'Dialysate Inflow Pump'
    try:
        pump = Pump(name=pump_name)
        pump.read_config()
    except PerfusionConfig.MissingConfigSection:
        print(f'Could not find sensor called {pump_name} in actuators.ini')
        SYS_HW.stop()
        raise SystemExit(1)
    pump.start()

    app = MyTestApp(0)
    app.MainLoop()
