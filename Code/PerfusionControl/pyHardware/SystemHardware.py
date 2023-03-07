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
import pyPerfusion.pyCDI as pyCDI
import pyPerfusion.pyPump11Elite as pyPump11Elite



class SystemHardware:
    def __init__(self):
        self.ni_dev1 = NIDAQAIDevice()
        self.ni_dev2 = NIDAQAIDevice()
        self.mock_device = pyAI.AIDevice()
        self.mock_cdi = pyCDI.MockCDI('mock_cdi')
        self.mock_syringe = pyPump11Elite.MockPump11Elite(name='mock_syringe')
        self.acq_start = 0

    def load_hardware_from_config(self):
        self.ni_dev1.cfg = AINIDAQDeviceConfig(name='Dev1')
        self.ni_dev1.read_config()
        self.ni_dev2.cfg = AINIDAQDeviceConfig(name='Dev2')
        self.ni_dev2.read_config()
        self.mock_device.cfg = pyAI.AIDeviceConfig(name='FakeEvents')
        self.mock_device.read_config()
        self.mock_cdi.cfg = pyCDI.CDIConfig(name='mock_cdi')
        self.mock_cdi.read_config()
        self.mock_syringe.cfg = pyPump11Elite.SyringeConfig(name='mock_syringe')
        self.mock_syringe.read_config()

    def start(self):
        self.ni_dev1.start()
        self.ni_dev2.start()
        self.mock_device.start()
        self.mock_cdi.start()
        self.mock_syringe.start()
        self.acq_start = perf_counter_ns()

    def stop(self):
        self.ni_dev1.stop()
        self.ni_dev2.stop()
        self.mock_device.stop()
        self.mock_cdi.stop()

    def get_hw(self, name: str):
        hw = self.ni_dev1.ai_channels.get(name, None)
        if hw is None:
            hw = self.ni_dev2.ai_channels.get(name, None)
        if hw is None:
            hw = self.mock_device.ai_channels.get(name, None)
        if hw is None:
            if name == "mock_cdi":
                hw = self.mock_cdi
            elif name == "mock_syringe":
                hw = self.mock_syringe
        return hw

    def get_elapsed_time_ms(self):
        return int((time.perf_counter_ns() - self.acq_start) / 1_000_000)

SYS_HW = SystemHardware()
