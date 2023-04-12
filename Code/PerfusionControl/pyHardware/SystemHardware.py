# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyHardware.pyAI as pyAI
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice
import pyHardware.pyDC as pyDC
import pyPerfusion.pyCDI as pyCDI
import pyPerfusion.pyPump11Elite as pyPump11Elite
import pyHardware.pyGB100 as pyGB100
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
import pyHardware.pyDC as pyDC


class SystemHardware:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        PerfusionConfig.MASTER_HALT.clear()
        self.mocks_enabled = True

        self.hw = {}

    def load_hardware_from_config(self):
        for name in ['Dev1', 'Dev2']:
            self.hw[name] = NIDAQAIDevice(name=name)
            try:
                self.hw[name].read_config()
            except pyAI.AIDeviceException as e:
                self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
                self._lgr.info(f'Loading mock for {name}')
                self.hw[name] = pyAI.AIDevice(name=name)
                self.hw[name].read_config()

            for ch in self.hw[name].ai_channels:
                self.hw[ch.name] = ch

        try:
            name = 'Arterial Gas Mixer'
            self.hw[name] = pyGB100.GasDevice(name=name)
            self.hw[name].read_config()
        except pyGB100.GasDeviceException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
            self._lgr.info(f'Loading mock for {name}')
            self.hw[name] = pyGB100.MockGasDevice(name=name)
            self.hw[name].open()

        try:
            name = 'Venous Gas Mixer'
            self.hw[name] = pyGB100.GasDevice(name=name)
            self.hw[name].read_config()
        except pyGB100.GasDeviceException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
            self._lgr.info(f'Loading mock for {name}')
            self.hw[name] = pyGB100.MockGasDevice(name=name)
            self.hw[name].read_config()

        try:
            name = 'CDI'
            self.hw[name] = pyCDI.CDI(name=name)
            self.hw[name].read_config()
        except pyCDI.CDIException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
            self._lgr.info(f'Loading mock for {name}')
            self.hw[name] = pyCDI.MockCDI(name=name)
            self.hw[name].read_config()

        pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump', 'Glucose Circuit Pump']
        for name in pump_names:
            self.hw[name] = NIDAQDCDevice(name=name)
            try:
                self.hw[name].read_config()
                self._lgr.debug(f'successfully read config for {name}')
            except pyDC.DCDeviceException as e:
                self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
                self._lgr.info(f'Loading mock for {name}')
                self.hw[name] = pyDC.DCDevice(name=name)
                self.hw[name].read_config()

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

    def start(self):
        PerfusionConfig.MASTER_HALT.clear()

        try:
            for name, device in self.hw.items():
                if type(device) != pyAI.AIChannel:
                    self._lgr.debug(f'Starting {name}')
                    device.start()
        except pyAI.AIDeviceException as e:
            self._lgr.debug('Exception caught')
            self._lgr.error(e)

    def stop(self):
        PerfusionConfig.MASTER_HALT.set()

        try:
            for name, device in self.hw.items():
                if type(device) != pyAI.AIChannel:
                    self._lgr.debug(f'Stopping {name}')
                    device.stop()
        except pyAI.AIDeviceException as e:
            self._lgr.error(e)

    def get_hw(self, name: str = None):
        self._lgr.debug(f'Getting hardware named: {name}')
        hw = self.hw.get(name, None)
        self._lgr.debug(f'Found {hw}')
        return hw


SYS_HW = SystemHardware()
