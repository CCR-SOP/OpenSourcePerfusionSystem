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

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
utils.configure_matplotlib_logging()


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, HA_mixer, PV_mixer, cdi):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.cdi_sensor = cdi

        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', gas_device=HA_mixer, cdi=self.cdi_sensor)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', gas_device=PV_mixer, cdi=self.cdi_sensor)
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
        pass


class BaseGasMixerPanel(wx.Panel):
    def __init__(self, parent, name, gas_device, cdi, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        self._lgr = logging.getLogger(__name__)

        self.parent = parent
        self.name = name
        self.gas_device = gas_device
        self.cdi_sensor = cdi
        if self.gas_device is not None:
            self.gas1 = self.gas_device.get_gas_type(1)
            self.gas2 = self.gas_device.get_gas_type(2)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        font = wx.Font()
        font.SetPointSize(int(12))

        # Pull initial total flow and create display
        total_flow = self.gas_device.get_total_flow()
        self.label_total_flow = wx.StaticText(self, label='Total gas flow (mL/min):')
        self.input_total_flow = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400, initial=total_flow, inc=1)
        self.label_total_flow.SetFont(font)
        self.input_total_flow.SetFont(font)

        self.label_real_total_flow = wx.StaticText(self, label='Actual total gas flow (mL/min):')
        self.real_total_flow = wx.TextCtrl(self, style=wx.TE_READONLY, value=str(total_flow))

        # Pull initial gas mix percentages and flow rates
        channel_nr = 1  # always just change the first channel and the rest will follow
        gas1_mix_perc = self.gas_device.get_percent_value(channel_nr)
        gas2_mix_perc = str(100 - gas1_mix_perc)
        gas1_flow = str(self.gas_device.get_sccm(1))
        gas2_flow = str(self.gas_device.get_sccm(2))
        gas1_target_flow = str(self.gas_device.get_target_sccm(1))
        gas2_target_flow = str(self.gas_device.get_target_sccm(2))

        # Gas 1 display
        self.label_gas1 = wx.StaticText(self, label=f'{self.gas1} % Mix:')
        self.input_percent_gas1 = wx.SpinCtrlDouble(self, wx.ID_ANY | wx.EXPAND, min=0, max=100, initial=gas1_mix_perc, inc=1)
        self.label_gas1.SetFont(font)
        self.input_percent_gas1.SetFont(font)

        self.label_real_gas1 = wx.StaticText(self, label=f'Actual {self.gas1} % Mix:')  # in case someone changes hardware, or runs auto
        self.percent_real_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY, value=str(gas1_mix_perc))
        self.label_flow_gas1 = wx.StaticText(self, label=f'{self.gas1} actual flow (mL/min):')
        self.flow_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas1_flow)
        self.label_target_flow_gas1 = wx.StaticText(self, label=f'{self.gas1} target flow (mL/min):')
        self.target_flow_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas1_target_flow)

        # Gas 2 display
        self.label_gas2 = wx.StaticText(self, label=f'{self.gas2} % Mix:')
        self.percent_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas2_mix_perc)
        self.label_flow_gas2 = wx.StaticText(self, label=f'{self.gas2} actual flow (mL/min):')
        self.flow_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas2_flow)
        self.label_target_flow_gas2 = wx.StaticText(self, label=f'{self.gas2} target flow (mL/min):')
        self.target_flow_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas2_target_flow)

        # Buttons for functionality
        self.update_total_flow_btn = wx.Button(self, label='Update Total Gas Flow')
        self.update_gas1_perc_btn = wx.Button(self, label='Update Gas % Mix')
        self.manual_start_btn = wx.ToggleButton(self, label='Start Manual')
        self.automatic_start_btn = wx.ToggleButton(self, label='Start Automatic')
        self.update_total_flow_btn.SetFont(font)
        self.update_gas1_perc_btn.SetFont(font)
        self.manual_start_btn.SetFont(font)
        self.automatic_start_btn.SetFont(font)
        self.manual_start_btn.Disable()
        self.automatic_start_btn.Disable()

        self.sync_with_hw_timer = wx.Timer(self)
        self.sync_with_hw_timer.Start(1_200_000, wx.TIMER_CONTINUOUS)

        self.cdi_timer = wx.Timer(self)

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

        sizer_cfg.Add(self.update_total_flow_btn, flags)
        sizer_cfg.Add(self.update_gas1_perc_btn, flags)
        sizer_cfg.Add(self.manual_start_btn, flags)
        sizer_cfg.Add(self.automatic_start_btn, flags)

        sizer_cfg.AddGrowableCol(0, 2)
        sizer_cfg.AddGrowableCol(1, 1)

        self.sizer.Add(sizer_cfg, proportion=1, flag=wx.ALL | wx.EXPAND, border=1)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.manual_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnManualStart)
        self.automatic_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnAutoStart)
        self.update_gas1_perc_btn.Bind(wx.EVT_BUTTON, self.OnChangePercentMix)
        self.update_total_flow_btn.Bind(wx.EVT_BUTTON, self.OnChangeTotalFlow)
        self.Bind(wx.EVT_TIMER, self.CheckHardwareForAccuracy, self.sync_with_hw_timer)
        self.Bind(wx.EVT_TIMER, self.readDataFromCDI, self.cdi_timer)

    def OnManualStart(self, evt):
        working_status = self.gas_device.get_working_status()

        if working_status == 0:  # 0 is off
            self.gas_device.set_working_status(turn_on=True)
            self.manual_start_btn.SetLabel('Stop Manual')
            self.automatic_start_btn.Disable()
        else:
            self.gas_device.set_working_status(turn_on=False)
            self.manual_start_btn.SetLabel('Start Manual')
            self.automatic_start_btn.Enable()

        time.sleep(3.0)
        self.UpdateApp()

    def OnAutoStart(self, evt):
        working_status = self.gas_device.get_working_status()

        if working_status == 0:  # 0 is off
            self.gas_device.set_working_status(turn_on=True)
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.manual_start_btn.Disable()
            self.cdi_timer.Start(10_000, wx.TIMER_CONTINUOUS)
            self._lgr.debug(f'CDI timer starting')
            self.cdi_sensor.hw.start()
            self.cdi_sensor.start()
        else:
            self.gas_device.set_working_status(turn_on=False)
            self.automatic_start_btn.SetLabel('Start Automatic')
            self.manual_start_btn.Enable()
            self.cdi_timer.Stop()
            self.cdi_sensor.stop()

        time.sleep(3.0)
        self.UpdateApp()
    
    def readDataFromCDI(self, evt):
        if evt.GetId() == self.cdi_timer.GetId():
            self._lgr.debug(f'CDI Timer going off!')
            cdi_reader = self.cdi_sensor.get_reader()
            ts, all_vars = cdi_reader.get_last_acq()
            cdi_data = CDIData(all_vars)
            if cdi_data is not None:
                if self.gas_device.name == "Venous Gas Mixer":  # channel_type == "PV":
                    new_flow = self.update_pH(cdi_data)
                    new_mix_perc_pv = self.update_O2(cdi_data)
                    if new_flow is not None:
                        self.UpdateApp()
                    if new_mix_perc_pv is not None:
                        self.UpdateApp(new_mix_perc_pv)
                elif self.gas_device.name == "Arterial Gas Mixer":  # channel_type == "HA":
                    new_mix_perc_ha = self.update_CO2(cdi_data)
                    if new_mix_perc_ha is not None:
                        self.UpdateApp(100 - new_mix_perc_ha)
            else:
                self._lgr.debug(f'No CDI data. Cannot run gas mixers automatically')

            if self.automatic_start_btn.GetLabel() == "Stop Automatic":
                self.EnsureTurnedOn()
                time.sleep(1.0)

    def OnChangePercentMix(self, evt):
        new_percent = self.input_percent_gas1.GetValue()
        self.gas_device.set_percent_value(2, 100 - new_percent)  # set channel 2 only
        time.sleep(2.0)

        if self.manual_start_btn.GetLabel() == "Stop Manual":  # prevents turning on if user hasn't hit start
            self.EnsureTurnedOn()
            time.sleep(1.0)

        self.UpdateApp(new_percent)

    def OnChangeTotalFlow(self, evt):
        new_total_flow = self.input_total_flow.GetValue()
        self.gas_device.set_total_flow(new_total_flow)

        if self.manual_start_btn.GetLabel() == "Stop Manual":
            self.EnsureTurnedOn()
            time.sleep(1.0)

        self.UpdateApp()

    def UpdateApp(self, new_perc=None):
        if new_perc is not None:
            self.percent_real_gas1.SetValue(str(new_perc))
            gas2_mix_perc = str(100 - new_perc)
            self.percent_gas2.SetValue(gas2_mix_perc)

        total_gas_flow = str(self.gas_device.get_total_flow())
        self.real_total_flow.SetValue(total_gas_flow)

        gas1_flow = str(self.gas_device.get_sccm_av(1))
        gas2_flow = str(self.gas_device.get_sccm_av(2))
        self.flow_gas1.SetValue(gas1_flow)
        self.flow_gas2.SetValue(gas2_flow)

        gas1_target_flow = str(self.gas_device.get_target_sccm(1))
        gas2_target_flow = str(self.gas_device.get_target_sccm(2))
        self.target_flow_gas1.SetValue(gas1_target_flow)
        self.target_flow_gas2.SetValue(gas2_target_flow)

        self.EnableButtons()

    def EnableButtons(self):
        if not self.automatic_start_btn.IsEnabled() and not self.manual_start_btn.IsEnabled():  # starting condition
            self.manual_start_btn.Enable()
            self.automatic_start_btn.Enable()

    def EnsureTurnedOn(self):
        if self.gas_device.get_working_status() == 0:
            self.gas_device.set_working_status(turn_on=True)

    def CheckHardwareForAccuracy(self, evt):
        if evt.GetId() == self.sync_with_hw_timer.GetId():
            # Update actual flows
            target_flows = [0] * 2
            target_flows[0] = self.gas_device.get_target_sccm(1)
            target_flows[1] = self.gas_device.get_target_sccm(2)
            actual_flows = [0] * 2
            actual_flows[0] = self.gas_device.get_sccm_av(1)
            actual_flows[1] = self.gas_device.get_sccm_av(2)

            for x in range(2):
                tolerance = [target_flows[x]*0.95, target_flows[x]*1.05]
                if not tolerance[0] <= actual_flows[x] <= tolerance[1]:
                    wx.MessageBox(f'Actual flow of {self.gas_device.channel_type} mixer, channel {x+1} not within '
                                  f'5% of target flow. Check gas tank flow')  # make a Lgr.warning
                    self.UpdateApp()

            if not self.input_percent_gas1.GetValue() == self.gas_device.get_percent_value(1):
                self.UpdateApp(self.gas_device.get_percent_value(1))

            if not self.input_total_flow.GetValue() == self.gas_device.get_total_flow():
                self.UpdateApp()

    def update_pH(self, CDI_input):
        total_flow = self.gas_device.get_total_flow()
        if 5 <= total_flow <= 250:
            if CDI_input.venous_pH == -1:
                self._lgr.warning(f'Venous pH is out of range. Cannot be adjusted automatically')
                return None
            elif CDI_input.venous_pH < self.gas_device.pH_range[0]:
                new_flow = total_flow + 5  # TODO: do not hard code
                self.gas_device.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV increased to {new_flow}')
                return new_flow
            elif CDI_input.venous_pH > self.gas_device.pH_range[1]:
                new_flow = total_flow - 5
                self.gas_device.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV decreased to {new_flow}')
                return new_flow
        elif total_flow >= 250:
            self._lgr.warning(f'Total flow in PV at or above 250 mL/min. Cannot be run automatically')
            return None
        elif total_flow <= 5:
            self._lgr.warning(f'Total flow in portal vein at or below 5 mL/min. Cannot be run automatically')
            return None
        else:
            return None

    def update_CO2(self, CDI_input):
        new_percentage_mix = None

        gas = self.gas_device.get_gas_type(2)
        if gas == "Carbon Dioxide":  # assumes 2-channel gas mixer with Carbon Dioxide as one of the options
            gas_index = 2
        else:
            gas_index = 1

        percentage_mix = self.gas_device.get_percent_value(gas_index)
        if 0 <= percentage_mix <= 100:
            if CDI_input.arterial_pH == -1:
                self._lgr.warning(f'Arterial pH is out of range. Cannot be adjusted automatically')
            elif CDI_input.arterial_CO2 == -1:
                self._lgr.warning(f'Arterial CO2 is out of range. Cannot be adjusted automatically')
            elif CDI_input.arterial_pH > self.gas_device.pH_range[1] or CDI_input.arterial_CO2 < self.gas_device.CO2_range[0]:
                new_percentage_mix = percentage_mix + 1  # TODO: not hard code
                self._lgr.warning(f'CO2 low, blood alkalotic')
            elif CDI_input.arterial_pH < self.gas_device.pH_range[0] or CDI_input.arterial_CO2 > self.gas_device.CO2_range[1]:
                new_percentage_mix = percentage_mix - 1  # to do: not hard code
                self._lgr.warning(f'CO2 high, blood acidotic')
        else:
            self._lgr.warning(f'CO2 % is out of range and cannot be changed automatically')

        return new_percentage_mix

    def update_O2(self, CDI_input):
        new_percentage_mix = None

        gas = self.gas_device.get_gas_type(1)
        if gas == "Oxygen":  # assumes 2-channel gas mixer with Oxygen as one of the options
            gas_index = 1
        else:
            gas_index = 2

        percentage_mix = self.gas_device.get_percent_value(gas_index)
        if 0 <= percentage_mix <= 100:
            if CDI_input.venous_O2 == -1:
                self._lgr.warning(f'Venous O2 is out of range. Cannot be adjusted automatically')
            elif CDI_input.venous_O2 < self.gas_device.O2_range[0]:
                new_percentage_mix = percentage_mix + 2  # TODO: not hard code
                self._lgr.warning(f'Venous O2 is low')
            elif CDI_input.venous_O2 > self.gas_device.O2_range[1]:
                new_percentage_mix = percentage_mix - 2
                self._lgr.warning(f'Venous O2 is high')
        else:
            self._lgr.warning(f'O2 % is out of range and cannot be changed automatically')

        return new_percentage_mix


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self, ha_mixer, pv_mixer, cdi=cdi_sensor)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        self.panel.cdi_sensor.stop()
        self.Destroy()
        self.panel._panel_HA.sync_with_hw_timer.Stop()
        self.panel._panel_PV.sync_with_hw_timer.Stop()
        self.panel._panel_HA.cdi_timer.Stop()
        self.panel._panel_PV.cdi_timer.Stop()
        self.panel._panel_HA.gas_device.set_working_status(turn_on=False)
        self.panel._panel_PV.gas_device.set_working_status(turn_on=False)

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)

    SYS_HW.load_hardware_from_config()
    ha_mixer = SYS_HW.get_hw('Arterial Gas Mixer')
    pv_mixer = SYS_HW.get_hw('Venous Gas Mixer')

    # Load CDI sensor
    cdi_sensor = Sensor(name='CDI')
    cdi_sensor.read_config()

    app = MyTestApp(0)
    app.MainLoop()
