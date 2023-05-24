# -*- coding: utf-8 -*-
""" Application to display dual Levitronix centrifugal pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
from time import sleep

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem


class BaseLeviPumpPanel(wx.Panel):
    def __init__(self, parent, sensor):  # autolevipump eventually
        super().__init__(parent)
        self.name = sensor.name
        self._lgr = utils.get_object_logger(__name__, self.name)

        self.autolevipump = sensor

        font = wx.Font()
        font.SetPointSize(int(12))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        # Pump speed and flow
        self.label_speed = wx.StaticText(self, label='Speed (rpm):')
        self.input_speed = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1700, initial=0, inc=25)
        self.label_speed.SetFont(font)
        self.input_speed.SetFont(font)

        self.label_corr_flow = wx.StaticText(self, label='Corresponding Flow (mL/min):')
        self.value_corr_flow = wx.TextCtrl(self, style=wx.TE_READONLY, value='0')  # TODO: figure out titration
        self.label_corr_flow.SetFont(font)
        self.value_corr_flow.SetFont(font)

        # Buttons for functionality
        self.btn_update = wx.Button(self, label='Update')
        self.btn_start = wx.ToggleButton(self, label='Start')
        self.chk_auto = wx.CheckBox(self, label='Auto Adjust based on flow')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Expand()

        self.sizer_cfg = wx.FlexGridSizer(cols=2)
        self.sizer_cfg.AddGrowableCol(0, 2)
        self.sizer_cfg.AddGrowableCol(1, 1)

        self.sizer_cfg.Add(self.label_speed, flags)
        self.sizer_cfg.Add(self.input_speed, flags)
        self.sizer_cfg.Add(self.label_corr_flow, flags)
        self.sizer_cfg.Add(self.value_corr_flow, flags)

        self.sizer_cfg.Add(self.btn_update, flags)
        self.sizer_cfg.Add(self.btn_start, flags)
        self.sizer_cfg.Add(self.chk_auto, flags)
        self.sizer_cfg.AddSpacer(1)
        self.sizer_cfg.SetSizeHints(self.GetParent())

        self.sizer.Add(self.sizer_cfg, flags)
        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.input_speed.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeSpeed)
        self.input_speed.Bind(wx.EVT_TEXT, self.OnChangeSpeed)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)
        self.Bind(wx.EVT_CHECKBOX, self.OnAuto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnAuto(self, evt):
        if not self.chk_auto.IsChecked():
            self.autolevipump.stop()
        else:
            self.autolevipump.start()
        self.input_speed.Enable(not self.chk_auto.IsChecked())
        self.btn_update.Enable(not self.chk_auto.IsChecked())

    def OnClose(self, evt):
        self.autolevipump.stop()

    def OnStart(self, evt):
        flow = self.value_corr_flow.GetValue()
        if flow != '0':
            self.ChangeRPM()
            self.autolevipump.hw.start()  # TODO: remove hw. eventually
            self.btn_start.SetLabel('Stop')
        else:
            self.autolevipump.hw.stop()
            self.btn_start.SetLabel('Start)')

    def OnChangeSpeed(self, evt):
        self.btn_update.Enable(True)
        self.input_speed.SetBackgroundColour(wx.RED)

    def OnUpdate(self, evt):
        self.ChangeRPM()
        self.input_speed.SetBackgroundColour(wx.WHITE)
        self.input_speed.Refresh()
        # self.btn_update.Enable(False)  # needed?
        # TODO: update value_corr_flow

    def ChangeRPM(self):
        rpm = self.input_speed.GetValue()
        self.autolevipump.hw.set_speed(rpm=rpm)
        sleep(1.0)  # needed?


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        # TODO: add dummy automation in config, pyPerfusion
        # automation_names = ['Arterial Pump Automation', 'Venous Pump Automation']
        # automations = []
        # for name in automation_names:
            # automations.append(SYS_PERFUSION.get_automation(name))
        name = 'Test i30'
        sensor = SYS_PERFUSION.get_sensor(name)
        self.panel = BaseLeviPumpPanel(self, sensor)  # change to automations eventually
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
    utils.setup_default_logging('panel_levitronix_pumps', logging.DEBUG)
    # TODO: add correct logging statements

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
