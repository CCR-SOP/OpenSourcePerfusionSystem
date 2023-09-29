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
    bpm: float = 0.0
    update_period_ms: int = 0


@dataclass
class ConstantConfig(WaveformConfig):
    min_rpm: float = 0.0
    max_rpm: float = 0.0
    bpm: float = 0


def create_waveform_from_str(config_str, parent):
    params = config_str.split(',')
    if params[0] == 'constant':
        cfg = ConstantConfig(min_rpm=float(params[1]))
        obj = create_waveform_from_config(cfg, parent)
    elif params[0] == 'sine':
        cfg = SineConfig(min_rpm=float(params[1]), max_rpm=float(params[2]), bpm=float(params[3]))
        obj = create_waveform_from_config(cfg, parent)
    else:
        obj = None
    return obj


def create_waveform_from_config(config, parent):
    if type(config) == ConstantConfig:
        obj = ConstantGen(parent=parent)
        obj.cfg = config
    elif type(config) == SineConfig:
        obj = SineGen(parent=parent)
        obj.cfg = config
    else:
        obj = None

    return obj


class WaveformGen:
    def __init__(self, parent: object):
        self._lgr = utils.get_object_logger(__name__, 'WaveformGen')
        self.cfg = WaveformConfig()
        self.name = "NoWaveform"
        self.parent = parent

    def get_value_at(self, time_pt):
        return 0

    def get_period_ms(self):
        return 0

    def get_config_str(self):
        return f'none'

    def write_config(self):
        self.parent.write_config()

    def read_config(self):
        self.parent.read_config()


class ConstantGen(WaveformGen):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lgr = utils.get_object_logger(__name__, "ConstantGen")
        self.cfg = ConstantConfig()
        self.name = "Constant"

    def get_value_at(self, time_pt):
        return self.cfg.min_rpm

    def get_config_str(self):
        return f'constant, {self.cfg.min_rpm}'


class SineGen(WaveformGen):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._lgr = utils.get_object_logger(__name__, 'SineGen')
        self.cfg = SineConfig()
        self.name = "Sine"

    def get_value_at(self, time_pt):
        # adjust time point to with a period
        freq = self.cfg.bpm / 60.0
        t = time_pt % (1.0 / freq)
        pt = (np.sin(2 * np.pi * self.cfg.bpm * t) + 1.0) * 0.5
        adjusted = pt * (self.cfg.max_rpm - self.cfg.min_rpm) + self.cfg.min_rpm
        # self._lgr.debug(f'{time_pt}|{adjusted}|{self.cfg.min_rpm}|{self.cfg.max_rpm}|{self.cfg.freq}')
        return adjusted

    def get_config_str(self):
        return f'sine, {self.cfg.min_rpm}, {self.cfg.max_rpm}, {self.cfg.bpm}'
