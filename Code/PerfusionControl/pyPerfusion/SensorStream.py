import pathlib
import datetime
from threading import Thread, Event
import logging
import time

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy
from pyPerfusion.FileStrategy import StreamToFile


DATA_VERSION = 1


class SensorStream:
    def __init__(self, name, unit_str, hw, valid_range=None):
        self._logger = logging.getLogger(__name__)
        self._logger.info(f'Creating SensorStream object {name}')
        self.__thread = None
        self._unit_str = unit_str
        self._valid_range = valid_range
        self.hw = hw
        self._ch_id = None
        self._evt_halt = Event()
        self.name = name
        self._timestamp = None
        self._strategies = []
        self._params = {'Sensor': self.name,
                        'Unit': self._unit_str,
                        'Data Format': str(np.dtype(self.hw.data_type)),
                        'Sampling Period (ms)': self.hw.period_sampling_ms,
                        'Start of Acquisition': 0
                        }

    @property
    def params(self):
        return self._params

    @property
    def buf_len(self):
        return self.hw.buf_len

    @property
    def unit_str(self):
        return self._unit_str

    @property
    def valid_range(self):
        return self._valid_range

    @property
    def ch_id(self):
        return self._ch_id

    def add_strategy(self, strategy: ProcessingStrategy):
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
        while not self._evt_halt.is_set():
            next_t += offset + self.hw.period_sampling_ms / 1000.0
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
                offset = 0
            else:
                offset = -delay
            data_buf, t = self.hw.get_data(self._ch_id)
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf = strategy.process_buffer(buf, t)

    def set_ch_id(self, ch_id):
        self._ch_id = ch_id

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
        self.__thread = Thread(target=self.run)
        self.__thread.name = f'SensorStream ({self.name})'
        self.__thread.start()

    def stop(self):
        self._evt_halt.set()
        if self.__thread:
            self.__thread.join(2.0)

