import datetime
from threading import Thread, Event
import logging
import time
from typing import Type

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy
from pyPerfusion.FileStrategy import StreamToFile, PointsToFile


DATA_VERSION = 1


class SensorStream:
    def __init__(self, hw_channel, unit_str, valid_range=None):
        self._lgr = logging.getLogger(__name__)
        self._lgr.info(f'Creating SensorStream object {hw_channel.cfg.name}')
        self.__thread = None
        self._unit_str = unit_str
        self._valid_range = valid_range
        self.hw = hw_channel
        self._evt_halt = Event()

        self.data = None
        self._timestamp = None
        self.data = np.array(self.hw.buf_len, dtype=self.hw.data_type)

        self._strategies = []
        self._params = {'Sensor': self.hw.cfg.name,
                        'Unit': self._unit_str,
                        'Data Format': np.dtype(self.hw.data_type).name,
                        'Sampling Period (ms)': self.hw.sampling_period_ms,
                        'Start of Acquisition': 0
                        }

    @property
    def params(self):
        return self._params

    @property
    def name(self):
        return self.hw.cfg.name

    @property
    def buf_len(self):
        return self.hw.buf_len

    @property
    def unit_str(self):
        return self._unit_str

    @property
    def valid_range(self):
        return self._valid_range

    def add_strategy(self, strategy: ProcessingStrategy):
        if isinstance(strategy, StreamToFile):
            strategy.open(self)
        elif isinstance(strategy, PointsToFile):
            strategy.open(self)
        else:
            strategy.open()
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

    def run(self):
        next_t = time.time()
        offset = 0
        if self.hw.sampling_period_ms == 0:
            sampling_period_s = 1.0
        else:
            sampling_period_s = self.hw.sampling_period_ms / 1000.0
        while not self._evt_halt.is_set():
            next_t += offset + sampling_period_s
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
                offset = 0
            else:
                offset = -delay

            data_buf, t = self.hw.get_data()
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf = strategy.process_buffer(buf, t)

    def open(self):
        pass

    def close(self):
        self.stop()
        for strategy in self._strategies:
            strategy.close()

    def start(self):
        if self.__thread:
            self.stop()
        self._timestamp = datetime.datetime.now()
        self._params['Start of Acquisition'] = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        self._evt_halt.clear()
        self.__thread = Thread(target=self.run)
        self.__thread.name = f'SensorStream ({self.hw.cfg.name})'
        self.__thread.start()
        self._lgr.debug(f'{self.hw.cfg.name} sensor started')

    def stop(self):
        self._evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)
            self.__thread = None

