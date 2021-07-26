# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
from pyHardware.PHDserial import PHDserial
from threading import Thread, Event
import time
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
        self.basal = None
        self.wait = None

        LP_CFG.set_base(basepath='~/Documents/LPTEST')
        LP_CFG.update_stream_folder()

        self.__thread_timer_injection = None
        self.__evt_halt_injection = Event()
        self.__thread_timer_reset = None
        self.__evt_halt_reset = Event()

        self.connect()

    def connect(self):
        self.syringe.open(self.COM, self.baud)
        self.syringe.ResetSyringe()
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
        while not self.__evt_halt_injection.wait(5.0):
            self.check_for_injection()

    def OnResetTimer(self):
        while not self.__evt_halt_reset.wait(15.0):
            self.syringe.cooldown = False
            self.__evt_halt_reset.set()
            self.__thread_timer_reset = None
            return

    def check_for_injection(self):
        if self.name == 'Insulin':
            t, glucose = self.sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
            glucose = float(glucose)
            if glucose > (self.threshold_value + self.tolerance) and glucose != 5000:
                if not self.syringe.cooldown:
                    diff = glucose - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 100
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='high')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Glucose is {glucose:.2f} , which is too high; however, insulin injections are currently frozen')
            else:
                print('Glucose does not need to be modulated by insulin')
        elif self.name == 'Glucagon':
            t, glucose = self.sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
            glucose = float(glucose)
            if glucose < (self.threshold_value - self.tolerance) and glucose != 0:
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - glucose
                    injection_volume = diff / 100
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='low')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Glucose is {glucose:.2f} , which is too low; however, glucagon injections are currently frozen')
            else:
                print('Glucose does not need to be modulated by glucagon')
        elif self.name == 'Phenylephrine':
            t, flow = self.sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
            flow = float(flow)
            if flow > (self.threshold_value + self.tolerance):
                if not self.syringe.cooldown:
                    diff = flow - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 100
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='high')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Flow is {flow:.2f} , which is too high; however, phenylephrine injections are currently frozen')
            else:
                print('Flow does not need to be modulated by phenylephrine')
        elif self.name == 'Epoprostenol':
            t, flow = self.sensor.get_file_strategy('Raw').retrieve_buffer(0, 1)
            flow = float(flow)
            if flow < (self.threshold_value - self.tolerance):
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - flow
                    injection_volume = diff / 100
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='low')
                    self.__evt_halt_reset.clear()
                    self.__thread_timer_reset = Thread(target=self.OnResetTimer)
                    self.__thread_timer_reset.start()
                else:
                    print(f'Flow is {flow:.2f} , which is too low; however, epoprostenol injections are currently frozen')
            else:
                print('Flow does not need to be modulated by epoprostenol')
        else:
            print('Perfusion-condition informed syringe injections are not supported for this syringe')

    def injection(self, syringe, name, parameter_name, parameter, volume, direction):
        print(f'{parameter_name} is {parameter:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        if self.basal:
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.stop(1111, infuse_rate, ml_volume, ml_min_rate)
        syringe.ResetSyringe()
        syringe.set_target_volume(volume, 'ml')
        syringe.set_infusion_rate(25, 'ml/min')
        syringe.infuse(volume, 25, True, True)
        self.wait = True
        t = time.perf_counter()
        while self.wait:
            x = time.perf_counter()
            if ((x - t) - 4) > (volume / 25):
                self.wait = False
        syringe.reset_target_volume()
        if self.basal:
            if ml_min_rate:
                unit = 'ml/min'
            else:
                unit = 'ul/min'
            syringe.set_infusion_rate(infuse_rate, unit)
            infuse_rate, ml_min_rate, ml_volume = syringe.get_stream_info()
            syringe.infuse(2222, infuse_rate, ml_volume, ml_min_rate)
        syringe.cooldown = True

