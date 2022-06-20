# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
from threading import Thread, Event
import logging
import time

class SyringeTimer:
    def __init__(self, name, sensor, syringe, feedback_injection_button):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.sensor = sensor
        self.syringe = syringe
        self.feedback_injection_button = feedback_injection_button
        self.threshold_value = None
        self.tolerance = None
        self.intervention = None
        self.time_between_checks = None
        self.cooldown_time = None
        self.max = None
        self.wait = None
        self.old_value = None

        self.__thread_feedback = None
        self.__evt_halt_feedback = Event()
        self.__thread_cooldown = None
        self.__evt_halt_cooldown = Event()

        if self.name == 'Insulin':
            self.insulin_basal_rate_threshold = None
            self.insulin_basal_rate_tolerance = None
            self.insulin_basal_infusion_rate_above_range = None
            self.insulin_basal_infusion_rate_in_range = None
            self.insulin_lower_glucose_limit = None
            self.old_glucose = None

    def start_feedback_injections(self):
        self.__evt_halt_feedback.clear()
        self.__thread_feedback = Thread(target=self.OnFeedbackLoop)
        self.__thread_feedback.start()

    def stop_feedback_injections(self):
        if self.__thread_feedback and self.__thread_feedback.is_alive():
            self.__evt_halt_feedback.set()
            self.__thread_feedback.join(2.0)
            self.__thread_feedback = None
        if self.__thread_cooldown and self.__thread_cooldown.is_alive():
            self.__evt_halt_cooldown.set()
            self.__thread_cooldown.join(2.0)
            self.__thread_cooldown = None
            self.syringe.cooldown = False
        return self.intervention

    def OnFeedbackLoop(self):
        while not self.__evt_halt_feedback.wait(self.time_between_checks):
            self.check_for_change()

    def OnCooldown(self):
        self.__evt_halt_cooldown.wait(self.cooldown_time)
        self.syringe.cooldown = False
        self.__evt_halt_cooldown.set()
        self.__thread_cooldown = None

    def check_for_change(self):
        change = False
        insulin_change = False
        if self.name in ['Insulin', 'Glucagon']:
            t, value = float(self.sensor.get_latest())  # Check what value could be from Dexcom sensor
        elif self.name in ['Epoprostenol', 'Phenylephrine']:
            t, value = self.sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
            value = float(value)
        else:
            self._logger.error('Perfusion-condition informed syringe injections are not supported for this syringe')
            return
        if self.name == 'Phenylephrine':
            if value > (self.threshold_value + self.tolerance):
                new_value = 'Intervention Required'
                if self.syringe.cooldown:
                    self.old_value = new_value
                    self._logger.info(f'{self.sensor.name} reads {value:.2f}; a change in {self.name} infusion rate is needed, but is currently frozen')
                else:
                    change = True
                    direction = 'high'
                    if new_value == self.old_value:
                        increment = True
                    else:
                        increment = False
                    self.old_value = new_value
            else:
                self.old_value = 'Intervention Not Required'
                self._logger.info(f'No change in {self.name} infusion rate is needed')
        elif self.name in ['Glucagon', 'Epoprostenol']:
            if value < (self.threshold_value - self.tolerance):
                new_value = 'Intervention Required'
                if self.syringe.cooldown:
                    self.old_value = new_value
                    self._logger.info(f'{self.sensor.name} reads {value:.2f}; a change in {self.name} infusion is needed, but is currently frozen')
                else:
                    change = True
                    direction = 'low'
                    if new_value == self.old_value:
                        increment = True
                    else:
                        increment = False
                    self.old_value = new_value
            else:
                self.old_value = 'Intervention Not Required'
                self._logger.info(f'No change in {self.name} infusion is needed')
        elif self.name == 'Insulin':
            if value > (self.threshold_value + self.tolerance):
                new_value = 'Intervention Required'
                if self.syringe.cooldown:
                    self.old_value = new_value
                    self._logger.info(f'{self.sensor.name} reads {value:.2f}; a bolus of {self.name} is needed, but is currently frozen')
                else:
                    change = True
                    direction = 'high'
                    if new_value == self.old_value:
                        increment = True
                    else:
                        increment = False
                    self.old_value = new_value
            else:
                self.old_value = 'Intervention Not Required'
            insulin_change, rate_intervention = self.check_for_basal_insulin_change(value)
            if not change and not insulin_change:
                self._logger.info(f'No change in {self.name} infusion is needed')
        if change:
            self.injection(self.syringe, self.name, self.sensor.name, value, self.intervention, direction, increment)
            self.__evt_halt_cooldown.clear()
            self.__thread_cooldown = Thread(target=self.OnCooldown)
            self.__thread_cooldown.start()
        if insulin_change:
            self.insulin_injection(self.syringe, self.name, self.sensor.name, value, rate_intervention)

    def check_for_basal_insulin_change(self, value):
        if value > self.insulin_basal_rate_threshold + self.insulin_basal_rate_tolerance:
            new_glucose = 'Above Range'
        elif value < self.insulin_lower_glucose_limit - self.insulin_basal_rate_tolerance:
            new_glucose = 'Below Range'
        else:
            new_glucose = 'In Range'
        if not self.old_glucose:
            self.old_glucose = new_glucose
            if self.old_glucose == 'Above Range':
                return True, 4.2
            elif self.old_glucose == 'Below Range':
                return True, 0
            elif self.old_glucose == 'In Range':
                return True, 0.5
        if self.old_glucose == new_glucose:
            return False, None  # Check to make sure that this doesn't go @ first
        else:
            self.old_glucose = new_glucose
            if self.old_glucose == 'Above Range':
                return True, 4.2
            elif self.old_glucose == 'Below Range':
                return True, 0
            elif self.old_glucose == 'In Range':
                return True, 0.5

    def injection(self, syringe, name, parameter_name, parameter, intervention_ul, direction, increment):
        if self.name == 'Glucagon':
            self.feedback_injection_button.Enable(False)
            if increment:
                intervention_ul += 100
                if intervention_ul > self.max:
                    intervention_ul = self.max  # See if changing this actually changes self.intervention
            self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; injecting {intervention_ul:.2f} uL of {name}')
            syringe.ResetSyringe()
            syringe.set_target_volume(intervention_ul, 'ul')
            syringe.set_infusion_rate(25, 'ml/min')
            syringe.infuse(intervention_ul, 25, False, True)
            self.wait = True
            time.sleep(60 * intervention_ul / 25000)
            while self.wait:
                response = float(self.syringe.get_infused_volume().split(' ')[0])
                unit = self.syringe.get_infused_volume().split(' ')[1]
                if 'ml' in unit:
                    response = response * 1000
                if response >= intervention_ul:
                    self.wait = False
            syringe.reset_target_volume()
            syringe.cooldown = True
            self.feedback_injection_button.Enable(True)
        if self.name in ['Epoprostenol', 'Phenylephrine']:
            self.feedback_injection_button.Enable(False)
            if increment:
                intervention_ul += 1
                if intervention_ul > self.max:
                    intervention_ul = self.max
            self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; changing {name} infusion rate to {intervention_ul:.2f}')
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
        #    syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)  Check to see if I need to stop syringe or if I can just change the rate?
            syringe.set_infusion_rate(intervention_ul, 'ul/min')
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            syringe.cooldown = True
            self.feedback_injection_button.Enable(True)
        elif self.name == 'Insulin':
            self.feedback_injection_button.Enable(False)
            if increment:
                intervention_ul += 1
                if intervention_ul > self.max:
                    intervention_ul = self.max
            self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; injecting {intervention_ul:.2f} uL of {name}')
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.ResetSyringe()
            syringe.set_target_volume(intervention_ul, 'ul')
            syringe.set_infusion_rate(25, 'ml/min')
            syringe.infuse(intervention_ul, 25, False, True)
            self.wait = True
            time.sleep(60 * intervention_ul / 25000)
            while self.wait:
                response = float(self.syringe.get_infused_volume().split(' ')[0])
                unit = self.syringe.get_infused_volume().split(' ')[1]
                if 'ml' in unit:
                    response = response * 1000
                if response >= intervention_ul:
                    self.wait = False
            syringe.reset_target_volume()
            if ml_min_rate:
                unit = 'ml/min'
            else:
                unit = 'ul/min'
            syringe.set_infusion_rate(infuse_rate, unit)
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            syringe.cooldown = True
            self.feedback_injection_button.Enable(True)

    def insulin_injection(self, syringe, name, parameter_name, parameter, rate_intervention):
        self.feedback_injection_button.Enable(False)
        self._logger.info(f'{parameter_name} reads {parameter:.2f}; changing {name} infusion rate to {intervention_ul:.2f}')
        #    infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
        #    syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)  Check to see if I need to stop syringe or if I can just change the rate?
        syringe.set_infusion_rate(rate_intervention, 'ul/min')
        infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
        syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
        self.feedback_injection_button.Enable(True)
