# -*- coding: utf-8 -*-
""" Application to display dual Levitronix centrifugal pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem


class LeviPumpPanel(wx.Panel):
    def __init__(self, parent, sensors):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)

        self.panels = {}
        log_names = []
        for sensor in sensors:
            panel = BaseLeviPumpPanel(self, sensor)
            self.panels[sensor.name] = panel
            self._lgr.debug(f'logging to {sensor.name}')
            log_names.append(sensor.name)

        self.text_log_levi = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)
        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        for panel in self.panels.values():
            self.sizer.Add(panel, wx.SizerFlags().Expand())
        self.sizer.Add(self.text_log_levi, wx.SizerFlags().Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.panels.values():
            panel.Close()


class BaseLeviPumpPanel(wx.Panel):
    def __init__(self, parent, sensor):  # autolevipump eventually
        super().__init__(parent)
        self.name = sensor.name
        self._lgr = utils.get_object_logger(__name__, self.name)

        self.autolevipump = sensor

        font = wx.Font()
        font.SetPointSize(int(12))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)

        # Buttons for functionality
        self.btn_update = wx.Button(self, label='Update')
        self.btn_start = wx.ToggleButton(self, label='Start')
        self.chk_auto = wx.CheckBox(self, label='Maintain\nFlow')

        self.chk_sine = wx.CheckBox(self, label='Sine Output')
        self.label_min = wx.StaticText(self, label='Min Speed\n(rpm):')
        self.spin_min = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=10000, initial=0, inc=100)
        self.label_max = wx.StaticText(self, label='Max Speed\n(rpm):')
        self.spin_max = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=10000, initial=0, inc=100)
        self.label_freq = wx.StaticText(self, label='Freq\n(Hz):')
        self.spin_freq = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=100, initial=0, inc=1)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Expand()

        self.sizer_cfg = wx.BoxSizer(wx.HORIZONTAL)

        sizer_waveform = wx.BoxSizer(wx.VERTICAL)
        sizer_waveform.Add(self.chk_sine, wx.SizerFlags().Border(wx.BOTTOM, 5))

        sizer_params = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_min)
        sizer.Add(self.spin_min)
        sizer_params.Add(sizer, wx.SizerFlags().Border(wx.RIGHT, 5))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_max)
        sizer.Add(self.spin_max)
        sizer_params.Add(sizer, wx.SizerFlags().Border(wx.RIGHT, 5))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_freq)
        sizer.Add(self.spin_freq)
        sizer_params.Add(sizer, wx.SizerFlags().Border(wx.RIGHT, 5))

        sizer_waveform.Add(sizer_params, wx.SizerFlags().Border(wx.RIGHT, 5))

        sizer_btn = wx.BoxSizer(wx.VERTICAL)
        sizer_btn.Add(self.btn_update)
        sizer_btn.Add(self.btn_start)
        sizer_btn.Add(self.chk_auto)

        self.sizer.Add(sizer_waveform)
        self.sizer.Add(sizer_btn)


        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        # self.input_speed.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeSpeed)
        # self.input_speed.Bind(wx.EVT_TEXT, self.OnChangeSpeed)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.btn_start.Bind(wx.EVT_TOGGLEBUTTON, self.OnStart)
        self.Bind(wx.EVT_CHECKBOX, self.OnAuto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnAuto(self, evt):
        if not self.chk_auto.IsChecked():
            self.autolevipump.hw.stop()
        else:
            pass
            # self.autolevipump.hw.start()
        self.input_speed.Enable(not self.chk_auto.IsChecked())
        self.btn_update.Enable(not self.chk_auto.IsChecked())

    def OnClose(self, evt):
        self.autolevipump.hw.stop()

    def OnStart(self, evt):
        if self.btn_start.GetLabel() == 'Start':
            self.ChangeRPM()
            self.btn_start.SetLabel('Stop')
        else:
            self.autolevipump.hw.stop()  # TODO: remove hw. eventually
            self.btn_start.SetLabel('Start')

    def OnChangeSpeed(self, evt):
        self.btn_update.Enable(True)
        self.input_speed.SetBackgroundColour(wx.RED)

    def OnUpdate(self, evt):
        self.ChangeRPM()
        self.input_speed.SetBackgroundColour(wx.WHITE)
        self.input_speed.Refresh()

    def ChangeRPM(self):
        rpm = self.input_speed.GetValue()
        self.autolevipump.hw.set_speed(rpm=rpm)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        # TODO: Change to automations eventually
        sensor_names = ['Arterial PuraLev', 'Venous PuraLev']
        sensors = []
        for name in sensor_names:
            sensors.append(SYS_PERFUSION.get_sensor(name))

        self.panel = LeviPumpPanel(self, sensors)
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

    SYS_PERFUSION = PerfusionSystem()
    try:
        SYS_PERFUSION.open()
        SYS_PERFUSION.load_all()
        SYS_PERFUSION.load_automations()
    except Exception as e:
        # if anything goes wrong loading the perfusion system close the hardware and exit the program
        SYS_PERFUSION.close()
        raise e

    app = MyTestApp(0)
    app.MainLoop()
    SYS_PERFUSION.close()
