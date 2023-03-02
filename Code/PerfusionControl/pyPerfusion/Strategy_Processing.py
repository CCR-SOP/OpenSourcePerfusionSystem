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

import pyPerfusion.Strategy_ReadWrite as Strategy_ReadWrite


@dataclass
class WindowConfig(Strategy_ReadWrite.WriterConfig):
    window_len: int = 1


class RMS(Strategy_ReadWrite.WriterStream):
    def __init__(self, cfg: WindowConfig, hw=None):
        self._lgr = logging.getLogger(__name__)
        super().__init__(cfg, hw)
        self.cfg.algorithm = "RMS"
        self._sum = 0
        self._window_buffer = None
        self._data_type = np.float64

    @classmethod
    def get_config_type(cls):
        return WindowConfig

    def _process(self, buffer, t=None):
        if self._window_buffer is None:
            self._window_buffer = np.zeros(self.cfg.window_len, dtype=self._data_type)
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

    def reset(self):
        super().reset()
        self._sum = 0


class MovingAverage(Strategy_ReadWrite.WriterStream):
    def __init__(self, cfg: WindowConfig):
        super().__init__(cfg)
        self.cfg.algorithm = "MovingAverage"
        self._sum = 0
        self._window_buffer = None
        self._data_type = np.float64

    @classmethod
    def get_config_type(cls):
        return WindowConfig

    def _process(self, buffer, t=None):
        if self._window_buffer is None:
            self._window_buffer = np.zeros(self.cfg.window_len, dtype=self._data_type)
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

    def reset(self):
        super().reset()
        self._sum = 0
