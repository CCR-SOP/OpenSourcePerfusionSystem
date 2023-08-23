""" Class for generating waveforms for pumps

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from dataclasses import dataclass
from enum import IntEnum
from queue import Queue, Empty
from threading import Lock, Thread, Event

import numpy as np

import pyHardware.pyGeneric as pyGeneric
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


class WaveformGenException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class WaveformConfig:
    update_period_ms: int = 0


@dataclass
class SineConfig(WaveformConfig):
    min_rpm: float = 0.0
    max_rpm: float = 0.0
    freq: float = 0.0
    update_period_ms: int = 0


@dataclass
class ConstantConfig(WaveformConfig):
    rpm: float = 0.0


def create_waveform_from_str(config_str):
    params = config_str.split(',')
    if params[0] == 'constant':
        cfg = ConstantConfig(rpm=float(params[1]))
        obj = create_waveform_from_config(cfg)
    elif params[0] == 'sine':
        cfg = SineConfig(min_rpm=float(params[1]), max_rpm=float(params[2]), freq=float(params[3]))
        obj = create_waveform_from_config(cfg)
    else:
        obj = None
    return obj


def create_waveform_from_config(config):
    if type(config) == ConstantConfig:
        obj = ConstantGen()
        obj.cfg = config
    elif type(config) == SineConfig:
        obj = SineGen()
        obj.cfg = config
    else:
        obj = None

    return obj


class WaveformGen:
    def __init__(self):
        self._lgr = utils.get_object_logger(__name__, 'WaveformGen')
        self.cfg = WaveformConfig()

    def get_value_at(self, time_pt):
        return 0

    def get_period_ms(self):
        return 0

    def get_config_str(self):
        return f'none'


class ConstantGen(WaveformGen):
    def __init__(self):
        super().__init__()
        self._lgr = utils.get_object_logger(__name__, "ConstantGen")
        self.cfg = ConstantConfig()

    def get_value_at(self, time_pt):
        return self.cfg.rpm

    def get_config_str(self):
        return f'constant, {self.cfg.rpm}'


class SineGen(WaveformGen):
    def __init__(self):
        super().__init__()
        self._lgr = utils.get_object_logger(__name__, 'SineGen')
        self.cfg = SineConfig()

    def get_value_at(self, time_pt):
        # adjust time point to with a period
        t = time_pt % (1.0 / self.cfg.freq)
        pt = (np.sin(2*np.pi*self.cfg.freq * t) + 1.0) * 0.5
        adjusted = pt * (self.cfg.max_rpm - self.cfg.min_rpm) + self.cfg.min_rpm
        # self._lgr.debug(f'{time_pt}|{adjusted}|{self.cfg.min_rpm}|{self.cfg.max_rpm}|{self.cfg.freq}')
        return adjusted

    def get_config_str(self):
        return f'sine, {self.cfg.min_rpm}, {self.cfg.max_rpm}, {self.cfg.freq}'
