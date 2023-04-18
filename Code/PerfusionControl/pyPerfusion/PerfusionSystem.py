# -*- coding: utf-8 -*-
""" PerfusionSystem provides a unified location to handle all system hardware and sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Sensor import Sensor, CalculatedSensor, DivisionSensor


def get_object(name: str):
    params = {}
    try:
        params = PerfusionConfig.read_section('sensors', name)
    except KeyError:
        print(f'Could not find {name} in sensors.ini')
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
        print(f'Class {class_name} was not imported in PerfusionSystem')
        return None

    obj = class_(name=name)
    return obj


class PerfusionSystem:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = logging.getLogger('PerfusionSystem')
        self.sensors = {}
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
        try:
            sensor.read_config()
            self.sensors[name] = sensor
            sensor.start()
        except PerfusionConfig.HardwareException as e:
            self._lgr.error(f'Error reading config for {name}. Message {e}.')
            raise e

    def get_sensor(self, name: str):
        if name in self.sensors.keys():
            return self.sensors[name]
        else:
            return None

