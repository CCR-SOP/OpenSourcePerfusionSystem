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
import pyPerfusion.utils as utils


@dataclass
class WindowConfig(Strategy_ReadWrite.WriterConfig):
    window_len: int = 1


@dataclass
class RunningSumConfig(Strategy_ReadWrite.WriterConfig):
    calibration_seconds: int = 1


class RMS(Strategy_ReadWrite.WriterStream):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = WindowConfig()
        self._sum = 0
        self._window_buffer = None
        self.data_dtype = np.dtype('float64')

    @classmethod
    def get_config_type(cls):
        return WindowConfig

    def _process(self, buffer, t=None):
        if self._window_buffer is None:
            self._window_buffer = np.zeros(self.cfg.window_len, dtype=self.data_dtype)
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
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = WindowConfig()
        self._sum = 0
        self._window_buffer = None
        self.data_dtype = np.dtype(np.float64)

    @classmethod
    def get_config_type(cls):
        return WindowConfig

    def _process(self, buffer, t=None):
        if self._window_buffer is None:
            self._window_buffer = np.zeros(self.cfg.window_len, dtype=self.data_dtype)
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


class RunningSum(Strategy_ReadWrite.WriterStream):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = RunningSumConfig()
        self._window_buffer = None
        self.data_dtype = np.dtype(np.float64)
        self._calibration_buffer = None
        self._cal_idx = 0
        self._calibrating = False
        self.flow_offset = 0.0
        self.last_volume = 0.0

    @classmethod
    def get_config_type(cls):
        return RunningSumConfig

    def _process(self, buffer, t=None):
        if self._calibrating:
            if self._calibration_buffer is None:
                cal_samples = int(self.cfg.calibration_seconds * 1_000 / self.sensor.sampling_period_ms)
                self._calibration_buffer = np.zeros(cal_samples, dtype=self.data_dtype)

            self._processed_buffer = buffer
            buf_len = len(buffer)
            buf_left = len(self._calibration_buffer) - self._cal_idx
            if buf_len <= buf_left:
                self._calibration_buffer[self._cal_idx:self._cal_idx + buf_len] = buffer
                self._cal_idx += buf_len
            else:
                self._calibration_buffer[self._cal_idx:self._cal_idx + buf_left] = buffer[0:buf_left]
                self._cal_idx += buf_left
            if self._cal_idx >= len(self._calibration_buffer):
                self._calibrating = False
                self.flow_offset = np.mean(self._calibration_buffer)
                self._lgr.info(f'Calibration complete, flow offset is {self.flow_offset}')
        else:
            try:
                self._processed_buffer = np.cumsum(buffer-self.flow_offset, dtype=self.data_dtype) \
                                         + self.last_volume
                self.last_volume = self._processed_buffer[-1]
            except IndexError as e:
                # buffer may not exist yet, could be waiting for data
                pass

    def reset(self):
        self.last_volume = 0.0
        self._cal_idx = 0
        self._calibrating = True

