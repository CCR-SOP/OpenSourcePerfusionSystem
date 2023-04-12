# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice, AINIDAQDeviceConfig
import pyPerfusion.pyCDI as pyCDI
import pyPerfusion.pyPump11Elite as pyPump11Elite
import pyHardware.pyGB100 as pyGB100
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC


class SystemHardware:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)
        PerfusionConfig.MASTER_HALT.clear()
        self.mocks_enabled = True

        # Preload the NIDAQ devices as the analog inputs channels
        # need this to exist anyway
        self.ni_dev1 = NIDAQAIDevice(name='Dev1')
        self.ni_dev2 = NIDAQAIDevice(name='Dev2')

        self.hw = {}
        self.mocks = {}

    def load_hardware_from_config(self):
        try:
            self.ni_dev1.cfg = AINIDAQDeviceConfig()
            self.ni_dev1.read_config()
            for ch in self.ni_dev1.ai_channels:
                self.hw[ch.name] = ch

            self.ni_dev2.cfg = AINIDAQDeviceConfig()
            self.ni_dev2.read_config()
            for ch in self.ni_dev2.ai_channels:
                self.hw[ch.name] = ch

        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

        name = ''
        try:
            name = 'Arterial Gas Mixer'
            self.hw[name] = pyGB100.GasDevice(name=name)
            self.hw[name].read_config()
        except Exception as e:
            self._lgr.error(f"Error trying to create {name}")
            self._lgr.error(f"GasDevice exception: {e}")

        try:
            name = 'Venous Gas Mixer'
            self.hw[name] = pyGB100.GasDevice(name=name)
            self.hw[name].read_config()
        except Exception as e:
            self._lgr.error(f"Error trying to create {name}")
            self._lgr.error(f"GasDevice exception: {e}")

        try:
            name = 'CDI'
            self.hw[name] = pyCDI.CDIStreaming(name=name)
            self.hw[name].read_config()
        except Exception as e:
            self._lgr.error(f'Error trying to create {name}')
            self._lgr.error(f'CDI exception: {e}')

        try:
            pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump', 'Glucose Circuit Pump']
            for name in pump_names:
                self.hw[name] = NIDAQDCDevice(name=name)
                self.hw[name].read_config()
        except pyDC.DCDeviceException as e:
            self._lgr.error(e)

        all_syringe_names = PerfusionConfig.get_section_names('syringes')
        real_syringe_names = all_syringe_names[1:]
        for name in real_syringe_names:
            syringe = pyPump11Elite.Pump11Elite(name=name)
            try:
                syringe.read_config()
                self._lgr.debug(f'read syringe {name}: {syringe}')
            except pyPump11Elite.Pump11EliteException:
                self._lgr.debug(f'Could not open syringe. Loading mock')
                syringe = pyPump11Elite.MockPump11Elite(name=name)
                syringe.read_config()
            self.hw[name] = syringe

    def load_mocks(self):


        name = 'FakeEvents'
        self.mocks[name] = pyAI.AIDevice(name=name)
        self.mocks[name].read_config()
        for ch in self.mocks[name].ai_channels:
            self.mocks[ch.name] = ch

        name = 'mock_cdi'
        self.mocks[name] = pyCDI.MockCDI(name=name)
        self.mocks[name] .read_config()

        name = 'mock_syringe'
        self.mocks[name] = pyPump11Elite.MockPump11Elite(name=name)
        self.mocks[name].read_config()

        name = 'Arterial Gas Mixer'
        self.mocks[name] = pyGB100.GasDevice(name=name)
        self.mocks[name].hw = pyGB100.MockGB100()

        name = 'Venous Gas Mixer'
        self.mocks[name] = pyGB100.GasDevice(name=name)
        self.mocks[name].hw = pyGB100.MockGB100()

    def start(self):
        PerfusionConfig.MASTER_HALT.clear()

        self.ni_dev1.start()
        self.ni_dev2.start()
        try:
            for name, device in self.hw.items():
                if type(device) != pyAI.AIChannel:
                    self._lgr.debug(f'Starting {name}')
                    device.start()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

        if self.mocks_enabled:
            try:
                for name, device in self.mocks.items():
                    self._lgr.debug(f'Starting {name}')
                    device.start()
            except pyAI.AIDeviceException as e:
                self._lgr.error(e)

    def stop(self):
        PerfusionConfig.MASTER_HALT.set()

        self.ni_dev1.stop()
        self.ni_dev2.stop()
        try:
            for name, device in self.hw.items():
                if type(device) != pyAI.AIChannel:
                    self._lgr.debug(f'Stopping {name}')
                    device.stop()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

        if self.mocks_enabled:
            try:
                for name, device in self.mocks.items():
                    if type(device) != pyAI.AIChannel:
                        self._lgr.debug(f'Starting {name}')
                        device.stop()
            except pyAI.AIDeviceException as e:
                self._lgr.error(e)

    def get_hw(self, name: str = None):
        self._lgr.debug(f'Getting hardware named: {name}')
        hw = self.hw.get(name, None)
        if hw is None and self.mocks_enabled:
            hw = self.mocks.get(name, None)
        self._lgr.debug(f'Found {hw}')
        return hw


SYS_HW = SystemHardware()
