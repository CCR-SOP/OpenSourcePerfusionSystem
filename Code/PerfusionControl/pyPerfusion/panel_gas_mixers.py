# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import serial

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils

from pyPerfusion.pyGB100_SL import GasControl, GasDevice
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
import time


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, gas_controller, cdi_output):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.cdi = cdi_output
        self.gas_control = gas_controller
        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', gas_device=gas_control.HA, cdi_output=self.cdi)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', gas_device=gas_control.PV, cdi_output=self.cdi)
        static_box = wx.StaticBox(self, wx.ID_ANY, label="Gas Mixers")
        self.sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand().Border()

        self.sizer.Add(self._panel_HA, flags.Proportion(2))
        self.sizer.Add(self._panel_PV, flags.Proportion(2))

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        pass


class BaseGasMixerPanel(wx.Panel):
    def __init__(self, parent, name, gas_device: GasDevice, cdi_output, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE

        self.parent = parent
        self.name = name
        self.gas_device = gas_device
        self.cdi = cdi_output
        if self.gas_device is not None:
            self.gas1 = self.gas_device.get_gas_type(1)
            self.gas2 = self.gas_device.get_gas_type(2)

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        # Pull initial total flow and create display
        total_flow = self.gas_device.get_total_flow()
        self.label_total_flow = wx.StaticText(self, label='Total gas flow (mL/min):')
        self.input_total_flow = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400, initial=total_flow, inc=1)

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
        self.manual_start_btn.Disable()
        self.automatic_start_btn.Disable()

        self.__do_layout()
        self.__set_bindings()

        self.timer = wx.Timer(self)
        self.timer.Start(30_000, wx.TIMER_CONTINUOUS)

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=2)

        sizer_cfg.Add(self.label_total_flow, flags)
        sizer_cfg.Add(self.input_total_flow, flags)

        sizer_cfg.Add(self.label_gas1, flags)
        sizer_cfg.Add(self.input_percent_gas1, flags)

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

        self.sizer.Add(sizer_cfg)

        self.sizer.SetSizeHints(self.parent)
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.manual_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnManualStart)
        self.automatic_start_btn.Bind(wx.EVT_TOGGLEBUTTON, self.OnAutoStart)
        self.update_gas1_perc_btn.Bind(wx.EVT_BUTTON, self.OnChangePercentMix)
        self.update_total_flow_btn.Bind(wx.EVT_BUTTON, self.OnChangeTotalFlow)
        self.Bind(wx.EVT_TIMER, self.CheckHardwareForAccuracy)

    def OnManualStart(self, evt):
        self.automatic_start_btn.Disable()
        working_status = self.gas_device.get_working_status()

        if working_status == 0:  # 0 is off
            self.gas_device.set_working_status(turn_on=True)
            self.manual_start_btn.SetLabel('Stop Manual')
        else:
            self.gas_device.set_working_status(turn_on=False)
            self.manual_start_btn.SetLabel('Start Manual')
            self.automatic_start_btn.Enable()

        time.sleep(4.0)
        self.UpdateApp()

    def OnAutoStart(self, evt):  # NOT READY FOR USE
        self.manual_start_btn.Disable()
        GB100_working_status = self.gas_device.get_working_status()

        if GB100_working_status == 0:
            self.gas_device.set_working_status(turn_on=True)
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.gas_device.update_pH(self.cdi)
            self.gas_device.update_CO2(self.cdi)
            self.gas_device.update_O2(self.cdi)
            # loop through on a timer
            new_perc = 1  # need real value as output from CDI methods
            self.UpdateApp(new_perc)
        else:
            self.automatic_start_btn.SetLabel('Start Automatic')
            self.cdi.stop()
            self.manual_start_btn.Enable()

    def OnChangePercentMix(self, evt):
        new_percent = self.input_percent_gas1.GetValue()

        # Update gas mixer percentages
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
            gas2_mix_perc = str(100 - new_perc)
            self.percent_gas2.SetValue(gas2_mix_perc)

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
        if evt.GetId() == self.timer.GetId():
            # Update actual flows
            target_flows = [0] * 2
            target_flows[0] = self.gas_device.get_target_sccm(1)
            target_flows[1] = self.gas_device.get_target_sccm(2)
            actual_flows = [0] * 2
            actual_flows[0] = self.gas_device.get_sccm_av(1)
            actual_flows[1] = self.gas_device.get_sccm_av(2)

            for x in range(2):  # this is running 3x every time?? Not sure why
                tolerance = [target_flows[x]*0.95, target_flows[x]*1.05]
                if not tolerance[0] <= actual_flows[x] <= tolerance[1]:
                    self.gas_device._lgr.debug(f'{x}')
                    self.gas_device._lgr.warning(f'Actual flow of {self.gas_device.channel_type} not within 5% of target flow. Check gas tank flow')
                    self.UpdateApp()

            if not self.input_percent_gas1.GetValue() == self.gas_device.get_percent_value(1):
                self.gas_device._lgr.warning(f'Please update gas 1 mix % on application to match hardware')

            if not self.input_total_flow.GetValue() == self.gas_device.get_total_flow():
                self.gas_device._lgr.warning(f'Please update total flow on application to match hardware')


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self, gas_control, read_from_cdi)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        # cdi.stop()
        # stream_cdi_to_file.stop()

        self.Destroy()
        # destroy timer??


class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)

    gas_control = GasControl()

    cdi = pyCDI.CDIStreaming('CDI')
    # cdi.read_config()  # need updated pyCDI and SensorPoint for this to work
    # stream_cdi_to_file = SensorPoint(cdi, 'NA')
    # stream_cdi_to_file.add_strategy(strategy=MultiVarToFile('write', 1, 17))
    # ro_sensor = ReadOnlySensorPoint(cdi, 'na')
    read_from_cdi = [1] * 18  # MultiVarFromFile('multi_var', 1, 17, 1)
    # ro_sensor.add_strategy(strategy=read_from_cdi)

    # stream_cdi_to_file.start()
    # cdi.start()

    app = MyTestApp(0)
    app.MainLoop()
