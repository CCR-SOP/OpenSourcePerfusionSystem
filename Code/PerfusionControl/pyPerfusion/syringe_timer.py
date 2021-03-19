# -*- coding: utf-8 -*-
"""
@author: Allen Luna
General code for initiating syringe injections based on a specific system parameter
"""
import wx
from pyHardware.PHDserial import PHDserial

class SyringeTimer(wx.Panel):
    def __init__(self, parent, name, COM, baud, threshold_value, tolerance, sensor):
        self.name = name
        self.COM = COM
        self.baud = baud
        self.threshold_value = threshold_value
        self.tolerance = tolerance
        self.sensor = sensor
        self.syringe = PHDserial()

        wx.Panel.__init__(self, parent, -1)

        self.timer_injection = wx.Timer(self, id=0)
        self.Bind(wx.EVT_TIMER, self.OnTimer, id=0)

        self.timer_reset = wx.Timer(self, id=1)
        self.Bind(wx.EVT_TIMER, self.OnResetTimer, id=1)

        self.connect()

    def connect(self):
        self.syringe.open(self.COM, self.baud)
        self.syringe.ResetSyringe()
        self.syringe.syringe_configuration()

    def start_injection_timer(self, time_ms):
        self.timer_injection.Start(time_ms, wx.TIMER_CONTINUOUS)

    def stop_injection_timer(self):
        self.timer_injection.Stop()

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
            if glucose > (self.threshold_value + self.tolerance) and glucose != 5000:
                if not self.syringe.cooldown:
                    diff = glucose - (self.threshold_value + self.tolerance)
                    injection_volume = diff / 25
                    self.injection(self.syringe, self.name, 'Glucose', glucose, injection_volume, direction='high')
                    self.timer_reset.Start(30000, wx.TIMER_CONTINUOUS)
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
                    self.timer_reset.Start(30000, wx.TIMER_CONTINUOUS)
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
                    self.timer_reset.Start(30000, wx.TIMER_CONTINUOUS)
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
                    self.timer_reset.Start(30000, wx.TIMER_CONTINUOUS)
                else:
                    print(f'Flow is {flow:.2f} , which is too low; however, epoprostenol injections are currently frozen')
            else:
                print('Flow does not need to be modulated by epoprostenol')

    def injection(self, syringe, name, parameter_name, parameter, volume, direction):
        print(f'{parameter_name} is {parameter:.2f} , which is too {direction}; injecting {volume:.2f} mL of {name}')
        syringe.set_target_volume(volume, 'ml')
        syringe.infuse()
        syringe.reset = True
        syringe.cooldown = True

