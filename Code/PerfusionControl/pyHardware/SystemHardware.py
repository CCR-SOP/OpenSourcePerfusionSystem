# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import time
from time import perf_counter_ns

import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig


class SystemHardware:
    def __init__(self):
        self.ni_dev1 = NIDAQAIDevice()
        self.ni_dev2 = NIDAQAIDevice()
        self.mock_device = pyAI.AIDevice()
        self.acq_start = 0

    def load_hardware_from_config(self):
        self.ni_dev1.cfg = AINIDAQDeviceConfig(name='Dev1')
        self.ni_dev1.read_config()
        self.ni_dev2.cfg = AINIDAQDeviceConfig(name='Dev2')
        self.ni_dev2.read_config()
        self.mock_device.cfg = pyAI.AIDeviceConfig(name='FakeEvents')
        self.mock_device.read_config()

    def start(self):
        self.ni_dev1.start()
        self.ni_dev2.start()
        self.mock_device.start()
        self.acq_start = perf_counter_ns()

    def stop(self):
        self.ni_dev1.stop()
        self.ni_dev2.stop()
        self.mock_device.stop()

    def get_hw(self, name: str):
        hw = self.ni_dev1.ai_channels.get(name, None)
        if hw is None:
            hw = self.ni_dev2.ai_channels.get(name, None)
        if hw is None:
            hw = self.mock_device.ai_channels.get(name, None)
        return hw

    def get_elapsed_time_ms(self):
        return int((time.perf_counter_ns() - self.acq_start) / 1_000_000)

SYS_HW = SystemHardware()
