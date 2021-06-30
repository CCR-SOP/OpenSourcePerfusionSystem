# -*- coding: utf-8 -*-
"""Base class for processing stream data


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import numpy as np


class ProcessingStrategy:
    def __init__(self, window_len, expected_buffer_len):
        self._data_type = np.float32
        self._win_len = window_len
        self._window_buffer = np.zeros(self._win_len, dtype=self._data_type)
        self._processed_buffer = np.zeros(expected_buffer_len, dtype=np.float32)
        self._midpt = np.floor(self._win_len / 2.0)

    def process_buffer(self, buffer):
        idx = 0
        for sample in buffer:
            front = self._window_buffer[0]
            self._window_buffer = np.roll(self._window_buffer, -1)
            self._window_buffer[-1] = sample
            self._processed_buffer = np.roll(self._processed_buffer, -1)
            self._processed_buffer[-1] = sample
            idx += 1
        return self._processed_buffer

    def reset(self):
        self._processed_buffer = np.zeros_like(self._window_buffer)


class RMSStrategy(ProcessingStrategy):
    def __init__(self, window_len, expected_buffer_len):
        super().__init__(window_len, expected_buffer_len)
        self._sum = 0

    def process_buffer(self, buffer):
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
