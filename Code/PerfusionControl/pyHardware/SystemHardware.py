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
from pyHardware.pyCDI import CDI, MockCDI
from pyHardware.pyPump11Elite import Pump11Elite, MockPump11Elite
from pyHardware.pyGB100 import GasDevice, MockGasDevice
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyHardware.pyDC import DCDevice

MOCKS = {'NIDAQAIDevice': 'AIDevice',
         'CDI': 'MockCDI',
         'Pump11Elite': 'MockPump11Elite',
         'GasDevice': 'MockGasDevice',
         'NIDAQDCDevice': 'DCDevice'}


def get_object(name: str):
    params = {}
    try:
        params = PerfusionConfig.read_section('hardware', name)
    except KeyError:
        print(f'Could not find {name} in hardware.ini')
        return None

    try:
        class_name = params['class']
    except KeyError:
        print(f'could not find key class in section {name}')
        print(params)
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
        self._lgr.info('loading all hardware')
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

        if isinstance(self.hw[name], NIDAQAIDevice) or isinstance(self.hw[name], AIDevice):
            for ch in self.hw[name].ai_channels:
                self.hw[ch.name] = ch

    def start(self):
        self._lgr.info('starting all hardware')
        PerfusionConfig.MASTER_HALT.clear()

        try:
            for name, device in self.hw.items():
                if type(device) != AIChannel:
                    self._lgr.debug(f'Starting {name}')
                    device.start()
        except AIDeviceException as e:
            self._lgr.debug('Exception caught')
            self._lgr.error(e)
<<<<<<< HEAD
=======
        for syringe in self.syringes:
            syringe.start()

        if self.cdi:
            self.cdi.start()

        if self.ha_mixer:
            self.ha_mixer.start()
        if self.pv_mixer:
            self.pv_mixer.start()

        if self.pump1:
            self.pump1.start()
        if self.pump2:
            self.pump2.start()
        if self.pump3:
            self.pump3.start()

        if self.leviflow1:
            self.leviflow1.start()
        if self.leviflow2:
            self.leviflow2.start()

        if self.mocks_enabled:
            self.mock_device.start()
            self.mock_cdi.start()
            self.mock_syringe.start()
>>>>>>> 6e7614e (update panel and mocks for working example (w/o hardware))

    def stop(self):
        PerfusionConfig.MASTER_HALT.set()

        try:
            for name, device in self.hw.items():
                if type(device) != AIChannel:
                    device.stop()
        except AIDeviceException as e:
            self._lgr.error(e)
<<<<<<< HEAD
        self._lgr.info('all hardware stopped')

    def get_hw(self, name: str = None):
        hw = self.hw.get(name, None)
=======

        for syringe in self.syringes:
            syringe.stop()

        if self.cdi:
            self.cdi.stop()

        if self.ha_mixer:
            self.ha_mixer.stop()
        if self.pv_mixer:
            self.pv_mixer.stop()

        if self.pump1:
            self.pump1.stop()
        if self.pump2:
            self.pump2.stop()
        if self.pump3:
            self.pump3.stop()

        if self.leviflow1:
            self.leviflow1.stop()
        if self.leviflow2:
            self.leviflow2.stop()

        if self.mocks_enabled:
            self.mock_device.stop()
            self.mock_cdi.stop()
            self.mock_syringe.stop()

    def get_hw(self, name: str = None):
        self._lgr.debug(f'Getting hardware named: {name}')
        hw = None
        if hw is None:
            if name == 'Glucose Circuit Pump':
                hw = self.glucose_circuit
            elif name == 'Dialysate Inflow Pump':
                hw = self.dialysate_inflow
            elif name == 'Dialysate Outflow Pump':
                hw = self.dialysate_outflow
            elif name == 'Dialysis Blood Pump':
                hw = self.dialysis_blood
            elif name == 'Arterial Gas Mixer':
                hw = self.ha_mixer
            elif name == 'Venous Gas Mixer':
                hw = self.pv_mixer
            elif name == 'CDI':
                hw = self.cdi
            elif name == 'Pump 1':
                hw = self.pump1
            elif name == 'Pump 2':
                hw = self.pump2
            elif name == 'Pump 3':
                hw = self.pump3
            elif name == 'LeviFlow1':
                hw = self.leviflow1
            elif name == 'LeviFlow2':
                hw = self.leviflow2

        if hw is None:
            hw = self.ni_dev1.ai_channels.get(name, None)
        if hw is None:
            hw = self.ni_dev2.ai_channels.get(name, None)
        if hw is None:
            hw = next((syringe for syringe in self.syringes if syringe.name == name), None)

        if self.mocks_enabled:
            if hw is None:
                hw = self.mock_device.ai_channels.get(name, None)
            if hw is None:
                if name == "mock_cdi":
                    hw = self.mock_cdi
                elif name == "mock_syringe":
                    hw = self.mock_syringe
        self._lgr.debug(f'Found {hw}')
>>>>>>> 6e7614e (update panel and mocks for working example (w/o hardware))
        return hw


SYS_HW = SystemHardware()
