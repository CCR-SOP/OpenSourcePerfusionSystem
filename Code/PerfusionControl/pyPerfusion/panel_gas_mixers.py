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
from pyPerfusion.pyGB100_SL import GB100_shift
# import something for CDI

PerfusionConfig.set_test_config()
utils.setup_stream_logger(logging.getLogger(__name__), logging.DEBUG)
utils.configure_matplotlib_logging()

HA_mixer = mcq.Main('Arterial Gas Mixer')
HA_mixer_shift = GB100_shift('HA', HA_mixer)
PV_mixer = mcq.Main('Venous Gas Mixer')
PV_mixer_shift = GB100_shift('PV', PV_mixer)

class GasMixerPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self._panel_HA = BaseGasMixerPanel(self, name='Arterial Gas Mixer', mixer_shifter=HA_mixer_shift)
        self._panel_PV = BaseGasMixerPanel(self, name='Venous Gas Mixer', mixer_shifter=PV_mixer_shift)
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
    def __init__(self, parent, name, mixer_shifter: GB100_shift, **kwds):
        wx.Panel.__init__(self, parent, -1)
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE

        self.parent = parent
        self.name = name
        self.mixer_shifter = mixer_shifter
        self.gas1 = list(self.mixer_shifter.gas_dict.keys())[0]
        self.gas2 = list(self.mixer_shifter.gas_dict.keys())[1]

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        total_flow = self.mixer_shifter.mixer.get_mainboard_total_flow()
        self.label_total_flow = wx.StaticText(self, label='Total gas flow (mL/min):')
        self.input_total_flow = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=400, initial=total_flow, inc=1)

        channel_nr = 1  # always just change the first channel and the rest will follow
        gas1_mix_perc = self.mixer_shifter.mixer.get_channel_percent_value(channel_nr)
        gas2_mix_perc = 100 - gas1_mix_perc
        gas2_mix_str = str(gas2_mix_perc)

        gas1_flow = self.mixer_shifter.mixer.get_channel_target_sccm(1)
        gas2_flow = self.mixer_shifter.mixer.get_channel_target_sccm(2)
        gas1_flow_str = str(gas1_flow)
        gas2_flow_str = str(gas2_flow)

        self.label_gas1 = wx.StaticText(self, label=f'{self.gas1} % Mix:')
        self.input_gas1 = wx.SpinCtrlDouble(self, wx.ID_ANY | wx.EXPAND, min=0, max=100, initial=gas1_mix_perc, inc=1)
        self.label_flow_gas1 = wx.StaticText(self, label=f'{self.gas1} actual flow (mL/min):')
        self.flow_gas1 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas1_flow_str)

        self.label_gas2 = wx.StaticText(self, label=f'{self.gas2} % Mix:')
        self.input_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas2_mix_str)
        self.label_flow_gas2 = wx.StaticText(self, label=f'{self.gas2} actual flow (mL/min):')
        self.flow_gas2 = wx.TextCtrl(self, style=wx.TE_READONLY, value=gas2_flow_str)

        self.manual_start_btn = wx.ToggleButton(self, label='Manual Start')
        self.automatic_start_btn = wx.ToggleButton(self, label='Automatic Start')

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Border(wx.ALL, 5).Center()
        sizer_cfg = wx.GridSizer(cols=2)

        sizer_cfg.Add(self.label_total_flow, flags)
        sizer_cfg.Add(self.input_total_flow, flags)

        sizer_cfg.Add(self.label_gas1, flags)
        sizer_cfg.Add(self.input_gas1, flags)
        sizer_cfg.Add(self.label_flow_gas1, flags)
        sizer_cfg.Add(self.flow_gas1, flags)

        sizer_cfg.Add(self.label_gas2, flags)
        sizer_cfg.Add(self.input_gas2, flags)
        sizer_cfg.Add(self.label_flow_gas2, flags)
        sizer_cfg.Add(self.flow_gas2, flags)

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
        self.input_gas1.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangePercentMix)
        self.input_total_flow.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeTotalFlow)

    def OnManualStart(self, evt):
        working_status = self.mixer_shifter.mixer.get_working_status()
        if working_status == 1:  # 1 is off
            self.mixer_shifter.mixer.set_working_status_ON()
            self.manual_start_btn.SetLabel('Stop Manual')
        else:
            self.manual_start_btn.SetLabel('Start Manual')

    def OnAutoStart(self, evt):
        working_status = self.mixer_shifter.mixer.get_working_status()
        CDI_output = [1] * 18  # BIND THIS TO THE REAL CDI OUTPUT
        if working_status == 1:  # 1 is off
            self.mixer_shifter.mixer.set_working_status_ON()
            self.automatic_start_btn.SetLabel('Stop Automatic')
            self.mixer_shifter.check_pH(CDI_output)
            self.mixer_shifter.check_CO2(CDI_output)
            self.mixer_shifter.check_O2(CDI_output)
            # something to make this repeat every 5 minutes
            # change all of the displays - maybe this should be an independent method
        else:
            self.automatic_start_btn.SetLabel('Start Automatic')
            # break out of the 5 minute loop

    def OnChangePercentMix(self, evt):
        new_percent = evt.GetValue()

        # Update gas mixer percentages
        self.mixer_shifter.mixer.set_channel_percent_value(1, new_percent)
        self.mixer_shifter.mixer.set_channel_percent_value(2, 100-new_percent)

        # Update app display to reflect new values
        gas2_mix_perc = 100 - new_percent  # or pull this value from the gas mixer?
        gas2_mix_str = str(gas2_mix_perc)
        self.input_gas2.SetValue(gas2_mix_str)

        gas1_flow = self.mixer_shifter.mixer.get_channel_sccm_av(1)
        gas2_flow = self.mixer_shifter.mixer.get_channel_sccm_av(2)
        gas1_flow_str = str(gas1_flow)
        gas2_flow_str = str(gas2_flow)
        self.flow_gas1.SetValue(gas1_flow_str)
        self.flow_gas2.SetValue(gas2_flow_str)

    def OnChangeTotalFlow(self, evt):
        new_total_flow = evt.GetValue()
        self.mixer_shifter.mixer.set_mainboard_total_flow(new_total_flow)
        print(new_total_flow)
        # this isn't working? i can't figure out why since I call this the same way in the (working) example file
        # Error: failed all the attempts


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.panel = GasMixerPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
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
    utils.configure_matplotlib_logging()
    app = MyTestApp(0)
    app.MainLoop()