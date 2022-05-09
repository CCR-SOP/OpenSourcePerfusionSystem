# -*- coding: utf-8 -*-
"""
@author: Allen Luna
Panel for controlling syringe injections; both basal infusions and feedback-controlled infusions are handled
"""
import wx
import pyPerfusion.utils as utils
import logging

from pyHardware.pyAI_NIDAQ import NIDAQ_AI
from pyPerfusion.panel_AI import PanelAI
from pyPerfusion.syringe_timer import SyringeTimer
from pyPerfusion.SensorStream import SensorStream
import pyPerfusion.PerfusionConfig as LP_CFG
from pyPerfusion.FileStrategy import StreamToFile
from pyHardware.PHDserial import PHDserial

class PanelSyringe(wx.Panel):
    def __init__(self, parent, sensor, name, injection):
        wx.Panel.__init__(self, parent, -1)
        self._logger = logging.getLogger(__name__)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._injection = injection

        self._inc = 0.1

        section = LP_CFG.get_hwcfg_section(self._injection.name)
        self.manucode = section['manucode']
        self.size = section['size']
        self.injectionrate = section['injectionrate']
        self.injectionunit = section['injectionunit']

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_rate.SetValue(float(self.injectionrate))
        self.choice_rate = wx.Choice(self, choices=['ul/min', 'ml/min'])
        self.choice_rate.SetStringSelection(self.injectionunit)
        self.btn_start_basal = wx.ToggleButton(self, label='Start Basal Infusion')

        self.spin_1TB_volume = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_1TB_volume.SetValue(1)
        self.choice_1TB_unit = wx.Choice(self, choices=['ul', 'ml'])
        self.choice_1TB_unit.SetSelection(1)
        self.btn_start_1TB = wx.ToggleButton(self, label='Bolus')

        if self._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
            self._panel_feedback = PanelFeedbackSyringe(self, self._sensor, self._name, self._injection)

        self._injection.ResetSyringe()
        self._injection.set_syringe_manufacturer_size(self.manucode[1:4], self.size)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.spin_rate, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.choice_rate, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_start_basal, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.spin_1TB_volume, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.choice_1TB_unit, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_start_1TB, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        if self._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
            sizer.Add(self._panel_feedback, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_start_basal.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartBasal)
        self.btn_start_1TB.Bind(wx.EVT_TOGGLEBUTTON, self.OnOneTimeBolus)

    def OnStartBasal(self, evt):
        state = self.btn_start_basal.GetLabel()
        if state == 'Start Basal Infusion':
            self._injection.ResetSyringe()
            rate = self.spin_rate.GetValue()
            unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
            self._injection.set_infusion_rate(rate, unit)
            self.spin_rate.Enable(False)
            self.choice_rate.Enable(False)
            self.spin_1TB_volume.Enable(False)
            self.choice_1TB_unit.Enable(False)
            self.btn_start_1TB.Enable(False)
            if self._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
                self._panel_feedback.btn_update_injection_volume.Enable(False)
                self._panel_feedback.btn_update_threshold.Enable(False)
                self._panel_feedback.btn_update_tolerance.Enable(False)
                self._panel_feedback.btn_update_time_between_checks.Enable(False)
                self._panel_feedback.btn_update_cooldown_time.Enable(False)
                self._panel_feedback.btn_start_feedback_injections.Enable(False)
                self._panel_feedback.btn_basal_infusion_status.Enable(False)
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_basal.SetLabel('Stop Basal Infusion')
        elif state == 'Stop Basal Infusion':
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.spin_rate.Enable(True)
            self.choice_rate.Enable(True)
            self.spin_1TB_volume.Enable(True)
            self.choice_1TB_unit.Enable(True)
            self.btn_start_1TB.Enable(True)
            if self._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
                self._panel_feedback.btn_update_injection_volume.Enable(True)
                self._panel_feedback.btn_update_threshold.Enable(True)
                self._panel_feedback.btn_update_tolerance.Enable(True)
                self._panel_feedback.btn_update_time_between_checks.Enable(True)
                self._panel_feedback.btn_update_cooldown_time.Enable(True)
                self._panel_feedback.btn_start_feedback_injections.Enable(True)
                self._panel_feedback.btn_basal_infusion_status.Enable(True)
            self.btn_start_basal.SetLabel('Start Basal Infusion')

    def OnOneTimeBolus(self, evt):
        self._injection.ResetSyringe()
        self._injection.set_infusion_rate(25, 'ml/min')
        volume = self.spin_1TB_volume.GetValue()
        unit = self.choice_1TB_unit.GetString(self.choice_1TB_unit.GetSelection())
        self._injection.set_target_volume(volume, unit)
        if 'ul' in unit:
            volume_unit = False
        else:
            volume_unit = True
        self._injection.infuse(volume, 25, volume_unit, True)

class PanelFeedbackSyringe(wx.Panel):
    def __init__(self, parent, sensor, name, injection):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._injection = injection

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        section = LP_CFG.get_hwcfg_section(self._injection.name)
        self.feedback = section['feedback']
        self.feedbackunit = section['feedbackunit']
        self.direction = section['direction']
        self.threshold = section['threshold']
        self.tolerance = section['tolerance']
        self.injectionvolume = section['injectionvolume']
        self.timebetween = section['timebetween']
        self.cooldown = section['cooldown']

        self.label_threshold = wx.StaticText(self, label='Inject When ' + self.feedback + ' ' + self.feedbackunit + ' is ' + self.direction)
        self.spin_threshold = wx.SpinCtrlDouble(self, min=0, max=1000, initial=float(self.threshold), inc=0.1)
        self.btn_update_threshold = wx.Button(self, label='Update Threshold')

        self.label_tolerance = wx.StaticText(self, label='Tolerance ' + self.feedbackunit)
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=float(self.tolerance), inc=0.1)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_injection_volume = wx.StaticText(self, label='Injection Volume (uL): ')
        self.spin_injection_volume = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.injectionvolume), inc=1)
        self.btn_update_injection_volume = wx.Button(self, label='Update Injection Volume')

        self.label_time_between_checks = wx.StaticText(self, label='Time Between Checks (s): ')
        self.spin_time_between_checks = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.timebetween), inc=1)
        self.btn_update_time_between_checks = wx.Button(self, label='Update Time Between Checks')

        self.label_cooldown_time = wx.StaticText(self, label='Cooldown Time (s): ')
        self.spin_cooldown_time = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.cooldown), inc=1)
        self.btn_update_cooldown_time = wx.Button(self, label='Update Cooldown Time')

        self.btn_basal_infusion_status = wx.ToggleButton(self, label='Basal Infusion Active')

        self.btn_start_feedback_injections = wx.ToggleButton(self, label='Start Feedback Injections')

        self._syringe_timer = SyringeTimer(self._injection.name, self._sensor, self._injection, self.btn_start_feedback_injections)

        self.__do_layout()
        self.__set_bindings()

    def __do_layout(self):
        flags = wx.SizerFlags().Expand()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_threshold, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_threshold, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_threshold, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_tolerance, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_tolerance, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_tolerance, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_injection_volume, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_injection_volume, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_injection_volume, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_time_between_checks, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_time_between_checks, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_time_between_checks, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_cooldown_time, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_cooldown_time, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_cooldown_time, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_basal_infusion_status, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btn_start_feedback_injections)
        self.sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def __set_bindings(self):
        self.btn_update_injection_volume.Bind(wx.EVT_BUTTON, self.OnUpdateInjectionVolume)
        self.btn_update_threshold.Bind(wx.EVT_BUTTON, self.OnUpdateThreshold)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnUpdateTolerance)
        self.btn_update_time_between_checks.Bind(wx.EVT_BUTTON, self.OnUpdateTimeBetweenChecks)
        self.btn_update_cooldown_time.Bind(wx.EVT_BUTTON, self.OnUpdateCooldown)
        self.btn_basal_infusion_status.Bind(wx.EVT_TOGGLEBUTTON, self.OnBasalInfusionToggle)
        self.btn_start_feedback_injections.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartFeedbackInjection)

    def OnBasalInfusionToggle(self, evt):
        state = self.btn_basal_infusion_status.GetLabel()
        if state == 'Basal Infusion Active':
            self.btn_basal_infusion_status.SetLabel('Basal Infusion Inactive')
        elif state == 'Basal Infusion Inactive':
            self.btn_basal_infusion_status.SetLabel('Basal Infusion Active')

    def OnStartFeedbackInjection(self, evt):
        state = self.btn_start_feedback_injections.GetLabel()
        if state == 'Start Feedback Injections':
            self._injection.ResetSyringe()
            self.parent.spin_rate.Enable(False)
            self.parent.choice_rate.Enable(False)
            self.parent.btn_start_basal.Enable(False)
            self.parent.spin_1TB_volume.Enable(False)
            self.parent.choice_1TB_unit.Enable(False)
            self.parent.btn_start_1TB.Enable(False)
            self.btn_basal_infusion_status.Enable(False)
            if self.btn_basal_infusion_status.GetLabel() == 'Basal Infusion Active':
                rate = self.parent.spin_rate.GetValue()
                unit = self.parent.choice_rate.GetString(self.parent.choice_rate.GetSelection())
                self._injection.set_infusion_rate(rate, unit)
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
                self._syringe_timer.basal = True
            else:
                self._syringe_timer.basal = False
            self._syringe_timer.threshold_value = self.spin_threshold.GetValue()
            self._syringe_timer.tolerance = self.spin_tolerance.GetValue()
            self._syringe_timer.injection_volume = self.spin_injection_volume.GetValue()
            self._syringe_timer.time_between_checks = self.spin_time_between_checks.GetValue()
            self._syringe_timer.cooldown_time = self.spin_cooldown_time.GetValue()
            self._syringe_timer.syringe.cooldown = False
            self._syringe_timer.start_bolus_injections()
            self.btn_start_feedback_injections.SetLabel('Stop Feedback Injections')
        elif state == 'Stop Feedback Injections':
            self._syringe_timer.stop_bolus_injections()
            self.parent.spin_rate.Enable(True)
            self.parent.choice_rate.Enable(True)
            self.parent.btn_start_basal.Enable(True)
            self.parent.spin_1TB_volume.Enable(True)
            self.parent.choice_1TB_unit.Enable(True)
            self.parent.btn_start_1TB.Enable(True)
            self.btn_basal_infusion_status.Enable(True)
            if self.btn_basal_infusion_status.GetLabel() == 'Basal Infusion Active':
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_feedback_injections.SetLabel('Start Feedback Injections')

    def OnUpdateInjectionVolume(self, evt):
        self._syringe_timer.injection_volume = self.spin_injection_volume.GetValue()

    def OnUpdateThreshold(self, evt):
        self._syringe_timer.threshold_value = self.spin_threshold.GetValue()

    def OnUpdateTolerance(self, evt):
        self._syringe_timer.tolerance = self.spin_tolerance.GetValue()

    def OnUpdateTimeBetweenChecks(self, evt):
        self._syringe_timer.time_between_checks = self.spin_time_between_checks.GetValue()

    def OnUpdateCooldown(self, evt):
        self._syringe_timer.cooldown_time = self.spin_cooldown_time.GetValue()

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=4)
        self._lgr = logging.getLogger(__name__)
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Flow Sensor', 'mL/min', self.acq)
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)
        sizer.Add(PanelAI(self, self.sensor, self.sensor.name, 'StreamRaw'), 1, wx.ALL | wx.EXPAND, border=1)

        section = LP_CFG.get_hwcfg_section('Heparin')
        com = section['commport']
        baud = section['baudrate']
        heparin_injection = PHDserial('Heparin')
        heparin_injection.open(com, baud)
        heparin_injection.ResetSyringe()
        heparin_injection.open_stream(LP_CFG.LP_PATH['stream'])
        heparin_injection.start_stream()

        section = LP_CFG.get_hwcfg_section('Epoprostenol')
        com = section['commport']
        baud = section['baudrate']
        vasodilator_injection = PHDserial('Epoprostenol')
        vasodilator_injection.open(com, baud)
        vasodilator_injection.ResetSyringe()
        vasodilator_injection.open_stream(LP_CFG.LP_PATH['stream'])
        vasodilator_injection.start_stream()

        section = LP_CFG.get_hwcfg_section('Phenylephrine')
        com = section['commport']
        baud = section['baudrate']
        vasoconstrictor_injection = PHDserial('Phenylephrine')
        vasoconstrictor_injection.open(com, baud)
        vasoconstrictor_injection.ResetSyringe()
        vasoconstrictor_injection.open_stream(LP_CFG.LP_PATH['stream'])
        vasoconstrictor_injection.start_stream()

        self._syringes = [heparin_injection, vasoconstrictor_injection, vasodilator_injection]
        self.panels = [PanelSyringe(self, None, heparin_injection.name, heparin_injection), PanelSyringe(self, self.sensor, vasodilator_injection.name, vasodilator_injection), PanelSyringe(self, self.sensor, vasoconstrictor_injection.name, vasoconstrictor_injection)]
        sizer.Add(self.panels[0], 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.panels[1], 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(self.panels[2], 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.panels:
            if panel._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
                panel._panel_feedback._syringe_timer.stop_bolus_injections()
        for syringe in self._syringes:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.close_stream()
        self.sensor.stop()
        self.Destroy()

class MyTestApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(frame)
        frame.Show()
        return True

if __name__ == "__main__":
    LP_CFG.set_base(basepath='~/Documents/LPTEST')
    LP_CFG.update_stream_folder()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    utils.setup_stream_logger(logger, logging.DEBUG)
    utils.setup_default_logging(filename='panel_syringe')
    app = MyTestApp(0)
    app.MainLoop()
