# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

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

import pyHardware.pyAO as pyAO


class NIDAQ_AO(pyAO.AO):
    def __init__(self):
        super().__init__()
        self.__dev = None
        self.__timeout = 1.0
        self.__task = None

    @property
    def _devname(self):
        return f"/{self.__dev}/ao{self._line}"

    def open(self, line, period_ms, volt_range=[-10, 10], bits=12, dev=None):
        super().open(line, period_ms, volt_range, bits)
        self.__dev = dev
        try:
            if self.__task:
                self.close()

            self.__task = Task()
            self.__task.CreateAOVoltageChan(self._devname, None, self._volt_range[0], self._volt_range[1], DAQmx_Val_Volts, None)
            self.__task.StartTask()
        except PyDAQmx.DAQError as e:
            print("Could not create AO Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def set_voltage(self, volts):
        self.__task.WriteAnalogScalarF64(True, self.__timeout, volts, None)
        super().set_voltage(volts)
