# -*- coding: utf-8 -*-
""" Application to display dialysis pump controls

@project: LiverPerfusion NIH
@author: Stephie Lux, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import wx

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import mcqlib_GB100.mcqlib.main as mcq
from pyPerfusion.pyGB100_SL import GB100
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.SensorPoint import SensorPoint
from pyPerfusion.FileStrategy import MultiVarToFile
import time


class GasMixerPanel(wx.Panel):
    def __init__(self, parent, HA_mixer_shifter, PV_mixer_shifter):  # , cdi):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        # self.cdi = cdi
        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', mixer_shifter=HA_mixer_shifter)  # , cdi=self.cdi)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', mixer_shifter=PV_mixer_shifter)  # , cdi=self.cdi)
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
    def __init__(self, parent, name, mixer_shifter: GB100, **kwds):  # cdi
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE

        self.parent = parent
        self.name = name
        self.mixer_shifter = mixer_shifter
        # self.cdi = cdi
        self.gas1 = list(self.mixer_shifter.gas_dict.keys())[0]  # how to access key in value:key dict pair
        self.gas2 = list(self.mixer_shifter.gas_dict.keys())[1]

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        # Pull initial total flow and create display
        total_flow = self.mixer_shifter.mixer.get_mainboard_total_flow()
        self.label_total_flow = wx.StaticText(self, label='Total gas flow (mL/min):')
        self.input_total_flow = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400, initial=total_flow, inc=1)

        # Pull initial gas mix percentages and flow rates
        channel_nr = 1  # always just change the first channel and the rest will follow
        gas1_mix_perc = self.mixer_shifter.mixer.get_channel_percent_value(channel_nr)
        gas2_mix_perc = str(100 - gas1_mix_perc)
        gas1_flow = str(self.mixer_shifter.mixer.get_channel_sccm(1))
        gas2_flow = str(self.mixer_shifter.mixer.get_channel_sccm(2))
        gas1_target_flow = str(self.mixer_shifter.mixer.get_channel_target_sccm(1))
        gas2_target_flow = str(self.mixer_shifter.mixer.get_channel_target_sccm(2))

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
        # self.timer.Start(30, wx.TIMER_CONTINUOUS)

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
        # self.Bind(wx.EVT_TIMER, self.CheckHardwareForUpdates)

    def OnManualStart(self, evt):
        self.automatic_start_btn.Disable()
        working_status = self.mixer_shifter.mixer.get_working_status()

        if working_status == 0:  # 0 is off
            self.mixer_shifter.mixer.set_working_status_ON()
            self.manual_start_btn.SetLabel('Stop Manual')
        else:
            self.mixer_shifter.mixer.set_working_status_OFF()
            self.manual_start_btn.SetLabel('Start Manual')
            self.automatic_start_btn.Enable()

        time.sleep(4.0)
        self.UpdateAppFlows()

    def OnAutoStart(self, evt):
        self.manual_start_btn.Disable()
        GB100_working_status = self.mixer_shifter.mixer.get_working_status()

        if GB100_working_status == 0:
            self.mixer_shifter.mixer.set_working_status_ON()
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.mixer_shifter.update_pH(self.cdi)
            self.mixer_shifter.update_CO2(self.cdi)
            self.mixer_shifter.update_O2(self.cdi)
            # loop through on a timer
            new_perc = 1  # need real value as output from CDI methods
            self.UpdateAppPercentages(new_perc)
        else:
            self.automatic_start_btn.SetLabel('Start Automatic')
            self.cdi.stop()
            self.manual_start_btn.Enable()

    def OnChangePercentMix(self, evt):
        new_percent = self.input_percent_gas1.GetValue()

        # Update gas mixer percentages
        self.mixer_shifter.mixer.set_channel_percent_value(1, new_percent)
        self.mixer_shifter.mixer.set_channel_percent_value(2, 100-new_percent)
        time.sleep(2.0)

        if self.manual_start_btn.GetLabel() == "Stop Manual":  # prevents turning on if user hasn't hit start
            self.EnsureTurnedOn()
            time.sleep(1.0)

        self.UpdateAppPercentages(new_percent)

    def OnChangeTotalFlow(self, evt):
        new_total_flow = self.input_total_flow.GetValue()
        self.mixer_shifter.mixer.set_mainboard_total_flow(int(new_total_flow))

        if self.manual_start_btn.GetLabel() == "Stop Manual":
            self.EnsureTurnedOn()
            time.sleep(1.0)

        self.UpdateAppFlows()

    def EnableButtons(self):
        if not self.automatic_start_btn.IsEnabled() and not self.manual_start_btn.IsEnabled():  # starting condition
            self.manual_start_btn.Enable()
            self.automatic_start_btn.Enable()

    def UpdateAppPercentages(self, new_perc):
        gas2_mix_perc = str(100 - new_perc)
        self.percent_gas2.SetValue(gas2_mix_perc)

        self.UpdateAppFlows()

    def UpdateAppFlows(self):
        gas1_flow = str(self.mixer_shifter.mixer.get_channel_sccm_av(1))
        gas2_flow = str(self.mixer_shifter.mixer.get_channel_sccm_av(2))
        self.flow_gas1.SetValue(gas1_flow)
        self.flow_gas2.SetValue(gas2_flow)

        gas1_target_flow = str(self.mixer_shifter.mixer.get_channel_target_sccm(1))
        gas2_target_flow = str(self.mixer_shifter.mixer.get_channel_target_sccm(2))
        self.target_flow_gas1.SetValue(gas1_target_flow)
        self.target_flow_gas2.SetValue(gas2_target_flow)

        self.EnableButtons()

    def EnsureTurnedOn(self):
           if self.mixer_shifter.mixer.get_working_status() == 0:
               self.mixer_shifter.mixer.set_working_status_ON()

    def CheckHardwareForUpdates(self, evt):
        # if evt.GetId() == self.timer.GetId():
            # new_total_flow = self.mixer_shifter.mixer.get_mainboard_total_flow()
            # self.input_total_flow.SetValue(new_total_flow)
            # new_gas1_mix_perc = self.mixer_shifter.mixer.get_channel_percent_value(1)
            # self.input_percent_gas1.SetValue(new_gas1_mix_perc)
            # self.UpdateAppPercentages(new_gas1_mix_perc)
        pass

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self, HA_mixer_shift, PV_mixer_shift)  # , CDI_output)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
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

    HA_mixer = mcq.Main('Arterial Gas Mixer')
    HA_mixer_shift = GB100('HA', HA_mixer)
    PV_mixer = mcq.Main('Venous Gas Mixer')
    PV_mixer_shift = GB100('PV', PV_mixer)

    # TODO: Put back when SensorStream is ready
    # cdi = pyCDI.CDIStreaming('CDI')
    # cdi.read_config() need updated pyCDI and SensorPoint for this to work
    # sensorpt = SensorPoint(cdi, 'NA')
    # sensorpt.start()
    # cdi.start()
    # CDI_output = sensorpt.add_strategy(strategy=MultiVarToFile('write', 1, 17))

    app = MyTestApp(0)
    app.MainLoop()
