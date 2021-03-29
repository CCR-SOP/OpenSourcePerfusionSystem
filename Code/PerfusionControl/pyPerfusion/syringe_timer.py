# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
from pyHardware.PHDserial import PHDserial
from threading import Thread, Event
import pyPerfusion.PerfusionConfig as LP_CFG

class SyringeTimer:
    def __init__(self, name, COM, baud, threshold_value, tolerance, sensor):
        self.name = name
        self.COM = COM
        self.baud = baud
        self.threshold_value = threshold_value
        self.tolerance = tolerance
        self.sensor = sensor
        self.syringe = PHDserial(self.name)

        self.__thread_timer_injection = None
        self.__evt_halt_injection = Event()
        self.__thread_timer_reset = None
        self.__evt_halt_reset = Event()

        self.connect()

    def connect(self):
        self.syringe.open(self.COM, self.baud)
        self.syringe.ResetSyringe()
        self.syringe.syringe_configuration()
        self.syringe.open_stream(LP_CFG.LP_PATH['stream'])
        self.syringe.start_stream()

    def start_injection_timer(self):
        self.__evt_halt_injection.clear()
        self.__thread_timer_injection = Thread(target=self.OnTimer)
        self.__thread_timer_injection.start()

    def stop_injection_timer(self):
        if self.__thread_timer_injection and self.__thread_timer_injection.is_alive():
            self.__evt_halt_injection.set()
            self.__thread_timer_injection.join(2.0)
            self.__thread_timer_injection = None
        if self.__thread_timer_reset and self.__thread_timer_reset.is_alive():
            self.syringe.cooldown = False
            self.__evt_halt_reset.set()
            self.__thread_timer_reset.join(2.0)
            self.__thread_timer_reset = None

    def OnTimer(self):
        while not self.__evt_halt_injection.wait(10.0):
            if self.syringe.reset:
                self.syringe.ResetSyringe()
                self.syringe.reset = False
            self.check_for_injection()

    def OnResetTimer(self):
        while not self.__evt_halt_reset.wait(30.0):
            self.syringe.cooldown = False
            self.__evt_halt_reset.set()
            self.__thread_timer_reset = None
            return

    def check_for_injection(self):
        if self.name == 'Insulin':
            glucose = float(self.sensor.get_current())
            if glucose > (self.threshold_value + self.tolerance) and glucose != 5000:
                if not self.syringe.cooldown:
                    diff = glucose - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='high')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Glucose is {glucose:.2f} , which is too high; however, insulin injections are currently frozen')
            else:
                print('Glucose does not need to be modulated by insulin')
        elif self.name == 'Glucagon':
            glucose = float(self.sensor.get_current())
            if glucose < (self.threshold_value - self.tolerance) and glucose != 0:
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - glucose
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='low')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Glucose is {glucose:.2f} , which is too low; however, glucagon injections are currently frozen')
            else:
                print('Glucose does not need to be modulated by glucagon')
        elif self.name == 'Phenylephrine':
            flow = float(self.sensor.get_current())
            if flow > (self.threshold_value + self.tolerance):
                if not self.syringe.cooldown:
                    diff = flow - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='high')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Flow is {flow:.2f} , which is too high; however, phenylephrine injections are currently frozen')
            else:
                print('Flow does not need to be modulated by phenylephrine')
        elif self.name == 'Epoprostenol':
            flow = float(self.sensor.get_current())
            if flow < (self.threshold_value - self.tolerance):
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - flow
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='low')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Flow is {flow:.2f} , which is too low; however, epoprostenol injections are currently frozen')
            else:
                print('Flow does not need to be modulated by epoprostenol')

    def injection(self, syringe, name, parameter_name, parameter, volume, direction):
        print(f'{parameter_name} is {parameter:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        syringe.set_target_volume(volume, 'ml')
        infusion_rate = syringe.get_infusion_rate()
        syringe.target_infuse(volume, infusion_rate)
        syringe.reset = True
        syringe.cooldown = True


