# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
import wx
from pyHardware.PHDserial import PHDserial

class SyringeTimer(wx):
    def __init__(self, name, COM, baud, threshold_value, tolerance, sensor):
        self.name = name
        self.COM = COM
        self.baud = baud
        self.threshold_value = threshold_value
        self.tolerance = tolerance
        self.sensor = sensor
        self.syringe = PHDserial()

        self.timer_injection = wx.Timer(self, id=0)
        self.Bind(wx.EVT_TIMER, self.OnTimer, id=0)

        self.timer_reset = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnResetTimer, id=1)

        self.open()

    def open(self):
        self.syringe.open(self.COM, self.baud)
        self.syringe.ResetSyringe()
        self.syringe.syringe_configuration()
        self.timer_injection.Start(30000, wx.TIMER_CONTINUOUS)  # Check to see if this executes prior to syringes being ready for injections

    def OnTimer(self, event):
        if event.GetId() == self.timer_injection.GetId():
            if self.syringe.reset:
                self.syringe.ResetSyringe()
                self.syringe.reset = False
            self.check_for_injection()

    def OnResetTimer(self, event):
        if event.GetId() == self.timer_reset.GetId():
            self.syringe.cooldown = False
            self.timer_reset.Stop()

    def check_for_injection(self):
        if self.name == 'Insulin':
            glucose = float(self.sensor.get_current())
            if glucose > (self.threshold_value + self.tolerance):
                if not self.syringe.cooldown:
                    diff = glucose - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='high')
                    self.timer_reset.Start(60000, wx.TIMER_CONTINUOUS)
                else:
                    print(f'Glucose is {glucose:.2f} , which is too high; however, insulin injections are currently frozen')
        elif self.name == 'Glucagon':
            glucose = float(self.sensor.get_current())
            if glucose < (self.threshold_value - self.tolerance):
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - glucose
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='low')
                    self.timer_reset.Start(60000, wx.TIMER_CONTINUOUS)
                else:
                    print(f'Glucose is {glucose:.2f} , which is too low; however, glucagon injections are currently frozen')
        elif self.name == 'Phenylephrine':
            flow = float(self.sensor.get_current())
            if flow > (self.threshold_value + self.tolerance):
                if not self.syringe.cooldown:
                    diff = flow - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='high')
                    self.timer_reset.Start(60000, wx.TIMER_CONTINUOUS)
                else:
                    print(f'Flow is {flow:.2f} , which is too high; however, phenylephrine injections are currently frozen')
        elif self.name == 'Epoprostenol':
            flow = float(self.sensor.get_current())
            if flow < (self.threshold_value - self.tolerance):
                if not self.syringe.cooldown:
                    diff = (self.threshold_value - self.tolerance) - flow
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Flow', flow, injection_volume, direction='low')
                    self.timer_reset.Start(60000, wx.TIMER_CONTINUOUS)
                else:
                    print(f'Flow is {flow:.2f} , which is too low; however, epoprostenol injections are currently frozen')

    def injection(self, syringe, name, parameter_name, parameter, volume, direction):
        print(f'{parameter_name} is {parameter:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        syringe.set_target_volume(volume, 'ml')
        syringe.infuse()
        syringe.reset = True
        syringe.cooldown = True

    def stop_injection_timer(self):
        self.timer_injection.Stop()

    def start_injection_timer(self, time):
        self.timer_injection.Start(time, wx.TIMER_CONTINUOUS)

