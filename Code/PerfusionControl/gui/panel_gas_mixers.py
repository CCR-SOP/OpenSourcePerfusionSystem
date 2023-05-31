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
        for automation in automations:
            panel = BaseGasMixerPanel(self, automation)
            self.panels.append(panel)
            if automation.name == 'Arterial Gas Mixer Automation':
                self.config_arterial = AutomationConfig(self, automation)
                self.config_arterial.add_var('pH_min', 'pH (min)', limits=(0, 0.01, 14), decimal_places=2)
                self.config_arterial.add_var('pH_max', 'pH (max)', limits=(0, 0.01, 14), decimal_places=2)
                self.config_arterial.add_var('CO2_min', 'CO2 (min)', limits=(0, 1, 100))
                self.config_arterial.add_var('CO2_max', 'CO2 (max)', limits=(0, 1, 100))
                self.config_arterial.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                self.config_arterial.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                self.config_arterial.do_layout()
                self.config_arterial.set_bindings()
            elif automation.name == 'Venous Gas Mixer Automation':
                self.config_venous = AutomationConfig(self, automation)
                self.config_venous.add_var('pH_min', 'pH (min)', limits=(0, 1, 14), decimal_places=2)
                self.config_venous.add_var('pH_max', 'pH (max)', limits=(0, 1, 14), decimal_places=2)
                self.config_venous.add_var('O2_min', 'O2 (min)', limits=(0, 1, 100))
                self.config_venous.add_var('O2_max', 'O2 (max)', limits=(0, 1, 100))
                self.config_venous.do_layout()
                self.config_venous.set_bindings()
        self.static_box = wx.StaticBox(self, wx.ID_ANY, label="Gas Mixers")
        self.wrapper = wx.StaticBoxSizer(self.static_box, wx.HORIZONTAL)

        self.text_log_arterial = utils.create_log_display(self, logging.INFO, ['Arterial Gas Mixer'])
        self.text_log_venous = utils.create_log_display(self, logging.INFO, ['Venous Gas Mixer'])

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()
        self.sizer = wx.FlexGridSizer(cols=2, vgap=1, hgap=1)

        for panel in self.panels:
            self.sizer.Add(panel, flags)

        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)

        self.sizer.Add(self.config_arterial, flags.Proportion(0))
        self.sizer.Add(self.config_venous, flags.Proportion(0))
        self.sizer.Add(self.text_log_arterial, flags)
        self.sizer.Add(self.text_log_venous, flags)

        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)

        self.sizer.SetSizeHints(self.GetParent())
        self.SetAutoLayout(True)
        self.SetSizer(self.wrapper)
        self.Layout()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.config_arterial.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)
        self.config_venous.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def on_pane_changed(self, evt):
        self.sizer.Layout()
        self.Layout()

    def OnClose(self, evt):
        for panel in self.panels:
            panel.Close()


class BaseGasMixerPanel(wx.Panel):
    def __init__(self, parent, autogasmixer):
        super().__init__(parent)
        self.name = autogasmixer.name
        self._lgr = utils.get_object_logger(__name__, self.name)

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

        self.static_box = wx.StaticBox(self, wx.ID_ANY, label=self.name)
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        # Adjustable parameters
        self.text_flow_adjust = wx.TextCtrl(self, value='Total (mL/min):')
        self.spin_flow_adjust = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400,
                                                  initial=int(self.autogasmixer.gas_device.get_total_flow()), inc=1)
        self.text_flow_adjust.SetFont(font)
        self.spin_flow_adjust.SetFont(font)

        self.slider_mix = wx.Slider(self, value=0, minValue=0, maxValue=100, style=wx.SL_INVERSE | wx.SL_VALUE_LABEL)

        self.label_gas1 = wx.StaticText(self, label=f'{self.gas1_name}', style=wx.ALIGN_LEFT)
        self.label_gas2 = wx.StaticText(self, label=f'{self.gas2_name}', style=wx.ALIGN_RIGHT)
        self.label_gas1.SetFont(font)
        self.label_gas2.SetFont(font)

        self.label_gas1_mix = wx.StaticText(self, label=f'0 %', style=wx.ALIGN_LEFT)
        self.label_gas2_mix = wx.StaticText(self, label=f'0 %', style=wx.ALIGN_RIGHT)
        self.label_gas1_flow = wx.StaticText(self, label=f'ml/min', style=wx.ALIGN_LEFT)
        self.label_gas2_flow = wx.StaticText(self, label=f'ml/min', style=wx.ALIGN_RIGHT)

        # Buttons for functionality
        self.btn_flow = wx.ToggleButton(self, label='Enable Flow')
        self.btn_update = wx.Button(self, label='Update')
        self.chk_auto = wx.CheckBox(self, label='Auto Adjust based on CDI')

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Proportion(1)

        sizerH = wx.BoxSizer(wx.HORIZONTAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_gas1, flags)
        sizer.Add(self.label_gas1_flow, flags)
        sizer.Add(self.label_gas1_mix, flags)

        sizerH.Add(sizer, flags.Proportion(1))

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizerf = wx.BoxSizer(wx.HORIZONTAL)
        sizerf.Add(self.text_flow_adjust, flags)
        sizerf.Add(self.spin_flow_adjust, flags)
        sizer.Add(sizerf, wx.SizerFlags().Center())

        sizer.AddSpacer(1)
        sizer.Add(self.slider_mix, flags)
        sizerH.Add(sizer, wx.SizerFlags().Proportion(3))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_gas2, flags)
        sizer.Add(self.label_gas2_flow, flags)
        sizer.Add(self.label_gas2_mix, flags)

        sizerH.Add(sizer, flags.Proportion(1))
        self.sizer.Add(sizerH, flags.Proportion(4))

        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        sizerH.Add(self.btn_update, flags)
        sizerH.Add(self.btn_flow, flags)
        self.sizer.Add(sizerH)

        self.sizer.Add(self.chk_auto, flags)
        self.sizer.AddSpacer(1)

        self.sizer.SetSizeHints(self.GetParent())

        # self.sizer.Add(self.sizer_cfg, flags)

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
        self.Bind(wx.EVT_CHECKBOX, self.OnAuto)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def update_controls(self):
        gas1_mix_set = self.autogasmixer.gas_device.percent[0]
        gas2_mix_set = self.autogasmixer.gas_device.percent[1]
        gas1_flow_set = self.autogasmixer.gas_device.total_flow * (gas1_mix_set / 100.0)
        gas2_flow_set =  self.autogasmixer.gas_device.total_flow * (gas2_mix_set / 100.0)
        gas1_mix_actual = self.autogasmixer.gas_device.get_percent_value(1)
        gas2_mix_actual = self.autogasmixer.gas_device.get_percent_value(2)
        gas1_flow_actual = self.autogasmixer.gas_device.get_target_sccm(1)
        gas2_flow_actual = self.autogasmixer.gas_device.get_target_sccm(2)

        self.label_gas1_mix.SetLabel(f'{gas1_mix_actual} %')
        self.label_gas2_mix.SetLabel(f'{gas2_mix_actual} %')
        self.label_gas1_flow.SetLabel(f'{gas1_flow_actual} ml/min')
        self.label_gas2_flow.SetLabel(f'{gas2_flow_actual} ml/min')

        self.warn_on_difference(self.label_gas1_mix, gas1_mix_actual, gas1_mix_set)
        self.warn_on_difference(self.label_gas2_mix, gas2_mix_actual, gas2_mix_set)
        self.warn_on_difference(self.label_gas1_flow, gas1_flow_actual, gas1_flow_set)
        self.warn_on_difference(self.label_gas2_flow, gas2_flow_actual, gas2_flow_set)

    def warn_on_difference(self, ctrl, actual, set_value):
        color = self.normal_color
        tooltip_msg = ''

        if not np.isclose(actual, set_value):
            color = self.warning_color
            tooltip_msg = f'Expected {set_value}'
        ctrl.SetBackgroundColour(color)
        ctrl.SetToolTip(tooltip_msg)
        ctrl.Refresh()

    def _update_manual_entries(self):
        self.spin_flow_adjust.SetValue(f'{self.autogasmixer.gas_device.get_total_flow()}')
        self.slider_mix.SetValue(int(self.autogasmixer.gas_device.get_percent_value(1)))

    def OnAuto(self, evt):
        if not self.chk_auto.IsChecked():
            self._update_manual_entries()
            self.autogasmixer.stop()
        else:
            self.autogasmixer.start()
        self.slider_mix.Enable(not self.chk_auto.IsChecked())
        self.spin_flow_adjust.Enable(not self.chk_auto.IsChecked())

    def OnFlow(self, evt):
        working_status = self.autogasmixer.gas_device.get_working_status()
        if working_status == 0:  # 0 is off
            self.autogasmixer.gas_device.set_working_status(turn_on=True)
            if self.chk_auto.IsChecked():
                self.autogasmixer.start()
            else:
                self._update_manual_entries()
        else:
            self.autogasmixer.gas_device.set_working_status(turn_on=False)
            self.autogasmixer.stop()

    def OnChangeFlow(self, evt):
        self.btn_update.Enable(True)
        self.spin_flow_adjust.SetBackgroundColour(wx.RED)

    def OnChangeGas(self, evt):
        self.btn_update.Enable(True)
        self.slider_mix.SetBackgroundColour(wx.RED)

    def OnUpdate(self, evt):
        self.autogasmixer.gas_device.set_percent_value(2, 100 - float(self.slider_mix.GetValue()))
        self.autogasmixer.gas_device.set_total_flow(int(self.spin_flow_adjust.GetValue()))
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
