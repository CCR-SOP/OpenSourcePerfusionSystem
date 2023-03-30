# -*- coding: utf-8 -*-
""" Application to display gas mixer controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor
from pyPerfusion.pyCDI import CDIData
from pyPerfusion.pyAutoGasMixer import AutoGasMixerVenous, AutoGasMixerArterial


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, ha_gasmixer, pv_gasmixer, cdi_reader):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.cdi_reader = cdi_reader
        self.ha_autogasmixer = ha_gasmixer
        self.pv_autogasmixer = pv_gasmixer
        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', autogasmixer=ha_gasmixer, cdi_reader=self.cdi_reader)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', autogasmixer=pv_gasmixer, cdi_reader=self.cdi_reader)
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Gas Mixers")
        self.wrapper = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()
        self.sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=1, hgap=1)

        self.sizer.Add(self._panel_HA, flags)
        self.sizer.Add(self._panel_PV, flags)

        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)

        self.sizer.SetSizeHints(self.parent)
        self.wrapper.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=2)
        self.SetSizer(self.wrapper)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        self._panel_PV.Close()
        self._panel_HA.Close()


class BaseGasMixerPanel(wx.Panel):
    def __init__(self, parent, name, autogasmixer, cdi_reader, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self._lgr = logging.getLogger(__name__)

        self.parent = parent
        self.name = name
        self.autogasmixer = autogasmixer
        self.cdi_reader = cdi_reader

        if self.autogasmixer.gas_device is not None:
            # TODO we should verify the gas mixer is configured
            # for the gases we want (O2, CO2)
            self.gas1_name = self.autogasmixer.gas_device.get_gas_type(1)
            self.gas2_name = self.autogasmixer.gas_device.get_gas_type(2)

        font = wx.Font()
        font.SetPointSize(int(12))

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)


        self.label_total_flow = wx.StaticText(self, label='Total gas flow (mL/min):')
        self.input_total_flow = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400, initial=0, inc=1)
        self.label_total_flow.SetFont(font)
        self.input_total_flow.SetFont(font)

        self.label_real_total_flow = wx.StaticText(self, label='Actual total gas flow (mL/min):')
        self.real_total_flow = wx.TextCtrl(self, style=wx.TE_READONLY, value='0')

        # Gas 1 display
        self.label_gas1 = wx.StaticText(self, label=f'{self.gas1_name} % Mix:')
        self.input_percent_gas1 = wx.SpinCtrlDouble(self, wx.ID_ANY | wx.EXPAND, min=0, max=100, initial=0, inc=1)
        self.label_gas1.SetFont(font)
        self.input_percent_gas1.SetFont(font)

        self.label_real_gas1 = wx.StaticText(self, label=f'Actual {self.gas1_name} % Mix:')
        self.percent_real_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY, value='0')
        self.label_flow_gas1 = wx.StaticText(self, label=f'{self.gas1_name} actual flow (mL/min):')
        self.flow_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.label_target_flow_gas1 = wx.StaticText(self, label=f'{self.gas1_name} target flow (mL/min):')
        self.target_flow_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY)

        # Gas 2 display
        self.label_gas2 = wx.StaticText(self, label=f'{self.gas2_name} % Mix:')
        self.percent_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.label_flow_gas2 = wx.StaticText(self, label=f'{self.gas2_name} actual flow (mL/min):')
        self.flow_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.label_target_flow_gas2 = wx.StaticText(self, label=f'{self.gas2_name} target flow (mL/min):')
        self.target_flow_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY)

        # Buttons for functionality
        self.btn_flow = wx.ToggleButton(self, label='Enable Flow')
        self.btn_update = wx.Button(self, label='Update')
        self.chk_auto = wx.CheckBox(self, label='Auto Adjust based on CDI')

        self.timer_gui_update = wx.Timer(self)
        self.timer_gui_update.Start(milliseconds=500, oneShot=wx.TIMER_CONTINUOUS)

        self.sync_with_hw_timer = wx.Timer(self)
        self.sync_with_hw_timer.Start(1_200_000, wx.TIMER_CONTINUOUS)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 2).Center()
        sizer_cfg = wx.FlexGridSizer(cols=2)

        sizer_cfg.Add(self.label_total_flow, flags)
        sizer_cfg.Add(self.input_total_flow, flags)

        sizer_cfg.Add(self.label_gas1, flags)
        sizer_cfg.Add(self.input_percent_gas1, flags)

        sizer_cfg.Add(self.label_real_total_flow, flags)
        sizer_cfg.Add(self.real_total_flow, flags)

        sizer_cfg.Add(self.label_real_gas1, flags)
        sizer_cfg.Add(self.percent_real_gas1, flags)
        sizer_cfg.Add(self.label_target_flow_gas1, flags)
        sizer_cfg.Add(self.target_flow_gas1, flags)
        sizer_cfg.Add(self.label_flow_gas1, flags)
        sizer_cfg.Add(self.flow_gas1, flags)

        sizer_cfg.Add(self.label_gas2, flags)
        sizer_cfg.Add(self.percent_gas2, flags)
        sizer_cfg.Add(self.label_target_flow_gas2, flags)
        sizer_cfg.Add(self.target_flow_gas2, flags)
        sizer_cfg.Add(self.label_flow_gas2, flags)
        sizer_cfg.Add(self.flow_gas2, flags)

        sizer_cfg.Add(self.btn_update, flags)
        sizer_cfg.Add(self.btn_flow, flags)

        sizer_cfg.Add(self.chk_auto, flags)
        sizer_cfg.AddSpacer(1)

        sizer_cfg.AddGrowableCol(0, 2)
        sizer_cfg.AddGrowableCol(1, 1)

        self.sizer.Add(sizer_cfg, proportion=1, flag=wx.ALL | wx.EXPAND, border=1)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_flow.Bind(wx.EVT_TOGGLEBUTTON, self.OnFlow)
        self.btn_update.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.input_total_flow.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeFlow)
        self.input_total_flow.Bind(wx.EVT_TEXT, self.OnChangeFlow)
        self.input_percent_gas1.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeGas)
        self.input_percent_gas1.Bind(wx.EVT_TEXT, self.OnChangeGas)
        self.chk_auto.Bind(wx.EVT_CHECKBOX, self.OnAuto)
        self.Bind(wx.EVT_TIMER, self.update_controls_from_hardware, self.timer_gui_update)
        self.Bind(wx.EVT_TIMER, self.CheckHardwareForAccuracy, self.sync_with_hw_timer)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def OnFlow(self, evt):
        working_status = self.autogasmixer.gas_device.get_working_status()

        self.btn_update.Enable(False)
        if working_status == 0:  # 0 is off
            self.autogasmixer.gas_device.set_working_status(turn_on=True)
            self.btn_flow.SetLabel('Disable Flow')
        else:
            self.autogasmixer.gas_device.set_working_status(turn_on=False)
            self.btn_flow.SetLabel('Enable Flow')

    def OnChangeFlow(self, evt):
        self.btn_update.Enable(True)
        self.input_total_flow.SetBackgroundColour(wx.RED)

    def OnChangeGas(self, evt):
        self.btn_update.Enable(True)
        self.input_percent_gas1.SetBackgroundColour(wx.RED)

    def OnUpdate(self, evt):
        self.autogasmixer.gas_device.set_total_flow(int(self.input_total_flow.GetValue()))
        self.input_total_flow.SetBackgroundColour(wx.WHITE)
        self.input_total_flow.Refresh()
        self.autogasmixer.gas_device.set_percent_value(2, 100 - float(self.input_percent_gas1.GetValue()))
        self.input_percent_gas1.SetBackgroundColour(wx.WHITE)
        self.input_percent_gas1.Refresh()

    def OnAuto(self, evt):
        if evt.IsChecked():
            self.autogasmixer.start()
        else:
            self.autogasmixer.stop()

    def update_controls_from_hardware(self, evt):
        self.real_total_flow.SetValue(f'{self.autogasmixer.gas_device.get_total_flow()}')

        self.flow_gas1.SetValue(f'{self.autogasmixer.gas_device.get_sccm_av(1)}')
        self.flow_gas2.SetValue(f'{self.autogasmixer.gas_device.get_sccm_av(2)}')

        self.target_flow_gas1.SetValue(f'{self.autogasmixer.gas_device.get_target_sccm(1)}')
        self.target_flow_gas1.SetValue(f'{self.autogasmixer.gas_device.get_target_sccm(2)}')

        self.target_flow_gas1.SetValue(f'{self.autogasmixer.gas_device.get_target_sccm(1)}')
        self.target_flow_gas2.SetValue(f'{self.autogasmixer.gas_device.get_target_sccm(2)}')

        update_allowed = not self.chk_auto.IsChecked() and self.autogasmixer.gas_device.get_working_status()
        self.btn_update.Enable(update_allowed)
        self.input_percent_gas1.Enable(update_allowed)
        self.input_total_flow.Enable(update_allowed)



    def UpdateApp(self, new_perc=None):
        if new_perc is not None:
            self.percent_real_gas1.SetValue(str(new_perc))
            gas2_mix_perc = str(100 - new_perc)
            self.percent_gas2.SetValue(gas2_mix_perc)

    def EnableButtons(self):
        if not self.automatic_start_btn.IsEnabled() and not self.manual_start_btn.IsEnabled():  # starting condition
            self.manual_start_btn.Enable()
            self.automatic_start_btn.Enable()

    def EnsureTurnedOn(self):
        if self.autogasmixer.gas_device.get_working_status() == 0:
            self.autogasmixer.gas_device.set_working_status(turn_on=True)

    def CheckHardwareForAccuracy(self, evt):
        if evt.GetId() == self.sync_with_hw_timer.GetId():
            # Update actual flows
            target_flows = [0] * 2
            target_flows[0] = self.autogasmixer.gas_device.get_target_sccm(1)
            target_flows[1] = self.autogasmixer.gas_device.get_target_sccm(2)
            actual_flows = [0] * 2
            actual_flows[0] = self.autogasmixer.gas_device.get_sccm_av(1)
            actual_flows[1] = self.autogasmixer.gas_device.get_sccm_av(2)

            for x in range(2):
                tolerance = [target_flows[x]*0.95, target_flows[x]*1.05]
                if not tolerance[0] <= actual_flows[x] <= tolerance[1]:
                    wx.MessageBox(f'Actual flow of {self.autogasmixer.gas_device.channel_type} mixer, channel {x+1} not within '
                                  f'5% of target flow. Check gas tank flow')  # make a Lgr.warning

            if not self.input_percent_gas1.GetValue() == self.autogasmixer.gas_device.get_percent_value(1):
                self.UpdateApp(self.autogasmixer.gas_device.get_percent_value(1))

            if not self.input_total_flow.GetValue() == self.autogasmixer.gas_device.get_total_flow():
                self.UpdateApp()

    def on_close(self, evt):
        self.timer_gui_update.Stop()
        self.sync_with_hw_timer.Stop()
        self.autogasmixer.gas_device.set_working_status(turn_on=False)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self, ha_autogasmixer, pv_autogasmixer, cdi_reader=cdi_sensor.get_reader())
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.Close()
        cdi_sensor.stop()
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
    utils.setup_file_logger(logging.getLogger(), logging.DEBUG, 'panel_gas_mixers_debug')

    SYS_HW.load_hardware_from_config()
    ha_mixer = SYS_HW.get_hw('Arterial Gas Mixer')
    pv_mixer = SYS_HW.get_hw('Venous Gas Mixer')

    # Load CDI sensor
    cdi_sensor = Sensor(name='CDI')
    cdi_sensor.read_config()
    cdi_sensor.start()

    ha_autogasmixer = AutoGasMixerArterial(name='HA Auto Gas Mixer', gas_device=ha_mixer, cdi_reader=cdi_sensor.get_reader())
    pv_autogasmixer = AutoGasMixerVenous(name='PV Auto Gas Mixer', gas_device=pv_mixer, cdi_reader=cdi_sensor.get_reader())

    app = MyTestApp(0)
    app.MainLoop()
