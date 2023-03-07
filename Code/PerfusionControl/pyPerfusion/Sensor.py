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

import pyPerfusion.ProcessingStrategy as ProcessingStrategy
import pyPerfusion.Strategies as Strategies
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.pyCDI import CDIStreaming, MockCDI
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

        # create hardware
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
                self.add_strategy(strategy_class(cfg))
            except AttributeError as e:
                self._lgr.error(f'Could not find algorithm {params["algorithm"]} for sensor {self.cfg.name}')
                self._lgr.error(f'Error message is {e}')

    def add_strategy(self, strategy: ProcessingStrategy):
        if isinstance(strategy, StreamToFile):
            strategy.open(self)
        elif isinstance(strategy, PointsToFile):
            strategy.open(self)
        else:
            strategy.open(sensor_name=self.name)
        self._strategies.append(strategy)

    def get_all_file_strategies(self):
        file_strategies = [strategy for strategy in self._strategies if isinstance(strategy, StreamToFile)]
        return file_strategies

    def get_file_strategy(self, name=None):
        strategy = None
        if name is None:
            file_strategies = self.get_all_file_strategies()
            if len(file_strategies) > 0:
                strategy = file_strategies[-1]
        else:
            strategy = [strategy for strategy in self._strategies if strategy.name == name]
            if len(strategy) > 0:
                strategy = strategy[0]
        return strategy

    def get_reader(self, name: str = None):
        if name is None:
            reader = self._strategies[-1]
        else:
            reader = [strategy for strategy in self._strategies if strategy.cfg.name == name]
            if len(reader) > 0:
                reader = reader[0]
            else:
                return None
        return reader.get_reader()

    def run(self):
        while not self._evt_halt.is_set():
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

