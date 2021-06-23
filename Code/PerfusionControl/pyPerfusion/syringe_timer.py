# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
from threading import Thread, Event
import logging
import time

class SyringeTimer:
    def __init__(self, name, sensor=None, syringe=None):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.sensor = sensor
        self.syringe = syringe
        self.threshold_value = None
        self.tolerance = None
        self.injection_volume = None
        self.time_between_checks = None
        self.cooldown_time = None
        self.basal = None
        self.wait = None

        self.__thread_boluses = None
        self.__evt_halt_boluses = Event()
        self.__thread_cooldown = None
        self.__evt_halt_cooldown = Event()

    def start_bolus_injections(self):
        self.__evt_halt_boluses.clear()
        self.__thread_boluses = Thread(target=self.OnBolusLoop)
        self.__thread_boluses.start()

    def stop_bolus_injections(self):
        if self.__thread_boluses and self.__thread_boluses.is_alive():
            self.__evt_halt_boluses.set()
            self.__thread_boluses.join(2.0)
            self.__thread_boluses = None
        if self.__thread_cooldown and self.__thread_cooldown.is_alive():
            self.syringe.cooldown = False
            self.__evt_halt_cooldown.set()
            self.__thread_cooldown.join(2.0)
            self.__thread_cooldown = None

    def OnBolusLoop(self):
        while not self.__evt_halt_boluses.wait(self.time_between_checks):
            self.check_for_injection()

    def OnCooldown(self):
        self.__evt_halt_cooldown.wait(self.cooldown_time)
        self.syringe.cooldown = False
        self.__evt_halt_cooldown.set()
        self.__thread_cooldown = None

    def check_for_injection(self):
        injection = False
        if self.sensor:
            value = float(self.sensor.get_current())
        else:
            self._logger.error('Perfusion-condition informed syringe injections are not supported for this syringe')
            return
        if self.name in ['Insulin', 'Phenylephrine']:
            if value > (self.threshold_value + self.tolerance) and value != -5000:
                if self.syringe.cooldown:
                    self._logger.info(f'A {self.name} infusion is needed, but is currently frozen')
                else:
                    injection = True
                    direction = 'high'
            else:
                self._logger.info(f'No {self.name} infusion is needed')
        elif self.name in ['Glucagon (Unasyn)', 'Epoprostenol']:
            if value < (self.threshold_value - self.tolerance) and value != -10000:
                if self.syringe.cooldown:
                    self._logger.info(f'A {self.name} infusion is needed, but is currently frozen')
                else:
                    injection = True
                    direction = 'low'
            else:
                self._logger.info(f'No {self.name} infusion is needed')
        if injection:
            self.injection(self.syringe, self.name, self.sensor.name, value, self.injection_volume/1000, direction)
            self.__evt_halt_cooldown.clear()
            self.__thread_cooldown = Thread(target=self.OnCooldown)
            self.__thread_cooldown.start()

    def injection(self, syringe, name, parameter_name, parameter, volume, direction):
        self._logger.info(f'{parameter_name} reads {parameter:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        if self.basal:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(-1, infuse_rate, ml_volume, ml_min_rate)
        syringe.ResetSyringe()
        syringe.set_target_volume(volume, 'ml')
        syringe.set_infusion_rate(25, 'ml/min')
        syringe.infuse(volume, 25, True, True)
        self.wait = True
        time.sleep(60*volume/25)
        while self.wait:
            response = float(self.syringe.get_infused_volume().split(' ')[0])
            unit = self.syringe.get_infused_volume().split(' ')[1]
            if 'ul' in unit:
                response = response / 1000
            if response >= volume:
                self.wait = False
        syringe.reset_target_volume()
        if self.basal:
            if ml_min_rate:
                unit = 'ml/min'
            else:
                unit = 'ul/min'
            syringe.set_infusion_rate(infuse_rate, unit)
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(-2, infuse_rate, ml_volume, ml_min_rate)
        syringe.cooldown = True
