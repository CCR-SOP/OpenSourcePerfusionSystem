# -*- coding: utf-8 -*-
""" Application to display dual gas mixer controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx
import wx.lib.colourdb
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyPerfusion.PerfusionSystem import PerfusionSystem
from gui.panel_config import AutomationConfig


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, automations):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)

        self.panels = []
        self.configs = []
        log_names = []
        for automation in automations:
            panel = BaseGasMixerPanel(self, automation)
            self.panels.append(panel)
            log_names.append(automation.gas_device.name)
            if automation.name == 'Arterial Gas Mixer Automation':
                panel.config.add_var('pH_min', 'pH (min)', limits=(0, 0.01, 14), decimal_places=2)
                panel.config.add_var('pH_max', 'pH (max)', limits=(0, 0.01, 14), decimal_places=2)
                panel.config.add_var('CO2_min', 'CO2 (min)', limits=(0, 1, 100))
                panel.config.add_var('CO2_max', 'CO2 (max)', limits=(0, 1, 100))
                panel.config.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                panel.config.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                panel.config.do_layout()
                panel.config.set_bindings()
            elif automation.name == 'Venous Gas Mixer Automation':
                panel.config.add_var('pH_min', 'pH (min)', limits=(0, 1, 14), decimal_places=2)
                panel.config.add_var('pH_max', 'pH (max)', limits=(0, 1, 14), decimal_places=2)
                panel.config.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                panel.config.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                panel.config.do_layout()
                panel.config.set_bindings()

        self._lgr.debug(f'Log names are {log_names}')
        # Add logs
        log_names.append('AutoGasMixer')
        self._lgr.debug(f'Log names are {log_names}')
        self.text_log_gas_mixer = utils.create_log_display(self, logging.INFO, log_names, use_last_name=True)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.panels[0], wx.SizerFlags().Proportion(1).Expand())
        self.sizer.Add(self.panels[1], wx.SizerFlags().Proportion(1).Expand())
        self.sizer.Add(self.text_log_gas_mixer, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)


    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()


class BaseGasMixerPanel(wx.Panel):
    def __init__(self, parent, autogasmixer):
        super().__init__(parent)
        self._lgr = logging.getLogger(__name__)
        self.name = autogasmixer.name

        self.autogasmixer = autogasmixer

        if self.autogasmixer.gas_device is not None:
            # for the gases we want (O2, CO2)
            self.gas1_name = self.autogasmixer.gas_device.get_gas_type(1)
            self.gas2_name = self.autogasmixer.gas_device.get_gas_type(2)
        else:
            self.gas1_name = "NA"
            self.gas2_name = "NA"

        wx.lib.colourdb.updateColourDB()
        self.normal_color = self.GetBackgroundColour()
        self.warning_color = wx.Colour('orange')

        font = wx.Font()
        font.SetPointSize(int(12))

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name, style=wx.ALIGN_CENTER_HORIZONTAL)
        self.static_box.SetFont(utils.get_header_font())
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        # Adjustable parameters
        self.text_flow_adjust = wx.TextCtrl(self, value='Total Flow (mL/min)',
                                            style=wx.TE_READONLY | wx.BORDER_NONE)
        self.spin_flow_adjust = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400,
                                                  initial=int(self.autogasmixer.gas_device.get_total_flow()), inc=1)
        self.text_flow_adjust.SetFont(font)
        self.spin_flow_adjust.SetFont(font)

        self.slider_mix = wx.Slider(self, value=0, minValue=0, maxValue=100,
                                    style=wx.SL_INVERSE | wx.SL_VALUE_LABEL)

        self.label_gas1 = wx.StaticText(self, label=f'{self.gas1_name}', style=wx.ALIGN_LEFT)
        self.label_gas2 = wx.StaticText(self, label=f'{self.gas2_name}', style=wx.ALIGN_RIGHT)
        self.label_gas1.SetFont(font)
        self.label_gas2.SetFont(font)

        self.label_gas1_mix = wx.StaticText(self, label=f'0 %', style=wx.ALIGN_LEFT)
        self.label_gas2_mix = wx.StaticText(self, label=f'0 %', style=wx.ALIGN_RIGHT)
        self.label_gas1_flow = wx.StaticText(self, label=f'ml/min', style=wx.ALIGN_LEFT)
        self.label_gas2_flow = wx.StaticText(self, label=f'ml/min', style=wx.ALIGN_RIGHT)
        self.label_gas1_mix.SetFont(font)
        self.label_gas2_mix.SetFont(font)
        self.label_gas1_flow.SetFont(font)
        self.label_gas2_flow.SetFont(font)

        # Buttons for functionality
        self.btn_flow = wx.ToggleButton(self, label='Enable Flow')
        self.btn_update = wx.Button(self, label='Update')
        self.btn_auto = wx.ToggleButton(self, label='Automate')

        self.config = AutomationConfig(self, self.autogasmixer)

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        sizer_gas1 = wx.BoxSizer(wx.VERTICAL)
        sizer_gas1.Add(self.label_gas1, wx.SizerFlags().Proportion(1))
        sizer_gas1.Add(self.label_gas1_flow, wx.SizerFlags().Proportion(1))
        sizer_gas1.Add(self.label_gas1_mix, wx.SizerFlags().Proportion(1))

        sizer_gas2 = wx.BoxSizer(wx.VERTICAL)
        sizer_gas2.Add(self.label_gas2, wx.SizerFlags().Proportion(1).Right())
        sizer_gas2.Add(self.label_gas2_flow, wx.SizerFlags().Proportion(1).Right())
        sizer_gas2.Add(self.label_gas2_mix, wx.SizerFlags().Proportion(1).Right())

        sizer_flow = wx.BoxSizer(wx.HORIZONTAL)
        sizer_flow.Add(self.text_flow_adjust, wx.SizerFlags().CenterVertical().Proportion(2).Border(wx.RIGHT, 5))
        sizer_flow.Add(self.spin_flow_adjust, wx.SizerFlags().CenterVertical().Proportion(1))

        sizer_adjust = wx.BoxSizer(wx.VERTICAL)
        sizer_adjust.Add(sizer_flow, wx.SizerFlags().Center().Proportion(1))
        sizer_adjust.Add(self.slider_mix, wx.SizerFlags().Expand())

        sizer_control = wx.BoxSizer(wx.HORIZONTAL)
        sizer_control.Add(sizer_gas1, wx.SizerFlags().Proportion(1))
        sizer_control.Add(sizer_adjust, wx.SizerFlags().Proportion(2))
        sizer_control.Add(sizer_gas2, wx.SizerFlags().Proportion(1))

        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons.Add(self.config, wx.SizerFlags().Proportion(0))
        sizer_buttons.AddStretchSpacer(2)
        sizer_buttons.Add(self.btn_update, wx.SizerFlags().Expand().Proportion(1))
        sizer_buttons.Add(self.btn_flow, wx.SizerFlags().Expand().Proportion(1))
        sizer_buttons.Add(self.btn_auto, wx.SizerFlags().Expand().Proportion(1))

        sizer_bottom = wx.BoxSizer(wx.VERTICAL)
        sizer_bottom.Add(sizer_buttons, wx.SizerFlags().Proportion(1).Expand())

        self.sizer.Add(sizer_control, wx.SizerFlags().Expand())
        self.sizer.Add(sizer_bottom, wx.SizerFlags().Expand())

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.sizer)
        self.Layout()

        self.update_controls_from_hardware()

    def __set_bindings(self):
        self.btn_flow.Bind(wx.EVT_TOGGLEBUTTON, self.OnFlow)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.spin_flow_adjust.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeFlow)
        self.spin_flow_adjust.Bind(wx.EVT_TEXT, self.OnChangeFlow)
        self.slider_mix.Bind(wx.EVT_SLIDER, self.OnChangeGas)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnAuto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.config.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()

    def update_controls(self):
        gas1_mix_set = self.autogasmixer.gas_device.percent[0]
        gas2_mix_set = self.autogasmixer.gas_device.percent[1]
        gas1_flow_set = self.autogasmixer.gas_device.total_flow * (gas1_mix_set / 100.0)
        gas2_flow_set =  self.autogasmixer.gas_device.total_flow * (gas2_mix_set / 100.0)
        gas1_mix_actual = self.autogasmixer.gas_device.get_percent_value(1)
        gas2_mix_actual = self.autogasmixer.gas_device.get_percent_value(2)
        gas1_flow_actual = self.autogasmixer.gas_device.get_target_sccm(1)
        gas2_flow_actual = self.autogasmixer.gas_device.get_target_sccm(2)

        self.label_gas1_mix.SetLabel(f'{gas1_mix_actual}%')
        self.label_gas2_mix.SetLabel(f'{gas2_mix_actual}%')
        self.label_gas1_flow.SetLabel(f'{gas1_flow_actual} ml/min')
        self.label_gas2_flow.SetLabel(f'{gas2_flow_actual} ml/min')

        self.warn_on_difference(self.label_gas1_mix, gas1_mix_actual, gas1_mix_set)
        self.warn_on_difference(self.label_gas2_mix, gas2_mix_actual, gas2_mix_set)
        self.warn_on_difference(self.label_gas1_flow, gas1_flow_actual, gas1_flow_set)
        self.warn_on_difference(self.label_gas2_flow, gas2_flow_actual, gas2_flow_set)

    def warn_on_difference(self, ctrl, actual, set_value):
        old_color = ctrl.GetBackgroundColour()
        tooltip_msg = ''

        if not np.isclose(actual, set_value):
            color = self.warning_color
            tooltip_msg = f'Expected {set_value:02f}'
        else:
            color = self.normal_color

        # this prevents "blinking" text by only refreshing when somthing changes
        if old_color != color:
            ctrl.SetBackgroundColour(color)
            ctrl.Refresh()
        ctrl.SetToolTip(tooltip_msg)

    def _update_manual_entries(self):
        self.spin_flow_adjust.SetValue(f'{self.autogasmixer.gas_device.get_total_flow()}')
        self.slider_mix.SetValue(int(self.autogasmixer.gas_device.get_percent_value(1)))

    def OnAuto(self, evt):
        self._lgr.debug(f'button value is {self.btn_auto.GetValue()}')
        if not self.btn_auto.GetValue():
            self._update_manual_entries()
            self.autogasmixer.stop()
            self.btn_auto.SetLabel('Automate')
        else:
            self.autogasmixer.start()
            self.btn_auto.SetLabel('Switch to Manual Control')
        self.slider_mix.Enable(not self.btn_auto.GetValue())
        self.spin_flow_adjust.Enable(not self.btn_auto.GetValue())
        self.Refresh()

    def OnFlow(self, evt):
        working_status = self.autogasmixer.gas_device.get_working_status()
        if working_status == 0:  # 0 is off
            self.autogasmixer.gas_device.set_working_status(turn_on=True)
            if self.btn_auto.GetValue():
                self.autogasmixer.start()
            else:
                self._update_manual_entries()
        else:
            self.autogasmixer.gas_device.set_working_status(turn_on=False)
            self.autogasmixer.stop()
            self._lgr.debug(f'{self.name} is off')

    def OnChangeFlow(self, evt):
        self.btn_update.Enable(True)
        self.spin_flow_adjust.SetBackgroundColour(wx.RED)

    def OnChangeGas(self, evt):
        self.btn_update.Enable(True)
        self.slider_mix.SetBackgroundColour(wx.RED)

    def OnUpdate(self, evt):
        self.autogasmixer.gas_device.set_percent_value(2, 100 - float(self.slider_mix.GetValue()))
        self.autogasmixer.gas_device.set_total_flow(int(self.spin_flow_adjust.GetValue()))
        self.spin_flow_adjust.SetValue(self.autogasmixer.gas_device.get_total_flow())
        self.spin_flow_adjust.SetBackgroundColour(wx.WHITE)
        self.spin_flow_adjust.Refresh()
        self.slider_mix.SetBackgroundColour(self.normal_color)
        self.slider_mix.Refresh()

        self.btn_update.Enable(False)

    def update_controls_from_hardware(self, evt=None):
        working_status = self.autogasmixer.gas_device.get_working_status()
        self.btn_flow.SetValue(working_status)
        if working_status:
            self.btn_flow.SetLabel('Disable Flow')
            # self.btn_update.Enable(False)
        else:
            self.btn_flow.SetLabel('Enable Flow')
            # self.btn_update.Enable(True)

        self.update_controls()

    def OnClose(self, evt):
        self.timer_gui_update.Stop()
        self.autogasmixer.stop()
        self.autogasmixer.gas_device.set_working_status(turn_on=False)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        automation_names = ['Arterial Gas Mixer Automation', 'Venous Gas Mixer Automation']
        automations = []
        for name in automation_names:
            automations.append(SYS_PERFUSION.get_automation(name))
        self.panel = GasMixerPanel(self, automations)
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
    utils.setup_default_logging('panel_gas_mixers', logging.DEBUG)

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
