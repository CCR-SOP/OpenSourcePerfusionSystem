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
        self.parent = parent
        self._sensor = sensor
        self._name = name
        self._injection = injection

        self._inc = 0.1

        section = LP_CFG.get_hwcfg_section(self._injection.name)
        self.manucode = section['manucode']
        self.size = section['size']
        self.inject = section['inject']
        self.injectionunit = section['injectionunit']

        static_box = wx.StaticBox(self, wx.ID_ANY, label=name)
        self.sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.spin_rate = wx.SpinCtrlDouble(self, min=0, max=100000, inc=self._inc)
        self.spin_rate.SetValue(float(self.inject))
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
            self.enable_buttons(False)
            self._injection.ResetSyringe()
            rate = self.spin_rate.GetValue()
            unit = self.choice_rate.GetString(self.choice_rate.GetSelection())
            self._injection.set_infusion_rate(rate, unit)
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_basal.SetLabel('Stop Basal Infusion')
        elif state == 'Stop Basal Infusion':
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_basal.SetLabel('Start Basal Infusion')
            self.enable_buttons(True)

    def OnOneTimeBolus(self, evt):
        self.btn_start_basal.Enable(False)
        self.enable_buttons(False)
        self._injection.ResetSyringe()
        self._injection.set_infusion_rate(25, 'ml/min')
        volume = self.spin_1TB_volume.GetValue()
        unit = self.choice_1TB_unit.GetString(self.choice_1TB_unit.GetSelection())
        self._injection.set_target_volume(volume, unit)
        if 'ul' in unit:
            volume_unit = False
            volume_ul = volume
        else:
            volume_unit = True
            volume_ul = volume * 1000
        self._injection.infuse(volume, 25, volume_unit, True)
        while True:
            response = float(self._injection.get_infused_volume().split(' ')[0])
            unit = self._injection.get_infused_volume().split(' ')[1]
            if 'ml' in unit:
                response = response * 1000
            if response >= (volume_ul - 1):
                break
        self.enable_buttons(True)
        self.btn_start_basal.Enable(True)

    def enable_buttons(self, state):
        self.spin_rate.Enable(state)
        self.choice_rate.Enable(state)
        self.spin_1TB_volume.Enable(state)
        self.choice_1TB_unit.Enable(state)
        self.btn_start_1TB.Enable(state)
        if self._injection.name in ['Epoprostenol', 'Phenylephrine', 'Insulin', 'Glucagon']:
            self._panel_feedback.btn_update_threshold.Enable(state)
            self._panel_feedback.btn_update_tolerance.Enable(state)
            self._panel_feedback.btn_update_time_between_checks.Enable(state)
            self._panel_feedback.btn_update_cooldown_time.Enable(state)
            self._panel_feedback.btn_update_max.Enable(state)
            self._panel_feedback.btn_update_min.Enable(state)
            self._panel_feedback.btn_update_incrementation.Enable(state)
            self._panel_feedback.btn_update_reduction_time.Enable(state)
            self._panel_feedback.btn_start_feedback_injections.Enable(state)
            if self._injection.name == 'Insulin':
                self._panel_feedback.btn_update_upper_glucose_limit.Enable(state)
                self._panel_feedback.btn_update_basal_rate_tolerance.Enable(state)
                self._panel_feedback.btn_update_basal_infusion_rate_above_range.Enable(state)
                self._panel_feedback.btn_update_basal_infusion_rate_in_range.Enable(state)
                self._panel_feedback.btn_update_lower_glucose_limit.Enable(state)

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
        self.intervention = section['intervention']
        self.timebetween = section['timebetween']
        self.cooldown = section['cooldown']
        self.max = section['max']
        self.min = section['min']
        self.incrementation = section['incrementation']
        self.reductiontime = section['reductiontime']

        if self._injection.name in ['Insulin', 'Glucagon']:
            label_intervention_description = 'Inject Bolus When '
            label_intervention = 'Injection Volume (uL)'
        elif self._injection.name in ['Epoprostenol', 'Phenylephrine']:
            label_intervention_description = 'Change Rate When '
            label_intervention = 'Infusion Rate (ul/min)'
        else:
            label_intervention_description = ''
            label_intervention = ''

        self.label_threshold = wx.StaticText(self, label=label_intervention_description + self.feedback + ' ' + self.feedbackunit + ' is ' + self.direction)
        self.spin_threshold = wx.SpinCtrlDouble(self, min=0, max=1000, initial=float(self.threshold), inc=0.1)
        self.btn_update_threshold = wx.Button(self, label='Update Threshold')

        self.label_tolerance = wx.StaticText(self, label='Tolerance ' + self.feedbackunit)
        self.spin_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=float(self.tolerance), inc=0.1)
        self.btn_update_tolerance = wx.Button(self, label='Update Tolerance')

        self.label_intervention = wx.StaticText(self, label='Initial ' + label_intervention)
        self.spin_intervention = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.intervention), inc=0.1)

        self.label_time_between_checks = wx.StaticText(self, label='Time Between Checks (s): ')
        self.spin_time_between_checks = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.timebetween), inc=1)
        self.btn_update_time_between_checks = wx.Button(self, label='Update Time Between Checks')

        self.label_cooldown_time = wx.StaticText(self, label='Cooldown Time (s): ')
        self.spin_cooldown_time = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.cooldown), inc=1)
        self.btn_update_cooldown_time = wx.Button(self, label='Update Cooldown Time')

        self.label_max = wx.StaticText(self, label='Max ' + label_intervention)
        self.spin_max = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.max), inc=0.1)
        self.btn_update_max = wx.Button(self, label='Update Max' + label_intervention)

        self.label_min = wx.StaticText(self, label='Minimum ' + label_intervention)
        self.spin_min = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.min), inc=0.1)
        self.btn_update_min = wx.Button(self, label='Update Minimum ' + label_intervention)

        self.label_incrementation = wx.StaticText(self, label='Incremental Change in ' + label_intervention)
        self.spin_incrementation = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.incrementation), inc=0.1)
        self.btn_update_incrementation = wx.Button(self, label='Update Incremental Increase')

        self.label_reduction_time = wx.StaticText(self, label='Reduce Intervention when  ' + self.feedback + ' ' + self.feedbackunit + ' is in range for (s)')
        self.spin_reduction_time = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.reductiontime), inc=1)
        self.btn_update_reduction_time = wx.Button(self, label='Update')

        if self._injection.name == 'Insulin':
            section = LP_CFG.get_hwcfg_section(self._injection.name)
            self.upperglucoselimit = section['upperglucoselimit']
            self.basalratetolerance = section['basalratetolerance']
            self.aboverangerate = section['aboverangerate']
            self.inrangerate = section['inrangerate']
            self.lowerglucoselimit = section['lowerglucoselimit']

            self.label_upper_glucose_limit = wx.StaticText(self, label='Reduce Basal Infusion Rate When ' + self.feedback + ' ' + self.feedbackunit + ' is Less Than')
            self.spin_upper_glucose_limit = wx.SpinCtrlDouble(self, min=0, max=1000, initial=float(self.upperglucoselimit), inc=0.1)
            self.btn_update_upper_glucose_limit = wx.Button(self, label='Update')

            self.label_basal_rate_tolerance = wx.StaticText(self, label='Tolerance ' + self.feedbackunit)
            self.spin_basal_rate_tolerance = wx.SpinCtrlDouble(self, min=0, max=100, initial=float(self.basalratetolerance), inc=0.1)
            self.btn_update_basal_rate_tolerance = wx.Button(self, label='Update')

            self.label_basal_infusion_rate_above_range = wx.StaticText(self, label='Infusion Rate (ul/min) When ' + self.feedback + ' ' + self.feedbackunit + ' is Above Range')  # If this is changed while the syringe_timer main thread is running, the new infusion rate will only be registered when the glucose goes in and out of a range (e.g., if the in-range rate is changed, the new rate will take affect only if the glucose increase out of range, and then comes back into range; if the glucose stays in range, the old infusion rate will persist); to avoid this and get the change to register immediately, you can stop and restart feedback injections
            self.spin_basal_infusion_rate_above_range = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.aboverangerate), inc=0.1)
            self.btn_update_basal_infusion_rate_above_range = wx.Button(self, label='Update')

            self.label_basal_infusion_rate_in_range = wx.StaticText(self, label='Infusion Rate (ul/min) When ' + self.feedback + ' ' + self.feedbackunit + ' is In Range')  # If this is changed while the syringe_timer main thread is running, the new infusion rate will only be registered when the glucose goes in and out of a range (e.g., if the in-range rate is changed, the new rate will take affect only if the glucose increase out of range, and then comes back into range; if the glucose stays in range, the old infusion rate will persist); to avoid this and get the change to register immediately, you can stop and restart feedback injections
            self.spin_basal_infusion_rate_in_range = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.inrangerate), inc=0.1)
            self.btn_update_basal_infusion_rate_in_range = wx.Button(self, label='Update')

            self.label_lower_glucose_limit = wx.StaticText(self, label='Lower ' + self.feedback + ' ' + self.feedbackunit + ' Limit:')
            self.spin_lower_glucose_limit = wx.SpinCtrlDouble(self, min=0, max=10000, initial=float(self.lowerglucoselimit), inc=0.1)
            self.btn_update_lower_glucose_limit = wx.Button(self, label='Update')

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
        sizer.Add(self.label_intervention, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_intervention, flags)
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
        sizer.Add(self.label_max, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_max, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_max, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_min, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_min, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_min, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_incrementation, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_incrementation, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_incrementation, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_reduction_time, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.spin_reduction_time, flags)
        sizer.AddSpacer(3)
        sizer.Add(self.btn_update_reduction_time, flags)
        self.sizer.Add(sizer)
        self.sizer.AddSpacer(20)

        if self._injection.name == 'Insulin':
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.label_upper_glucose_limit, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.spin_upper_glucose_limit, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.btn_update_upper_glucose_limit, flags)
            self.sizer.Add(sizer)
            self.sizer.AddSpacer(20)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.label_basal_rate_tolerance, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.spin_basal_rate_tolerance, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.btn_update_basal_rate_tolerance, flags)
            self.sizer.Add(sizer)
            self.sizer.AddSpacer(20)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.label_basal_infusion_rate_above_range, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.spin_basal_infusion_rate_above_range, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.btn_update_basal_infusion_rate_above_range, flags)
            self.sizer.Add(sizer)
            self.sizer.AddSpacer(20)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.label_basal_infusion_rate_in_range, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.spin_basal_infusion_rate_in_range, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.btn_update_basal_infusion_rate_in_range, flags)
            self.sizer.Add(sizer)
            self.sizer.AddSpacer(20)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.label_lower_glucose_limit, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.spin_lower_glucose_limit, flags)
            sizer.AddSpacer(3)
            sizer.Add(self.btn_update_lower_glucose_limit, flags)
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
        self.btn_update_threshold.Bind(wx.EVT_BUTTON, self.OnUpdateThreshold)
        self.btn_update_tolerance.Bind(wx.EVT_BUTTON, self.OnUpdateTolerance)
        self.btn_update_time_between_checks.Bind(wx.EVT_BUTTON, self.OnUpdateTimeBetweenChecks)
        self.btn_update_cooldown_time.Bind(wx.EVT_BUTTON, self.OnUpdateCooldown)
        self.btn_update_max.Bind(wx.EVT_BUTTON, self.OnUpdateMax)
        self.btn_update_min.Bind(wx.EVT_BUTTON, self.OnUpdateMin)
        self.btn_update_incrementation.Bind(wx.EVT_BUTTON, self.OnUpdateIncrementation)
        self.btn_update_reduction_time.Bind(wx.EVT_BUTTON, self.OnUpdateReductionTime)
        if self._injection.name == 'Insulin':
            self.btn_update_upper_glucose_limit.Bind(wx.EVT_BUTTON, self.OnUpdateUpperLimit)
            self.btn_update_basal_rate_tolerance.Bind(wx.EVT_BUTTON, self.OnUpdateBasalRateTolerance)
            self.btn_update_basal_infusion_rate_above_range.Bind(wx.EVT_BUTTON, self.OnUpdateBasalInfusionRateAboveRange)
            self.btn_update_basal_infusion_rate_in_range.Bind(wx.EVT_BUTTON, self.OnUpdateBasalInfusionRateInRange)
            self.btn_update_lower_glucose_limit.Bind(wx.EVT_BUTTON, self.OnUpdateLowerLimit)
        self.btn_start_feedback_injections.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartFeedbackInjection)

    def OnUpdateThreshold(self, evt):
        self._syringe_timer.threshold_value = self.spin_threshold.GetValue()

    def OnUpdateTolerance(self, evt):
        self._syringe_timer.tolerance = self.spin_tolerance.GetValue()

    def OnUpdateTimeBetweenChecks(self, evt):
        self._syringe_timer.time_between_checks = self.spin_time_between_checks.GetValue()

    def OnUpdateCooldown(self, evt):
        self._syringe_timer.cooldown_time = self.spin_cooldown_time.GetValue()

    def OnUpdateMax(self, evt):
        self._syringe_timer.max = self.spin_max.GetValue()

    def OnUpdateMin(self, evt):
        self._syringe_timer.min = self.spin_min.GetValue()

    def OnUpdateIncrementation(self, evt):
        self._syringe_timer.incrementation = self.spin_incrementation.GetValue()

    def OnUpdateReductionTime(self, evt):
        self._syringe_timer.reduction_time = self.spin_reduction_time.GetValue()

    def OnUpdateUpperLimit(self, evt):
        self._syringe_timer.insulin_upper_glucose_limit = self.spin_upper_glucose_limit.GetValue()

    def OnUpdateBasalRateTolerance(self, evt):
        self._syringe_timer.insulin_basal_rate_tolerance = self.spin_basal_rate_tolerance.GetValue()

    def OnUpdateBasalInfusionRateAboveRange(self, evt):
        self._syringe_timer.insulin_basal_infusion_rate_above_range = self.spin_basal_infusion_rate_above_range.GetValue()

    def OnUpdateBasalInfusionRateInRange(self, evt):
        self._syringe_timer.insulin_basal_infusion_rate_in_range = self.spin_basal_infusion_rate_in_range.GetValue()

    def OnUpdateLowerLimit(self, evt):
        self._syringe_timer.insulin_lower_glucose_limit = self.spin_lower_glucose_limit.GetValue()

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
            if self._injection.name in ['Epoprostenol', 'Phenylephrine']:
                rate = self.spin_intervention.GetValue()
                self._injection.set_infusion_rate(rate, 'ul/min')
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            elif self._injection.name == 'Insulin':
                self._syringe_timer.insulin_upper_glucose_limit = self.spin_upper_glucose_limit.GetValue()
                self._syringe_timer.insulin_basal_rate_tolerance = self.spin_basal_rate_tolerance.GetValue()
                self._syringe_timer.insulin_basal_infusion_rate_above_range = self.spin_basal_infusion_rate_above_range.GetValue()
                self._syringe_timer.insulin_basal_infusion_rate_in_range = self.spin_basal_infusion_rate_in_range.GetValue()
                self._syringe_timer.insulin_lower_glucose_limit = self.spin_lower_glucose_limit.GetValue()
                rate = self.spin_basal_infusion_rate_in_range.GetValue()
                self._injection.set_infusion_rate(rate, 'ul/min')
                infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
                self._injection.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            elif self._injection.name == 'Glucagon':
                pass
            self._syringe_timer.threshold_value = self.spin_threshold.GetValue()
            self._syringe_timer.tolerance = self.spin_tolerance.GetValue()
            self._syringe_timer.intervention = self.spin_intervention.GetValue()
            self._syringe_timer.time_between_checks = self.spin_time_between_checks.GetValue()
            self._syringe_timer.cooldown_time = self.spin_cooldown_time.GetValue()
            self._syringe_timer.max = self.spin_max.GetValue()
            self._syringe_timer.min = self.spin_min.GetValue()
            self._syringe_timer.incrementation = self.spin_incrementation.GetValue()
            self._syringe_timer.reduction_time = self.spin_reduction_time.GetValue()
            self._syringe_timer.syringe.cooldown = False
            self._syringe_timer.reduce = False
            self._syringe_timer.insulin_change = False
            self._syringe_timer.start_feedback_injections()
            self.btn_start_feedback_injections.SetLabel('Stop Feedback Injections')
        elif state == 'Stop Feedback Injections':
            latest_intervention = self._syringe_timer.stop_feedback_injections()
            self.spin_intervention.SetValue(latest_intervention)
            self.parent.spin_rate.Enable(True)
            self.parent.choice_rate.Enable(True)
            self.parent.btn_start_basal.Enable(True)
            self.parent.spin_1TB_volume.Enable(True)
            self.parent.choice_1TB_unit.Enable(True)
            self.parent.btn_start_1TB.Enable(True)
            infuse_rate, ml_min_rate, ml_volume = self._injection.get_stream_info()
            self._injection.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            self.btn_start_feedback_injections.SetLabel('Start Feedback Injections')

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        sizer = wx.GridSizer(cols=4)
        self.acq = NIDAQ_AI(period_ms=100, volts_p2p=5, volts_offset=2.5)
        self.sensor = SensorStream('Flow Sensor', 'mL/min', self.acq)
        raw = StreamToFile('StreamRaw', None, self.acq.buf_len)
        raw.open(LP_CFG.LP_PATH['stream'], f'{self.sensor.name}_raw', self.sensor.params)
        self.sensor.add_strategy(raw)
        sizer.Add(PanelAI(self, self.sensor, self.sensor.name, 'StreamRaw'), 1, wx.ALL | wx.EXPAND, border=1)

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

        section = LP_CFG.get_hwcfg_section('Heparin')
        com = section['commport']
        baud = section['baudrate']
        heparin_injection = PHDserial('Heparin')
        heparin_injection.open(com, baud)
        heparin_injection.ResetSyringe()
        heparin_injection.open_stream(LP_CFG.LP_PATH['stream'])
        heparin_injection.start_stream()

        section = LP_CFG.get_hwcfg_section('TPN & Bile Salts')
        com = section['commport']
        baud = section['baudrate']
        tpn_bilesalts_injection = PHDserial('TPN & Bile Salts')
        tpn_bilesalts_injection.open(com, baud)
        tpn_bilesalts_injection.ResetSyringe()
        tpn_bilesalts_injection.open_stream(LP_CFG.LP_PATH['stream'])
        tpn_bilesalts_injection.start_stream()

        self._syringes = [vasodilator_injection, vasoconstrictor_injection, heparin_injection, tpn_bilesalts_injection]
        self.feedback_panels = [PanelSyringe(self, self.sensor, vasodilator_injection.name, vasodilator_injection), PanelSyringe(self, self.sensor, vasoconstrictor_injection.name, vasoconstrictor_injection)]
        self.other_panels = [PanelSyringe(self, self.sensor, heparin_injection.name, heparin_injection), PanelSyringe(self, self.sensor, tpn_bilesalts_injection.name, tpn_bilesalts_injection)]
        sizer_other_panels = wx.GridSizer(cols=1)
        for panel in self.feedback_panels:
            sizer.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)

        for panel in self.other_panels:
            sizer_other_panels.Add(panel, 1, wx.ALL | wx.EXPAND, border=1)
        sizer.Add(sizer_other_panels, 1, wx.ALL | wx.EXPAND, border=1)

        self.SetSizer(sizer)
        self.Fit()
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        for panel in self.feedback_panels:
            panel._panel_feedback._syringe_timer.stop_feedback_injections()
        for syringe in self._syringes:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.close_stream()
        self.sensor.stop()
        if self.sensor.hw._task:
            self.sensor.hw.stop()
            self.sensor.hw.close()
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
