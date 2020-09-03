# -*- coding: utf-8 -*-
"""Provides concrete class for controlling DIO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""

import time
import threading

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyDIO as pyDIO


class NIDAQ_DIO(pyDIO.DIO):
    def __init__(self, port, line, active_high=True, read_only=True, dev=None):
        super().__init__(port, line, active_high, read_only)
        self.__dev = dev
        self.__timeout = 1.0
        self.__task = None

    @property
    def _devname(self):
        return f"/{self.__dev}/{self._port}/{self._line}"

    def open(self):
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
            print("Could not create DI Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def _activate(self):
        data = np.array([1], dtype=np.uint8)
        self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
        print("activated channel")

    def _deactivate(self):
        data = np.array([0], dtype=np.uint8)
        self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
        print("activated channel")
