# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
from threading import Thread, Event, Timer
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
        self.time_between_checks = None
        self.cooldown_time = None
        self.max = None
        self.min = None
        self.incrementation = None
        self.reduction_time = None

        self.intervention = None

        self.increase = None
        self.direction = None
        self.old_value = None
        self.old_time = None

        self.wait = None

        self.insulin_change = None
        self.insulin_rate_intervention = None

        if self.name == 'Insulin':
            self.insulin_upper_glucose_limit = None
            self.insulin_basal_rate_tolerance = None
            self.insulin_basal_infusion_rate_above_range = None
            self.insulin_basal_infusion_rate_in_range = None
            self.insulin_lower_glucose_limit = None
            self.old_glucose = None

        self.__thread_feedback = None
        self.__evt_halt_feedback = Event()
        self.__thread_cooldown = None
        self.__evt_halt_cooldown = Event()

        self.reduction_timer = None
        self.reduce = None

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

    def OnReductionTimer(self):
        self.reduce = True
        self.reduction_timer = None

    def out_of_range(self, value):
        new_value = 'Intervention Required'
        if self.reduction_timer:
            self.reduction_timer.cancel()
            self.reduction_timer = None
        if self.syringe.cooldown:
            self.old_value = new_value
            self._logger.info(f'{self.sensor.name} reads {value:.2f}; a change in {self.name} infusion rate is needed, but is currently frozen')
        else:
            self.increase = True
            self.old_value = new_value
            if self.name in ['Insulin', 'Phenylephrine']:
                self.direction = 'high'
            elif self.name in ['Glucagon', 'Epoprostenol']:
                self.direction = 'low'
            else:
                self.direction = None

    def in_range(self):
        new_value = 'Intervention Not Required'
        if not self.syringe.cooldown:
            if new_value == self.old_value or not self.old_value:  # If an injection hasn't just been given, and if the flow is steadily in range, start / continue thread looking to reduce flow
                if not self.reduction_timer:
                    self.reduction_timer = Timer(self.reduction_time, self.OnReductionTimer)
                    self.reduction_timer.start()
                else:
                    pass
        self.old_value = new_value

    def check_for_change(self):
        self.increase = False
        self.direction = None
        self.insulin_change = False
        if self.name in ['Insulin', 'Glucagon']:
            t, value = self.sensor.get_latest()  # Check what value could be from Dexcom sensor
            if not t or t == self.old_time or not value:
                self._logger.error(f'Dexcom Sensor is currently inactive; no change in {self.name} infusion rate')
                self.old_time = t
                return
            else:
                value = float(value)
                print(value)
                self.old_time = t
        elif self.name in ['Epoprostenol', 'Phenylephrine']:
            t, value = self.sensor.get_file_strategy('StreamRaw').retrieve_buffer(0, 1)
            value = float(value)
        else:
            self._logger.error('Perfusion-condition informed syringe injections are not supported for this syringe')
            return
        if self.name in ['Phenylephrine', 'Insulin']:
            if value > (self.threshold_value + self.tolerance) and not self.reduce:
                self.out_of_range(value)
            elif not self.reduce:
                self.in_range()
            if self.name == 'Insulin':
                self.insulin_change, self.insulin_rate_intervention = self.check_for_basal_insulin_change(value)
        elif self.name in ['Glucagon', 'Epoprostenol']:
            if value < (self.threshold_value - self.tolerance) and not self.reduce:
                self.out_of_range(value)
            elif not self.reduce:
                self.in_range()
        if self.increase or self.reduce or self.insulin_change:
            if self.increase and self.reduce:  # Handles rare case where reduction timer finishes at the same time that an increase in infusion rate is indicated
                self.reduce = False
                if self.reduction_timer:
                    self.reduction_timer.cancel()
                self.reduction_timer = None
            if self.increase:
                current_intervention = self.intervention
                self.intervention += self.incrementation
                if self.intervention > self.max:
                    self.intervention = self.max
                    if self.intervention == current_intervention:
                        self._logger.info(f'{self.name} infusion rate is maxed out')
                        return
                if self.intervention < self.min:
                    self.intervention = self.min
                    if self.intervention == current_intervention:
                        return
            elif self.reduce:
                self.reduce = False
                if self.reduction_timer:
                    self.reduction_timer.cancel()
                self.reduction_timer = None
                self.direction = 'In Range'
                current_intervention = self.intervention
                self.intervention -= self.incrementation
                if self.intervention > self.max:
                    self.intervention = self.max
                    if self.intervention == current_intervention:
                        return
                if self.intervention < self.min:
                    self.intervention = self.min
                    if self.intervention == current_intervention:
                        self._logger.info(f'{self.name} infusion rate cannot be decreased further')
                        return
                if self.name in ['Insulin, Glucagon'] and not self.insulin_change and not self.increase:  # Check this
                    self._logger.info(f'Glucose is stable and in range; future boluses of {self.name} will be decreased to {self.intervention}')
                    return
            self.injection(self.syringe, self.name, self.sensor.name, value, self.intervention, self.direction, self.insulin_change, self.insulin_rate_intervention)  # Check this
            if self.increase:
                self.__evt_halt_cooldown.clear()
                self.__thread_cooldown = Thread(target=self.OnCooldown)
                self.__thread_cooldown.start()
        else:
            self._logger.info(f'No change in {self.name} infusion rate')

    def check_for_basal_insulin_change(self, value):
        if value > self.insulin_upper_glucose_limit + self.insulin_basal_rate_tolerance:
            new_glucose = 'Above Range'
        elif value < self.insulin_lower_glucose_limit - self.insulin_basal_rate_tolerance:
            new_glucose = 'Below Range'
        else:
            new_glucose = 'In Range'
        if self.old_glucose and self.old_glucose == new_glucose:
            return False, None  # Check to make sure that this doesn't go @ first
        else:
            self.old_glucose = new_glucose
            if self.old_glucose == 'Above Range':
                return True, self.insulin_basal_infusion_rate_above_range
            elif self.old_glucose == 'Below Range':
                return True, 0
            elif self.old_glucose == 'In Range':
                return True, self.insulin_basal_infusion_rate_in_range

    def injection(self, syringe, name, parameter_name, parameter, intervention_ul, direction, insulin_change, insulin_rate_intervention):
        if self.name == 'Glucagon':
            self.feedback_injection_button.Enable(False)
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
            if self.increase:
                syringe.cooldown = True
            self.feedback_injection_button.Enable(True)
        elif self.name in ['Epoprostenol', 'Phenylephrine']:
            self.feedback_injection_button.Enable(False)
            if self.increase:
                self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; increasing {name} infusion rate to {intervention_ul:.2f}')
            else:
                self._logger.info(f'Flow is {direction}; decreasing {name} infusion rate to {intervention_ul:.2f}')
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            if float(infuse_rate) == 0:
                syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.ResetSyringe()
            syringe.set_infusion_rate(intervention_ul, 'ul/min')
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            if self.increase:
                syringe.cooldown = True
            self.feedback_injection_button.Enable(True)
        elif self.name == 'Insulin':
            self.feedback_injection_button.Enable(False)
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
            syringe.ResetSyringe()
            if self.increase:
                self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; injecting {intervention_ul:.2f} uL of {name}')
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
                rate = infuse_rate
                if ml_min_rate:
                    unit = 'ml/min'
                else:
                    unit = 'ul/min'
            if insulin_change:
                rate = insulin_rate_intervention
                unit = 'ul/min'
                self._logger.info(f'{parameter_name} reads {parameter:.2f}; changing {name} basal infusion rate to {insulin_rate_intervention:.2f}')
            syringe.set_infusion_rate(rate, unit)
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
            if self.increase:
                syringe.cooldown = True
            self.feedback_injection_button.Enable(True)
