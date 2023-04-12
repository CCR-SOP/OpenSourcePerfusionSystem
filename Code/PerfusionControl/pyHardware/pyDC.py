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
from dataclasses import dataclass
from queue import Queue, Empty

import numpy as np
import numpy.typing as npt

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class DCDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class DCChannelConfig:
    device: str = ''
    line: int = 0
    output_volts: float = 0.0
    data_type: npt.DTypeLike = np.dtype(np.float64).name
    buf_type: npt.DTypeLike = np.dtype(np.uint16).name


class DCDevice:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)

        self.cfg = DCChannelConfig()
        self._queue = Queue()
        self._q_timeout = 0.5

        self._buffer = np.zeros(1, dtype=self.cfg.data_type)

        self.acq_start_ms = 0
        self.buf_len = 1
        self.sampling_period_ms = 0

    @property
    def devname(self):
        return 'dc'

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def open(self, cfg: DCChannelConfig):
        self.cfg = cfg
        self._buffer = np.zeros(1, dtype=self.cfg.data_type)

    def is_open(self):
        return self.cfg is not None

    def close(self):
        self.stop()

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.name
        PerfusionConfig.read_into_dataclass('hardware', channel_name, self.cfg)

    def start(self):
        self.acq_start_ms = utils.get_epoch_ms()

    def stop(self):
        self.set_output(0)

    def set_output(self, output_volts: float):
        self._buffer[0] = output_volts
        self._queue.put((self._buffer, utils.get_epoch_ms()))

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=self._q_timeout)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t
