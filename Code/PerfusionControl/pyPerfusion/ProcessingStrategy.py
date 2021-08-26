# -*- coding: utf-8 -*-
"""Base class for processing stream data


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pathlib
import datetime
import logging
from os import SEEK_END

import numpy as np


class ProcessingStrategy:
    def __init__(self, name, window_len, expected_buffer_len):
        self._logger = logging.getLogger(__name__)
        self._name = name
        self._data_type = np.float32
        self._win_len = window_len
        self._window_buffer = np.zeros(self._win_len, dtype=self._data_type)
        self._processed_buffer = np.zeros(expected_buffer_len, dtype=self._data_type)
        self._params = {'Algorithm': 'Raw',
                        'Window Length': window_len}

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params

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
    def __init__(self, name, window_len, expected_buffer_len):
        super().__init__(name, window_len, expected_buffer_len)
        self._params['Algorithm'] = 'RMS'
        self._params['Data Format'] = str(np.dtype(np.float32))
        self._sum = 0

    def process_buffer(self, buffer, t=None):
        idx = 0
        for sample in buffer:
            sqr = sample * sample
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sqr
            self._sum += sqr - front
            rms = np.sqrt(self._sum / self._win_len)
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = rms
            idx += 1

        return self._processed_buffer

    def reset(self):
        super().reset()
        self._sum = 0
