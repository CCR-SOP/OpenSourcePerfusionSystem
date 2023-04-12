# -*- coding: utf-8 -*-
""" SystemHardware provides a unified location to handle all system hardware

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.pyAI import AIDevice, AIChannel, AIDeviceException
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice

MOCKS = {'NIDAQAIDevice': 'AIDevice',
         'CDI': 'MockCDI',
         'Pump11Elite': 'MockPump11Elite',
         'GasDevice': 'MockGasDevice',
         'NIDAQDCDevice': 'DCDevice'}


def get_object(name: str):
    try:
        params = PerfusionConfig.read_section('hardware', name)
    except KeyError:
        print(f'Could not find {name} in hardware.ini')
        return None

    try:
        class_name = params['class']
    except KeyError:
        print(f'could not find key class in section {name}')
        return None

    try:
        class_ = globals().get(class_name, None)
    except KeyError:
        print(f'Class {class_name} was not imported in SystemHardware')
        return None

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

    def load_all(self):
        all_names = PerfusionConfig.get_section_names('hardware')

        for name in all_names:
            self.load(name)

    def load(self, name: str):
        self.hw[name] = get_object(name)
        try:
            self.hw[name].read_config()
        except PerfusionConfig.HardwareException as e:
            self._lgr.error(f'Error opening {name}. Message {e}. Loading mock')
            self._lgr.info(f'Loading mock for {name}')

            self.hw[name] = get_mock(name)
            self.hw[name].read_config()

        self._lgr.debug(f'hw type is {type(self.hw[name])}')
        if isinstance(self.hw[name], NIDAQAIDevice) or isinstance(self.hw[name], AIDevice):
            for ch in self.hw[name].ai_channels:
                self._lgr.debug(f'adding channel {ch.name}')
                self.hw[ch.name] = ch

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
