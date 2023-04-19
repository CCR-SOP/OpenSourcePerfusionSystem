# -*- coding: utf-8 -*-
"""Base class for sensors which is the interface for acquiring data from hardware and writing to files

Requires numpy library

The Sensor class is intended to the primary interface for apps and scripts to retrieve data from hardware sensors like
flow or pressure. It is also used to log how actuators, e.g., pumps, are being controlled.


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Thread, Event
from dataclasses import dataclass, field
from typing import List

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW
from pyPerfusion.Strategy_Processing import *
from pyPerfusion.Strategy_ReadWrite import *

@dataclass
class BaseSensorConfig:
    strategy_names: str = ''


@dataclass
class SensorConfig(BaseSensorConfig):
    hw_name: str = ''
    units: str = ''
    valid_range: List = field(default_factory=lambda: [0, 100])


@dataclass
class CalculatedSensorConfig(BaseSensorConfig):
    units: str = ''
    samples_per_calc: int = 1
    sensor_strategy: str = ''


@dataclass
class DivisionSensorConfig(BaseSensorConfig):
    units: str = ''
    dividend_name: str = ''
    divisor_name: str = ''
    dividend_strategy: str = ''
    divisor_strategy: str = ''
    samples_per_calc: int = 1


@dataclass
class ActuatorWriterConfig(BaseSensorConfig):
    units: str = ''
    hw_name: str = ''


@dataclass
class GasMixerConfig(BaseSensorConfig):
    hw_name: str = ''


@dataclass
class SyringeConfig(BaseSensorConfig):
    hw_name: str = ''
    target_ul: int = 0
    rate_ul_per_min: int = 0


class Sensor:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self._lgr.info(f'Creating {__name__} object {name}')
        self.__thread = None
        self._evt_halt = Event()
        self._timeout = 0.5
        self.hw = None

        self.cfg = SensorConfig()

        self._strategies = []

    @property
    def data_dtype(self):
        return self.hw.data_dtype

    def write_config(self):
        PerfusionConfig.write_from_dataclass('sensors', self.name, self.cfg)

    def read_config(self):
        # self._lgr.debug(f'Reading config for {self.name}')
        PerfusionConfig.read_into_dataclass('sensors', self.name, self.cfg)

        # attach hardware
        if hasattr(self.cfg, 'hw_name'):
            self.hw = SYS_HW.get_hw(self.cfg.hw_name)

        # load strategies
        # self._lgr.debug(f'strategies are {self.cfg.strategy_names}')
        for name in self.cfg.strategy_names.split(', '):
            # self._lgr.debug(f'Getting strategy {name}')
            params = PerfusionConfig.read_section('strategies', name)
            try:
                # self._lgr.debug(f'Looking for {params["class"]}')
                strategy_class = globals().get(params['class'], None)
                try:
                    # self._lgr.debug(f'Found {strategy_class}')
                    cfg = strategy_class.get_config_type()()
                    # self._lgr.debug(f'Config type is {cfg}')
                    PerfusionConfig.read_into_dataclass('strategies', name, cfg)
                    # self._lgr.debug('adding strategy')
                    strategy = strategy_class(name)
                    strategy.cfg = cfg
                    self.add_strategy(strategy)
                except AttributeError as e:
                    self._lgr.error(f'Could not find strategy class for {name}')
                    pass
            except AttributeError as e:
                self._lgr.error(f'Could not create algorithm {params["algorithm"]} for {__name__} {self.name}')
                self._lgr.exception(e)

    def add_strategy(self, strategy):
        strategy.open(sensor=self)
        self._strategies.append(strategy)

    def get_reader(self, name: str = None):
        writer = self.get_writer(name)
        if writer is None:
            reader = None
        else:
            reader = writer.get_reader()
        return reader

    def get_writer(self, name: str = None):
        if name is None:
            writer = self._strategies[-1]
        else:
            try:
                writer = [strategy for strategy in self._strategies if strategy.name == name]
                if len(writer) > 0:
                    writer = writer[0]
                else:
                    return None
            except IndexError as e:
                self._lgr.error(f'No strategies exist for {name}')
                writer = None
        return writer

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            if self._evt_halt.wait(self._timeout):
                break
            if self.hw is not None:
                data_buf, t = self.hw.get_data()
                if data_buf is not None:
                    buf = data_buf
                    for strategy in self._strategies:
                        buf, t = strategy.process_buffer(buf, t)

    def open(self):
        pass

    def close(self):
        self.stop()
        for strategy in self._strategies:
            strategy.close()

    def start(self):
        if self.__thread:
            self.stop()
        self._evt_halt.clear()
        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{__name__} {self.name}'
        self.__thread.start()
        # self._lgr.debug(f'{self.name} sensor started')

    def stop(self):
        self._evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)
            self.__thread = None


class CalculatedSensor(Sensor):
    def __init__(self, name):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = CalculatedSensorConfig()

    @property
    def data_dtype(self):
        return self.get_reader().data_dtype

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            if self._evt_halt.wait(self._timeout):
                break
            t, data_buf = self.get_reader().get_data_from_last_read(self.cfg.samples_per_calc)
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf, t = strategy.process_buffer(buf, t)


class DivisionSensor(Sensor):
    def __init__(self, name):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = DivisionSensorConfig()
        self.reader_dividend = None
        self.reader_divisor = None

    @property
    def data_dtype(self):
        return self.get_writer().data_dtype

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            if self._evt_halt.wait(self._timeout):
                break
            t_f, dividend = self.reader_dividend.get_data_from_last_read(self.cfg.samples_per_calc)
            t_p, divisor = self.reader_divisor.get_data_from_last_read(self.cfg.samples_per_calc)
            if dividend is not None and divisor is not None:
                buf = np.divide(dividend, divisor)
                for strategy in self._strategies:
                    buf, t = strategy.process_buffer(buf, t_f)


class GasMixerSensor(Sensor):
    def __init__(self, name):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = GasMixerConfig()


class SyringeSensor(Sensor):
    def __init__(self, name):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = SyringeConfig()
