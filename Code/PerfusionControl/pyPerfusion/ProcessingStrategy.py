# -*- coding: utf-8 -*-
"""Base class for processing stream data


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from dataclasses import dataclass

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class ProcessingStrategyConfig:
    name: str = ''
    strategy: str = "ProcessingStrategy"
    buf_len: int = 0
    window_len: int = 1


class ProcessingStrategy:
    def __init__(self, name: str, window_len: int, buf_len: int):
        self._lgr = logging.getLogger(__name__)
        self._data_type = np.float64
        self.cfg = ProcessingStrategyConfig(name=name, window_len=window_len, buf_len=buf_len)
        self._window_buffer = np.zeros(self.cfg.window_len, dtype=self._data_type)
        self._processed_buffer = np.zeros(self.cfg.buf_len, dtype=self._data_type)

    @classmethod
    def get_config_type(cls):
        return ProcessingStrategyConfig

    @property
    def name(self):
        return self.cfg.name

    def write_config(self):
        PerfusionConfig.write_from_dataclass('strategies', self.cfg.name, self.cfg)

    def read_config(self, strategy_name: str = None):
        if strategy_name is None:
            strategy_name = self.cfg.name
        PerfusionConfig.read_into_dataclass('strategies', strategy_name, self.cfg)

    def process_buffer(self, buffer, t=None):
        idx = 0
        for sample in buffer:
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sample
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = sample
            idx += 1
        return self._processed_buffer

    def retrieve_buffer(self, time_period, samples_needed):
        buffer = []
        return buffer

    def reset(self):
        self._processed_buffer = np.zeros_like(self._window_buffer)

    def open(self):
        pass

    def close(self):
        pass


class RMSStrategy(ProcessingStrategy):
    def __init__(self, name: str, window_len: int, buf_len: int):
        super().__init__(name, window_len, buf_len)
        self.cfg.algorithm = "RMSStrategy"

        self._sum = 0

    def process_buffer(self, buffer, t=None):
        idx = 0
        for sample in buffer:
            sqr = sample * sample
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sqr
            self._sum += sqr - front
            rms = np.sqrt(self._sum / self.cfg.window_len)
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = rms
            idx += 1

        return self._processed_buffer

    def reset(self):
        super().reset()
        self._sum = 0


class MovingAverageStrategy(ProcessingStrategy):
    def __init__(self, name: str, window_len: int, buf_len: int):
        super().__init__(name, window_len, buf_len)
        self.cfg.algorithm = "MovingAverageStrategy"
        self._sum = 0

    def process_buffer(self, buffer, t=None):
        idx = 0
        for sample in buffer:
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sample
            self._sum += sample - front
            avg = np.sum(self._window_buffer) / self.cfg.window_len
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = avg
            # self._lgr.debug(f'sample: {sample}: avg: {avg}')
            # self._lgr.debug(f'buffer: {buffer}')
            # self._lgr.debug(f'processed buffer: {self._processed_buffer}')
            idx += 1

        return self._processed_buffer

    def reset(self):
        super().reset()
        self._sum = 0
