# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
import pyPerfusion.PerfusionConfig as PerfusionConfig


class SystemHardware:
    def __init__(self):
        self.ni_dev1 = NIDAQAIDevice()
        self.ni_dev2 = NIDAQAIDevice()
        self.load_hardware_from_config()

    def load_hardware_from_config(self):
        self.ni_dev1.cfg = AINIDAQDeviceConfig(name='Dev1')
        self.ni_dev1.read_config()
        self.ni_dev2.cfg = AINIDAQDeviceConfig(name='Dev2')
        self.ni_dev2.read_config()

    def get_hw(self, name: str):
        ai_ch = self.ni_dev1.ai_channels.get(name, 'None')
        if ai_ch is None:
            ai_ch = self.ni_dev2.ai_channels.get(name, 'None')
        return ai_ch


SYS_HW = SystemHardware()
