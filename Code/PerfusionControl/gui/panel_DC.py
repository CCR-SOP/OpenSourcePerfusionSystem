# -*- coding: utf-8 -*-
""" Panel class for controlling analog output

@project: LiverPerfusion NIH
@author: Stephie Lux NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
import wx.lib.colourdb
import numpy as np

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

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.static_box.SetFont(utils.get_header_font())
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
        font.SetPointSize(10)

        wx.lib.colourdb.updateColourDB()
        self.normal_color = self.GetBackgroundColour()
        self.warning_color = wx.Colour('orange')

        self.label_offset = wx.StaticText(self, label='Flow (mL/min):')
        self.spin_offset = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=50, inc=.5, initial=0)
        self.label_offset.SetFont(font)
        self.spin_offset.SetFont(font)

        self.btn_change_rate = wx.Button(self, label='Update Rate')
        self.btn_change_rate.SetFont(font)
        self.btn_start = wx.ToggleButton(self, label='Start')
        self.btn_start.SetFont(font)

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer_spin = wx.BoxSizer(wx.VERTICAL)
        sizer_spin.Add(self.label_offset, wx.SizerFlags().Border(wx.RIGHT, 10))
        sizer_spin.Add(self.spin_offset)

        sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons.Add(self.btn_change_rate)
        sizer_buttons.Add(self.btn_start)

        self.sizer.Add(sizer_spin, wx.SizerFlags().Border(wx.BOTTOM, 10))
        self.sizer.Add(sizer_buttons)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.btn_change_rate.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.on_start)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)

    def warn_on_difference(self, ctrl, actual, set_value):
        old_color = ctrl.GetClassDefaultAttributes().colBg
        tooltip_msg = ''

        if not np.isclose(actual, set_value):
            color = self.warning_color
            tooltip_msg = f'Actual {actual:02f}'
        else:
            color = self.normal_color

        ctrl.SetBackgroundColour(color)
        ctrl.Refresh()

        ctrl.SetToolTip(tooltip_msg)

    def update_controls_from_hardware(self, evt=None):
        self.warn_on_difference(self.spin_offset, self.pump.last_flow, self.spin_offset.GetValue())

    def on_start(self, evt):
        in_start_mode = self.btn_start.GetValue()
        new_flow = self.spin_offset.GetValue()
        if self.pump:
            if in_start_mode:
                self.btn_start.SetLabel("Stop")
                self.pump.set_flow(new_flow)
            else:
                self.pump.set_flow(0)
                self.btn_start.SetLabel("Start")


    def on_update(self, evt):
        new_flow = self.spin_offset.GetValue()
        in_start_mode = self.btn_start.GetValue()
        if self.pump:
            if in_start_mode:
                self.pump.set_flow(new_flow)
                self.update_controls_from_hardware()





            



    def on_close(self, evt):
        self.timer_gui_update.Stop()


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