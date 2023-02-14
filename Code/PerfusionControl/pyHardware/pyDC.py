# -*- coding: utf-8 -*-
"""Base class for generating analog DC output

Provides basic interface for accessing analog outputs.
Used directly only for testing other code without direct access to the hardware

Requires numpy library

This class will output the data to a file to verify operation. This can also be used by derived classes to verify
the data being written to the analog output channel.

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from time import perf_counter
from dataclasses import dataclass
from collections import deque

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig


class DCDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class DCChannelConfig:
    name: str = 'Channel'
    Device: str = ''
    LineName: int = 0
    output_volts: float = 0.0


class DCDevice:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)
        self.cfg = None
        self._queue = self._queue = deque(maxlen=100)
        self._buffer = np.zeros(1, dtype=np.float64)
        # stores the perf_counter value at the start of the acquisition which defines the zero-time for all
        # following samples
        self.__acq_start_t = 0
        self.buf_len = 1
        self.data_type = float
        self.sampling_period_ms = 0

    @property
    def devname(self):
        return 'dc'

    def open(self, cfg: DCChannelConfig):
        self.cfg = cfg

    def is_open(self):
        return self.cfg is not None

    def close(self):
        self.stop()

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.cfg.name, self.cfg)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.cfg.name
        PerfusionConfig.read_into_dataclass('hardware', channel_name, self.cfg)

    def start(self):
        # self.stop()
        self.__acq_start_t = perf_counter()

    def stop(self):
        self.set_output(0)

    def set_output(self, output_volts: float):
        self._buffer[0] = output_volts
        self._queue.append((self._buffer, perf_counter()-self.__acq_start_t))

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.pop()
        except IndexError:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t
