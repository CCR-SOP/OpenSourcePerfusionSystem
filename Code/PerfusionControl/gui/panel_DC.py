# -*- coding: utf-8 -*-
""" Panel class for controlling analog output

@project: LiverPerfusion NIH
@author: Stephie Lux NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem


class PanelDC(wx.Panel):
    def __init__(self, parent, sensor):
        self.name = sensor.name
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self.pump = sensor.hw

        self.panel_dc = PanelDCControl(self, self.pump)

        font = wx.Font()
        font.SetPointSize(int(16))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.static_box.SetFont(font)
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.__do_layout()
        self.__set_bindings()

    def close(self):
        pass

    def __do_layout(self):

        self.sizer.Add(self.panel_dc, wx.SizerFlags(1).Expand().Proportion(1))

        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        pass


class PanelDCControl(wx.Panel):
    def __init__(self, parent, pump):
        self.name = pump.name
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
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

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Expand()
        self.sizer_cfg = wx.GridSizer(rows=3, cols=2, vgap=1, hgap=1)

        self.sizer_cfg.Add(self.label_offset, flags)
        self.sizer_cfg.Add(self.label_real, flags)
        self.sizer_cfg.Add(self.entered_offset, flags)
        self.sizer_cfg.Add(self.text_real, flags)
        self.sizer_cfg.Add(self.btn_change_rate, flags)
        self.sizer_cfg.Add(self.btn_stop, flags)

        self.sizer_cfg.SetSizeHints(self.GetParent())
        self.sizer.Add(self.sizer_cfg, flags)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_update(self, evt):
        self._lgr.debug('on update')
        new_flow = self.entered_offset.GetValue()
        if self.pump:
            self._lgr.debug('setting flow')
            self.pump.set_flow(new_flow)
            # volts = self.pump.mlpermin_to_volts(new_flow)
            self.text_real.SetValue(str(new_flow*0.99))

    def on_stop(self, evt):
        if self.pump:
            self.pump.set_flow(0)

    def on_close(self, evt):
        pass


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        pump_name = 'Dialysis Blood Pump'
        self.panel = PanelDC(self, SYS_PERFUSION.get_sensor(pump_name))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Close()
        self.Destroy()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('panel_DC', logging.DEBUG)

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system
        # close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()