# -*- coding: utf-8 -*-
"""Provides concrete class for controlling DIO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import logging

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyDIO as pyDIO


class NIDAQ_DIO(pyDIO.DIO):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        super().__init__()
        self.__dev = None
        self.__timeout = 1.0
        self.__task = None

    @property
    def _devname(self):
        return f"/{self.__dev}/{self._port}/{self._line}"

    def open(self, port, line, active_high=True, read_only=True, dev=None):
        self.__dev = dev
        super().open(port, line, active_high, read_only)
        try:
            if self.__task:
                self.close()

            self.__task = Task()
            if self._read_only:
                self.__task.CreateDIChan(self._devname, '', DAQmx_Val_ChanPerLine)
            else:
                self.__task.CreateDOChan(self._devname, '', DAQmx_Val_ChanPerLine)
            self.__task.StartTask()
        except PyDAQmx.DAQError as e:
            self._logger.error("Could not create DI Channel for {}".format(self._devname))
            self._logger.error(f"{e}")
            self.__task = None

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def _activate(self):
        data = np.array([self._active_state.ACTIVE], dtype=np.uint8)
        self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
        super()._activate()
        self._logger.debug(f"activated channel {self._devname}')

    def _deactivate(self):
        data = np.array([self._active_state.INACTIVE], dtype=np.uint8)
        self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
        super()._deactivate()

        print("deactivated channel")

    def is_open(self):
        return self.__task

