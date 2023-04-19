# -*- coding: utf-8 -*-
""" PerfusionSystem provides a unified location to handle all system hardware and sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW

# Do NOT delete anything below this line. All objects are required for auto-loading
from pyPerfusion.Sensor import *
from pyPerfusion.pyAutoGasMixer import *
from pyPerfusion.pyAutoDialysis import *
from pyPerfusion.pyAutoSyringe import *


def get_object(name: str, config: str ='sensors'):
    params = {}
    try:
        params = PerfusionConfig.read_section(config, name)
    except KeyError:
        logging.getLogger().error(f'Could not find {name} in {config}.ini')
        return None

    try:
        class_name = params['class']
    except KeyError:
        logging.getLogger().error(f'could not find key class in section {name}. Params={params}')
        return None

    try:
        class_ = globals().get(class_name, None)
    except KeyError:
        logging.getLogger().error(f'Class {class_name} was not imported in PerfusionSystem')
        return None

    obj = class_(name=name)
    return obj


class PerfusionSystem:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = logging.getLogger('PerfusionSystem')
        self.sensors = {}
        self.automations = {}
        self.is_opened = False

    def open(self):
        SYS_HW.load_all()
        SYS_HW.start()
        self.is_opened = True

    def close(self):
        SYS_HW.stop()
        for sensor in self.sensors.values():
            sensor.stop()
            if sensor.hw:
                sensor.hw.stop()
        self.is_opened = False
        self._lgr.info('PerfusionSystem is closed')

    def load_all(self):
        if not self.is_opened:
            self.open()
        all_names = PerfusionConfig.get_section_names('sensors')
        for name in all_names:
            self.load(name)

    def load(self, name: str):
        if not self.is_opened:
            self.open()
        if name in self.sensors.keys():
            self._lgr.error(f'Sensor {name} already loaded')
            return

        self._lgr.info(f'Loading {name}')
        sensor = get_object(name)
        sensor.read_config()
        self.sensors[name] = sensor
        sensor.start()

    def load_automations(self):
        all_names = PerfusionConfig.get_section_names('automations')
        for name in all_names:
            automation = get_object(name, config='automations')
            automation.read_config()

            if isinstance(automation, AutoGasMixer):
                automation.gas_device = self.get_sensor(automation.cfg.gas_device).hw
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoDialysis):
                automation.pump = self.get_sensor(automation.cfg.pump)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoSyringe):
                automation.device = self.get_sensor(automation.cfg.device)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            self.automations[name] = automation

    def get_sensor(self, name: str):
        return self.sensors.get(name, None)

    def get_automation(self, name: str):
        return self.automations.get(name, None)
