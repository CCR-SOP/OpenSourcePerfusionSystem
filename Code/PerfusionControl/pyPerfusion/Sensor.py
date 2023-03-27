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
import logging
import time
from dataclasses import dataclass, field
from typing import Protocol, TypeVar, List

import numpy as np
import numpy.typing as npt

import pyPerfusion.Strategies as Strategies
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyHardware.SystemHardware import SYS_HW


class HWProtocol(Protocol):
    T = TypeVar("T", bound=npt.NBitBase)

    def get_buf_info(self) -> (int, np.dtype):
        pass

    def get_data(self) -> (np.int32, np.dtype[T]):
        pass

    def sampling_period_ms(self):
        pass


@dataclass
class SensorConfig:
    name: str = ''
    hw_name: str = ''
    strategy_names: str = ''
    units: str = ''
    valid_range: List = field(default_factory=lambda: [0, 100])


@dataclass
class CalculatedSensorConfig(SensorConfig):
    samples_per_calc: int = 1
    sensor_strategy: str = ''


@dataclass
class DivisionSensorConfig(SensorConfig):
    dividend_name: str = ''
    divisor_name: str = ''
    dividend_strategy: str = ''
    divisor_strategy: str = ''
    samples_per_calc: int = 1


class Sensor:
    def __init__(self, name: str):
        self._lgr = logging.getLogger(__name__)
        self._lgr.info(f'Creating Sensor object {name}')
        self.__thread = None
        self._evt_halt = Event()
        self.hw = None

        self.cfg = SensorConfig(name=name)

        self._strategies = []

    @property
    def name(self):
        return self.cfg.name

    def write_config(self):
        PerfusionConfig.write_from_dataclass('sensors', self.cfg.name, self.cfg)

    def read_config(self):
        self._lgr.debug(f'Reading config for {self.cfg.name}')
        PerfusionConfig.read_into_dataclass('sensors', self.cfg.name, self.cfg)
        # update the valid_range attribute to a list of integers
        # as it will be read in as a list of characters
        self.cfg.valid_range = [int(x) for x in ''.join(self.cfg.valid_range).split(',')]

        # attach hardware
        self._lgr.info(f'Attaching hw {self.cfg.hw_name} to {self.cfg.name}')
        self.hw = SYS_HW.get_hw(self.cfg.hw_name)

        # load strategies
        self._lgr.debug(f'strategies are {self.cfg.strategy_names}')
        for name in self.cfg.strategy_names.split(', '):
            self._lgr.debug(f'Getting strategy {name}')
            params = PerfusionConfig.read_section('strategies', name)
            self._lgr.debug(f'Attempting to get algorithm {params["algorithm"]}')
            try:
                strategy_class = Strategies.get_class(params['algorithm'])
                self._lgr.debug(f'Found {strategy_class}')
                cfg = strategy_class.get_config_type()()
                self._lgr.debug(f'Config type is {cfg}')
                PerfusionConfig.read_into_dataclass('strategies', name, cfg)
                cfg.name = name
                self._lgr.debug('adding strategy')
                self.add_strategy(strategy_class(cfg))
            except AttributeError as e:
                self._lgr.error(f'Could not create algorithm {params["algorithm"]} for sensor {self.cfg.name}')
                self._lgr.error(f'Error message is {e}')

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
            writer = [strategy for strategy in self._strategies if strategy.cfg.name == name]
            if len(writer) > 0:
                writer = writer[0]
            else:
                return None
        return writer

    def run(self):
        while not self._evt_halt.is_set():
            if self.hw is not None:
                data_buf, t = self.hw.get_data()
                if data_buf is not None:
                  buf = data_buf
                  for strategy in self._strategies:
                        buf, t = strategy.process_buffer(buf, t)

                else:
                   time.sleep(0.5)

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
        self.__thread.name = f'Sensor ({self.cfg.name})'
        self.__thread.start()
        self._lgr.debug(f'{self.cfg.name} sensor started')

    def stop(self):
        self._evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)
            self.__thread = None


class CalculatedSensor(Sensor):
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        super().__init__(name)
        self.cfg = CalculatedSensorConfig(name=name)
        self.reader = None

    def run(self):
        while not self._evt_halt.is_set():
            t, data_buf = self.reader.get_data_from_last_read(self.cfg.samples_per_calc)
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf, t = strategy.process_buffer(buf, t)

            else:
                time.sleep(0.5)


class DivisionSensor(Sensor):
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        super().__init__(name)
        self.cfg = DivisionSensorConfig(name=name)
        self.reader = None
        self.reader_dividend = None
        self.reader_divisor = None

    def run(self):
        while not self._evt_halt.is_set():
            t_f, dividend = self.reader_dividend.get_data_from_last_read(self.cfg.samples_per_calc)
            t_p, divisor = self.reader_divisor.get_data_from_last_read(self.cfg.samples_per_calc)
            if dividend is not None and divisor is not None:
                buf = np.divide(dividend, divisor)
                for strategy in self._strategies:
                    buf, t = strategy.process_buffer(buf, t_f)
            else:
                time.sleep(0.5)
