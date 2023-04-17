# -*- coding: utf-8 -*-
"""Base class for a pump

Requires numpy library

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from dataclasses import dataclass, field
from typing import List
from threading import Lock

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class PumpDeviceException(PerfusionConfig.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class PumpConfig:
    hw_name: str = ''
    flow_range: List = field(default_factory=lambda: [0, 100])
    cal_pt1_volts: np.float64 = 0.0
    cal_pt1_flow: np.float64 = -0.03
    cal_pt2_volts: np.float64 = 5
    cal_pt2_flow: np.float64 = 49.7


class Pump:
    def __init__(self, name):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.name = name
        self.hw = None
        self.cfg = PumpConfig()

        self._queue = None
        self.acq_start_ms = 0
        self.mutex = Lock()

        self.data_type = np.uint32

    @property
    def last_flow(self):
        return self.volts_to_mlpermin(self.hw.last_value)

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

    def write_config(self):
        PerfusionConfig.write_from_dataclass('actuators', self.name, self.cfg)

    def read_config(self):
        self._lgr.debug(f'Reading config for {self.name}')
        PerfusionConfig.read_into_dataclass('actuators', self.name, self.cfg)
        self.open()

    def open(self, cfg=None):
        self._lgr.debug(f'Attempting to open {self.name} with config {cfg}')
        if cfg is not None:
            self.cfg = cfg

    def close(self):
        self.stop()

    def start(self):
        self.acq_start_ms = utils.get_epoch_ms()
        if self.hw:
            self.hw.start()

    def stop(self):
        if self.hw:
            self.hw.stop()

    def set_speed(self, value: float):
        if self.hw:
            with self.mutex:
                self.hw.set_output(value)

    def set_flow(self, ml_per_min: float):
        if self.hw:
            with self.mutex:
                volts = self.mlpermin_to_volts(ml_per_min)
                self._lgr.debug(f'ml/min = {ml_per_min}, volts = {volts}')
                self.hw.set_output(volts)

    def get_speed(self) -> int:
        return self.hw.last_value

    def get_flow(self) -> float:
        return self.last_flow
