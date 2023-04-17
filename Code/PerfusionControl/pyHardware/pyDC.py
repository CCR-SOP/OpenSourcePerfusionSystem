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

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class DCDeviceException(PerfusionConfig.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class DCChannelConfig:
    device: str = ''
    line: int = 0
    output_volts: float = 0.0
    cal_pt1_volts: np.float64 = 0.0
    cal_pt1_flow: np.float64 = -0.03
    cal_pt2_volts: np.float64 = 5
    cal_pt2_flow: np.float64 = 49.7


class DCDevice:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)

        self.cfg = DCChannelConfig()
        self.buf_dtype = np.dtype(np.float64)
        self.data_dtype = np.dtype(np.float64)
        self._queue = Queue()
        self._q_timeout = 0.5
        self.volt_range = [0, 5.0]

        self._buffer = np.zeros(1, dtype=self.buf_dtype) - self.cfg.cal_pt1_flow

        self.acq_start_ms = 0
        self.buf_len = 1
        self.sampling_period_ms = 0

    @property
    def devname(self):
        return 'dc'

    @property
    def last_value(self):
        return self._buffer[0]

    @property
    def last_flow(self):
        return self.volts_to_mlpermin(self._buffer[0])

    @property
    def is_running(self):
        return self._buffer[0] == 0

    def volts_to_mlpermin(self, volts):
        ml_per_min = (((volts - self.cfg.cal_pt1_volts) * (self.cfg.cal_pt2_flow - self.cfg.cal_pt1_flow))
                       / (self.cfg.cal_pt2_volts - self.cfg.cal_pt1_volts)) + self.cfg.cal_pt1_flow
        return ml_per_min

    def mlpermin_to_volts(self, ml_per_min):
        volts = ((((ml_per_min - self.cfg.cal_pt1_flow)
                 * (self.cfg.cal_pt2_volts - self.cfg.cal_pt1_volts))
                 / (self.cfg.cal_pt2_flow - self.cfg.cal_pt1_flow))
                 + self.cfg.cal_pt1_volts)
        return volts

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def open(self, cfg: DCChannelConfig = None):
        if cfg is not None:
            self.cfg = cfg
        self._buffer = np.zeros(1, dtype=self.buf_dtype)

    def is_open(self):
        return self.cfg is not None

    def close(self):
        self.stop()

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg)

    def read_config(self):
        PerfusionConfig.read_into_dataclass('hardware', self.name, self.cfg)
        self.open()

    def start(self):
        self.acq_start_ms = utils.get_epoch_ms()

    def stop(self):
        self.set_output(0)

    def set_flow(self, ml_per_min: float):
        volts = self.mlpermin_to_volts(ml_per_min)
        self._lgr.debug(f'ml/min = {ml_per_min}, volts = {volts}')
        self.set_output(volts)

    def set_output(self, output_volts: float):
        self._buffer[0] = output_volts
        self._queue.put((self._buffer, utils.get_epoch_ms()))
        self._lgr.debug(f'last value is {self.volts_to_mlpermin(self._buffer[0])}')

    def adjust_percent_of_max(self, percent: float):
        self._lgr.debug(f'last value is {self._buffer[0]}')
        adjustment = (percent / 100.0) * (self.volt_range[1] - self.volt_range[0])
        value = self._buffer[0] + adjustment
        self._lgr.debug(f'adjust speed by {adjustment} to {value}')

        if value < self.volt_range[0]:
            self._lgr.warning(f'Pump speed already at lowest value. No adjustment can be made')
        elif value > self.volt_range[1]:
            self._lgr.warning(f'Pump speed already at highest value. No adjustment can be made')
        else:
            self.set_output(value)

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
