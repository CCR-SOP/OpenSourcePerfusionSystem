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
from pyHardware.pyAI import AIDevice, AIChannel, AIDeviceException
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice
from pyPerfusion.pyCDI import CDI, MockCDI
from pyPerfusion.pyPump11Elite import Pump11Elite, MockPump11Elite
from pyHardware.pyGB100 import GasDevice, MockGasDevice
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyHardware.pyDC import DCDevice

MOCKS = {'NIDAQAIDevice': 'AIDevice',
         'CDI': 'MockCDI',
         'Pump11Elite': 'MockPump11Elite',
         'GasDevice': 'MockGasDevice',
         'NIDAQDCDevice': 'DCDevice'}


def get_object(name: str):
    params = PerfusionConfig.read_section('hardware', name)
    try:
        class_ = globals().get(params['class'], None)
    except KeyError:
        params = PerfusionConfig.read_section('syringes', name)
    try:
        class_ = globals().get(params['class'], None)
    except KeyError:
        class_ = None

    if class_ is not None:
        obj = class_(name=name)
    else:
        print(f'class {params["class"]} doesnt exist')
        obj = None
    return obj


def get_mock(name: str):
    params = PerfusionConfig.read_section('hardware', name)
    if params:
        mock_name = MOCKS[params['class']]
    else:
        params = PerfusionConfig.read_section('syringes', name)
        mock_name = MOCKS[params['class']]
    try:
        class_ = globals().get(mock_name, None)
    except KeyError:
        class_ = None

    if class_ is not None:
        obj = class_(name=name)
    else:
        print(f'class {params["class"]} doesnt exist')
        obj = None
    return obj


class SystemHardware:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        PerfusionConfig.MASTER_HALT.clear()
        self.mocks_enabled = True

        self.hw = {}

    def load_hardware_from_config(self):
        for name in ['NI_Dev1', 'NI_Dev2']:
            self.hw[name] = get_object(name)
            try:
                self.hw[name].read_config()
            except PerfusionConfig.HardwareException as e:
                self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
                self._lgr.info(f'Loading mock for {name}')

                self.hw[name] = get_mock(name)
                self.hw[name].read_config()

            for ch in self.hw[name].ai_channels:
                self.hw[ch.name] = ch

        names = ['Arterial Gas Mixer', 'Venous Gas Mixer']
        for name in names:
            self.hw[name] = get_object(name)
            try:
                self.hw[name].read_config()
            except PerfusionConfig.HardwareException as e:
                self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
                self._lgr.info(f'Loading mock for {name}')
                self.hw[name] = get_mock(name)
                self.hw[name].read_config()

        try:
            name = 'CDI'
            self.hw[name] = get_object(name)
            self.hw[name].read_config()
        except PerfusionConfig.HardwareException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
            self._lgr.info(f'Loading mock for {name}')
            self.hw[name] = get_mock(name)
            self.hw[name].read_config()

        pump_names = ['Dialysate Inflow Pump', 'Dialysate Outflow Pump', 'Dialysis Blood Pump', 'Glucose Circuit Pump']
        for name in pump_names:
            self.hw[name] = get_object(name)
            try:
                self.hw[name].read_config()
                self._lgr.debug(f'successfully read config for {name}')
            except PerfusionConfig.HardwareException as e:
                self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
                self._lgr.info(f'Loading mock for {name}')
                self.hw[name] = get_mock(name)
                self.hw[name].read_config()

        all_syringe_names = PerfusionConfig.get_section_names('syringes')
        real_syringe_names = all_syringe_names[1:]
        for name in real_syringe_names:
            syringe = get_object(name)
            try:
                syringe.read_config()
                self._lgr.debug(f'read syringe {name}: {syringe}')
            except PerfusionConfig.HardwareException:
                self._lgr.debug(f'Could not open syringe. Loading mock')
                syringe = get_mock(name)
                syringe.read_config()
            self.hw[name] = syringe

    def start(self):
        PerfusionConfig.MASTER_HALT.clear()

        try:
            for name, device in self.hw.items():
                if type(device) != AIChannel:
                    self._lgr.debug(f'Starting {name}')
                    device.start()
        except AIDeviceException as e:
            self._lgr.debug('Exception caught')
            self._lgr.error(e)

    def stop(self):
        PerfusionConfig.MASTER_HALT.set()

        try:
            for name, device in self.hw.items():
                if type(device) != AIChannel:
                    self._lgr.debug(f'Stopping {name}')
                    device.stop()
        except AIDeviceException as e:
            self._lgr.error(e)

    def get_hw(self, name: str = None):
        self._lgr.debug(f'Getting hardware named: {name}')
        hw = self.hw.get(name, None)
        self._lgr.debug(f'Found {hw}')
        return hw


SYS_HW = SystemHardware()
