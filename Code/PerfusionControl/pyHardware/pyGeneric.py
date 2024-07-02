# -*- coding: utf-8 -*-
""" Base class for all hardware classes

Provides some common methods and attributes that all hardware classes should share

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from dataclasses import dataclass, field
from typing import List
from queue import Queue, Empty

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


class HardwareException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


class GenericDevice:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.parent = None
        self.cfg = None
        self._queue = Queue()
        self._q_timeout = 0.5
        self.acq_start_ms = 0
        self._is_started = False

    @property
    def is_started(self):
        return self._is_started

    def set_parent(self, parent):
        self.parent = parent
        if parent is not None:
            new_lgr_name = f'{self.name}.{self.parent.name}'
        else:
            new_lgr_name = f'{self.name}'

        self._lgr.info(f'Setting logger name to {new_lgr_name}')
        self._lgr = utils.get_object_logger(__name__, new_lgr_name)

    @property
    def data_dtype(self):
        try:
            data_type = self.cfg.data_type
        except AttributeError:
            # if a config does not have a data type, use the default
            data_type = 'float64'
        return np.dtype(data_type)

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def open(self):
        self._queue = Queue()
        pass

    def is_open(self):
        return self.cfg is not None

    def close(self):
        self.stop()

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.name, self.cfg, classname=self.__class__.__name__)

    def read_config(self):
        PerfusionConfig.read_into_dataclass('hardware', self.name, self.cfg)
        self.open()

    def start(self):
        if self.is_started:
            self.stop()
        self.acq_start_ms = utils.get_epoch_ms()

    def stop(self):
        self._is_started = False

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

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()
