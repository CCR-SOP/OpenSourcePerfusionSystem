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

from dataclasses import dataclass, field
from typing import List

import numpy as np

import pyPerfusion.utils as utils
import pyHardware.pyGeneric as pyGeneric


class DCDeviceException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class DCChannelConfig:
    device: str = ''
    line: int = 0
    flow_range: List = field(default_factory=lambda: [0, 100])
    cal_pt1_volts: np.float64 = 0.0
    cal_pt1_flow: np.float64 = 0.03
    cal_pt2_volts: np.float64 = 5
    cal_pt2_flow: np.float64 = 49.7


class DCDevice(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = DCChannelConfig()

        self._buffer = np.zeros(1, dtype=self.data_dtype)
        self.buf_len = 1
        self.sampling_period_ms = 0
        self.output_range = [0, 5]

    @property
    def last_value(self):
        return self._buffer[0]

    @property
    def last_flow(self):
        return self.volts_to_mlpermin(self.last_value)

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

    def stop(self):
        self.set_output(0)
        super().stop()

    def set_flow(self, ml_per_min):
        volts = self.mlpermin_to_volts(ml_per_min)
        self._lgr.debug(f'ml/min = {ml_per_min}, volts = {volts}')
        self.set_output(volts)

    def adjust_percent_of_max(self, percent: float):
        adjust = (percent / 100.0) * (self.output_range[1] - self.output_range[0])
        volts = self.last_value + adjust
        self.set_output(volts)

    def set_output(self, output_volts: float):
        if output_volts < self.output_range[0]:
            self._lgr.warning(f'Attempt to set output below {self.output_range[0]}')
            output_volts = self.output_range[0]
        elif output_volts > self.output_range[1]:
            self._lgr.warning(f'Attempt to set output below {self.output_range[1]}')
            output_volts = self.output_range[1]
        self._buffer[0] = output_volts
        self._queue.put((self._buffer, utils.get_epoch_ms()))
