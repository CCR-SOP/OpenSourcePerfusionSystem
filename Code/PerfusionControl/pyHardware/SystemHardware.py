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
import pyHardware.pyGeneric as pyGeneric
from pyHardware.pyAI import AIDevice, AIChannel, AIDeviceException
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice
from pyHardware.pyCDI import CDI, MockCDI
from pyHardware.pyPump11Elite import Pump11Elite, MockPump11Elite
from pyHardware.pyGB100 import GasDevice, MockGasDevice
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyHardware.pyDC import DCDevice
from pyHardware.pyLeviFlow import *
from pyHardware.pyPuraLevi30 import *
from pyHardware.pyCITSens import *


MOCKS = {'NIDAQAIDevice': 'AIDevice',
         'CDI': 'MockCDI',
         'Pump11Elite': 'MockPump11Elite',
         'GasDevice': 'MockGasDevice',
         'NIDAQDCDevice': 'DCDevice',
         'PuraLevi30': 'Mocki30',
         'LeviFlow': 'MockLeviFlow',
         'CITSens': 'MockCITSens'}


lgr = logging.getLogger('pyHardware.SystemHardware')


def get_object(name: str):

    params = {}
    obj = None
    try:
        params = PerfusionConfig.read_section('hardware', name)
    except KeyError:
        lgr.error(f'Could not find {name} in hardware.ini')
        return None

    try:
        class_name = params['class']
    except KeyError:
        lgr.error(f'could not find key class in section {name}')
        lgr.error(params)
        return None

    try:
        lgr.debug(f'Attempting to get {class_name}')
        class_ = globals().get(class_name, None)
        lgr.debug(f'got {class_}')
    except KeyError:
        lgr.error(f'Class {class_name} was not imported in SystemHardware')
        return None

    if class_ is None:
        lgr.error(f'Could not get object for {class_name}')
    obj = class_(name=name)

    return obj


def get_mock(name: str):
    params = PerfusionConfig.read_section('hardware', name)
    if params:
        mock_name = MOCKS[params['class']]
    else:
        return None

    try:
        class_ = globals().get(mock_name, None)
    except KeyError:
        class_ = None

    if class_ is not None:
        obj = class_(name=name)
    else:
        lgr.error(f'class {params["class"]} doesnt exist')
        obj = None
    return obj


class SystemHardware:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        PerfusionConfig.MASTER_HALT.clear()
        self.mocks_enabled = True

        self.hw = {}

    def load_all(self):
        self._lgr.info('loading all hardware')
        all_names = PerfusionConfig.get_section_names('hardware')
        for name in all_names:
            self.load(name)

    def load(self, name: str):
        self.hw[name] = get_object(name)
        try:
            self.hw[name].read_config()
            self._lgr.debug(f'cfg is {self.hw[name].cfg}')
        except pyGeneric.HardwareException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')

            self.hw[name] = get_mock(name)
            self._lgr.info(f'Loading mock {get_mock(name)}for {name}')
            self.hw[name].read_config()

        if isinstance(self.hw[name], NIDAQAIDevice) or isinstance(self.hw[name], AIDevice):
            for ch in self.hw[name].ai_channels:
                self.hw[ch.name] = ch

    def start(self):
        self._lgr.info('starting all hardware')
        PerfusionConfig.MASTER_HALT.clear()

        try:
            for name, device in self.hw.items():
                if type(device) != AIChannel and type(device) != PuraLevi30:
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
                    device.stop()
        except AIDeviceException as e:
            self._lgr.error(e)
        self._lgr.info('all hardware stopped')

    def get_hw(self, name: str = None):
        hw = self.hw.get(name, None)
        return hw


SYS_HW = SystemHardware()
