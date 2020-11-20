# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx

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

import pyHardware.pyAI as pyAI


class NIDAQ_AI(pyAI.AI):
    def __init__(self):
        super().__init__()
        self.__dev = None
        self._line = None
        self.__timeout = 1.0
        self.__task = None
        self._volts_min = 0
        self._volts_max = 5

    @property
    def devname(self):
        return f"/{self.__dev}/ai{self._line}"

    def _convert_to_units(self):
        data = super()._convert_to_units()
        return self.data_type(data)

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_ms / 1000.0
        samples_read = PyDAQmx.int32()
        self.__task.ReadAnalogF64(self.samples_per_read, sleep_time, DAQmx_Val_GroupByChannel, self._buffer,
                                  self.samples_per_read, PyDAQmx.byref(samples_read), None)
        self._buffer_t = time.perf_counter()

    def open(self, period_ms, buf_type=np.float64, data_type=np.float32, read_period_ms=500, line='None', dev='None', volts_min=0, volts_max=5,):
        self.__dev = dev
        self._line = line
        super().open(period_ms, buf_type, data_type, read_period_ms)
        try:
            if self.__task:
                self.close()

            self.__task = Task()
            self.__task.CreateAIVoltageChan(self.devname, None, DAQmx_Val_RSE, volts_min, volts_max, DAQmx_Val_Volts, None)
            self.__task.StartTask()
        except PyDAQmx.DAQError as e:
            print("Could not create AO Channel for {}".format(self.devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None
