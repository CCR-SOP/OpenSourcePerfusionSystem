# -*- coding: utf-8 -*-
""" PerfusionSystem provides a unified location to handle all system hardware and sensors

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import inspect

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW

# Do NOT delete anything below this line. All objects are required for auto-loading
from pyPerfusion.Sensor import *
from pyPerfusion.pyAutoGasMixer import *
from pyPerfusion.pyAutoDialysis import *
from pyPerfusion.pyAutoSyringe import *
from pyPerfusion.pyAutoFlow import *
from pyPerfusion.Strategy_ReadWrite import *
from pyPerfusion.Strategy_Processing import *
from pyPerfusion.pyAutoFlow import *


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

    try:
        obj = class_(name=name)
    except TypeError:
        obj = None
        logging.getLogger().error(f'Class {class_name} could be created in PerfusionSystem')
    return obj


class PerfusionSystem:
    def __init__(self, name: str = "Standard"):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.sensors = {}
        self.automations = {}
        self.is_opened = False
        self.config_name = 'sensors'
        self._lgr.debug(f'create Perfusion System {self.name}')

    def open(self):
        SYS_HW.load_all()
        SYS_HW.start()
        self.is_opened = True

    def close(self):
        self._lgr.info('Closing PerfusionSystem')
        SYS_HW.stop()
        for sensor in self.sensors.values():
            sensor.stop()
            if sensor.hw:
                sensor.hw.stop()
            sensor.close()
        for automation in self.automations.values():
            automation.stop()

        self.is_opened = False
        self._lgr.info('PerfusionSystem is closed')

    def load_all(self):
        if not self.is_opened:
            self.open()
        all_names = PerfusionConfig.get_section_names(self.config_name)
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
        sensor = self.create_config(sensor)
        # self._lgr.debug(f'created config {sensor.cfg}')
        self.sensors[name] = sensor
        if isinstance(sensor, CalculatedSensor):
            sensor.reader = self.get_sensor(sensor.cfg.sensor_name).get_reader(sensor.cfg.sensor_strategy)
        elif isinstance(sensor, DivisionSensor):
            sensor.reader_dividend = self.get_sensor(sensor.cfg.dividend_name).get_reader(sensor.cfg.dividend_strategy)
            sensor.reader_divisor = self.get_sensor(sensor.cfg.divisor_name).get_reader(sensor.cfg.divisor_strategy)
        sensor.start()

    def load_automations(self):
        all_names = PerfusionConfig.get_section_names('automations')
        for name in all_names:
            try:
                automation = get_object(name, config='automations')
                automation.read_config()
            except AttributeError as e:
                self._lgr.error(f'Failed to read config for {name}')
                self._lgr.exception(e)
                continue

            self._lgr.debug(f'Automation is {type(automation)}')
            if isinstance(automation, AutoGasMixer):
                # self._lgr.debug(f'loading {automation.cfg.gas_device}, {automation.cfg.data_source}')
                automation.gas_device = self.get_sensor(automation.cfg.gas_device).hw
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoDialysis):
                automation.pump = self.get_sensor(automation.cfg.pump)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoSyringeVaso):
                automation.constrictor = self.get_sensor(automation.cfg.constrictor)
                automation.dilator = self.get_sensor(automation.cfg.dilator)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoSyringeGlucose):
                automation.decrease = self.get_sensor(automation.cfg.decrease)
                automation.increase = self.get_sensor(automation.cfg.increase)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoSyringe):
                automation.device = self.get_sensor(automation.cfg.device)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, StaticAutoFlow):
                self._lgr.warning(f'Looking for {automation.cfg.device}')
                automation.device = self.get_sensor(automation.cfg.device)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
                self._lgr.warning(f'loaded automation StaticAutoFlow with {automation.device}, {automation.data_source}')
            elif isinstance(automation, SinusoidalAutoFlow):
                automation.device = self.get_sensor(automation.cfg.device)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()
            elif isinstance(automation, AutoFlow):
                automation.device = self.get_sensor(automation.cfg.device)
                automation.data_source = self.get_sensor(automation.cfg.data_source).get_reader()


            self.automations[name] = automation

    def get_sensor(self, name: str):
        return self.sensors.get(name, None)

    def get_automation(self, name: str):
        return self.automations.get(name, None)

    def write_config(self, obj):
        PerfusionConfig.write_from_dataclass('sensors', obj.name, obj.cfg, classname=self.__class__.__name__)

    def create_config(self, obj):
        PerfusionConfig.read_into_dataclass(self.config_name, obj.name, obj.cfg)

        # change logging name to reflect sensor name for easier filtering
        # of log message
        lgr = logging.getLogger(f'{__name__}.{obj.name}')
        # attach hardware
        try:
            if hasattr(obj.cfg, 'hw_name'):
                obj.hw = SYS_HW.get_hw(obj.cfg.hw_name)
                obj.hw.set_parent(obj)
        except AttributeError:
            lgr.debug(f'no hardware for for {obj.cfg.hw_name}')

        # load strategies
        lgr.debug(f'strategies are {obj.cfg.strategy_names}')
        for name in obj.cfg.strategy_names.split(', '):
            # lgr.debug(f'Getting strategy {name}')
            params = PerfusionConfig.read_section('strategies', name)
            try:
                # lgr.debug(f'Looking for {params}')
                strategy_class = globals().get(params['class'], None)
                try:
                    # lgr.debug(f'Found {strategy_class}')
                    cfg = strategy_class.get_config_type()()
                    # lgr.debug(f'Config type is {cfg}')
                    PerfusionConfig.read_into_dataclass('strategies', name, cfg)
                    # lgr.debug(f'adding strategy {name}')
                    strategy = strategy_class(name)
                    strategy.cfg = cfg
                    obj.add_strategy(strategy)
                except AttributeError:
                    self._lgr.exception(f'Could not find strategy class for {name}')
                    pass
            except AttributeError:
                lgr.exception(f'Could not create algorithm {params["algorithm"]} for {__name__} {self.name}')
        return obj
