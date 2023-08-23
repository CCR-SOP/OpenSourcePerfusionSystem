# -*- coding: utf-8 -*-
""" Example to test PID

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import wx
import logging

from simple_pid import PID

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.PerfusionSystem import PerfusionSystem
from gui.plotting import SensorPlot, PanelPlotting


class PanelPID(wx.Panel):
    def __init__(self, parent, automation):
        self.parent = parent
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.automation = automation

        self.panel_flow = PanelPlotting(self)
        self.plot_flow = SensorPlot(automation.data_source, self.panel_flow.axes)
        self.plot_flow.set_reader(automation.data_source)
        self.panel_flow.add_plot(self.plot_flow)

        self.panel_speed = PanelPlotting(self)
        self.plot_speed = SensorPlot(automation.device, self.panel_speed.axes)
        self.plot_speed.set_reader(automation.device.get_reader())
        self.panel_speed.add_plot(self.plot_speed)

        self.label_p = wx.StaticText(self, label='Proportional')
        self.spin_p = wx.SpinCtrlDouble(self, min=0, max=32000, initial=10, inc=100)
        self.spin_p.SetDigits(3)

        self.label_i = wx.StaticText(self, label='Integral')
        self.spin_i = wx.SpinCtrlDouble(self, min=0, max=32000, initial=10, inc=100)
        self.spin_i.SetDigits(3)

        self.label_d = wx.StaticText(self, label='Derivative')
        self.spin_d = wx.SpinCtrlDouble(self, min=0, max=100, initial=10, inc=0.1)
        self.spin_d.SetDigits(3)

        self.label_setpoint = wx.StaticText(self, label='SetPoint')
        self.spin_setpoint = wx.SpinCtrlDouble(self, min=0, max=10000, initial=5000, inc=100)
        self.spin_setpoint.SetDigits(0)

        self.btn_start_auto = wx.ToggleButton(self, label="Start Auto")
        self.btn_start_pump= wx.ToggleButton(self, label="Start Pump")
        self.btn_update_auto = wx.Button(self, label="Update")

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_pids = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_p)
        sizer.Add(self.spin_p)
        sizer_pids.Add(sizer, wx.SizerFlags().CenterVertical().Proportion(1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_i)
        sizer.Add(self.spin_i)
        sizer_pids.Add(sizer, wx.SizerFlags().CenterVertical().Proportion(1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_d)
        sizer.Add(self.spin_d)
        sizer_pids.Add(sizer, wx.SizerFlags().CenterVertical().Proportion(1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_setpoint)
        sizer.Add(self.spin_setpoint)
        sizer_pids.AddSpacer(5)
        sizer_pids.Add(sizer, wx.SizerFlags().CenterVertical().Proportion(1))

        sizer_btn = wx.BoxSizer(wx.HORIZONTAL)
        sizer_btn.Add(self.btn_start_auto, wx.SizerFlags().Proportion(1).CenterVertical())
        sizer_btn.Add(self.btn_start_pump, wx.SizerFlags().Proportion(1).CenterVertical())
        sizer_btn.Add(self.btn_update_auto, wx.SizerFlags().Proportion(1).CenterVertical())

        self.sizer.Add(sizer_pids, wx.SizerFlags().Proportion(1).CenterHorizontal())
        self.sizer.Add(sizer_btn, wx.SizerFlags().Proportion(1).CenterHorizontal())
        self.sizer.Add(self.panel_flow, wx.SizerFlags().Expand().Proportion(4))
        self.sizer.Add(self.panel_speed, wx.SizerFlags().Expand().Proportion(4))

        self.SetSizer(self.sizer)

        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start_auto.Bind(wx.EVT_TOGGLEBUTTON, self.on_start_stop_auto)
        self.btn_start_pump.Bind(wx.EVT_TOGGLEBUTTON, self.on_start_stop_pump)
        self.btn_update_auto.Bind(wx.EVT_BUTTON, self.on_update_auto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel_flow.Destroy()
        self.panel_speed.Destroy()
        self.Destroy()

    def on_start_stop_auto(self, evt):
        if not evt.IsChecked():
            self.btn_start_auto.SetLabel('Start Auto')
            self.automation.stop()
        else:
            self.btn_start_auto.SetLabel('Stop Auto')
            self.automation.start()

    def on_start_stop_pump(self, evt):
        if not evt.IsChecked():
            self.btn_start_pump.SetLabel('Start Pump')
            self.automation.device.hw.set_speed(0)
        else:
            self.btn_start_pump.SetLabel('Stop Pump')
            self.automation.device.hw.set_speed(5000)

    def on_update_auto(self, evt):
        p = self.spin_p.GetValue()
        i = self.spin_i.GetValue()
        d = self.spin_d.GetValue()
        setpoint = self.spin_setpoint.GetValue()
        self.automation.update_tunings(p, i, d)
        self.automation.update_setpoint(setpoint)

    def update_controls(self):
        if self.automation.pid:
            p, i, d = self.automation.pid.tunings
            self.spin_p.SetValue(p)
            self.spin_i.SetValue(i)
            self.spin_d.SetValue(d)
            self.spin_setpoint.SetValue(self.automation.pid.setpoint)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.auto = SYS_PERFUSION.get_automation('TestAutoFlowDC')
        self.flow = SYS_PERFUSION.get_sensor('Portal Vein Flow')
        self.flow.hw.cfg.cal_pt1_target = 0.0
        self.flow.hw.cfg.cal_pt1_reading = 0.0
        self.flow.hw.cfg.cal_pt2_target = 760
        self.flow.hw.cfg.cal_pt2_reading = 0.76
        self.panel = PanelPID(self, automation=self.auto)
        self.panel.update_controls()


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == '__main__':
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('ex_gui_test_pid', logging.DEBUG)

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
