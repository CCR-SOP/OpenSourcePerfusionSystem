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
    def __init__(self, period_ms, volts_p2p, volts_offset):
        super().__init__(period_ms, buf_type=np.float64)
        self._dev = None
        self._line = None
        self.__timeout = 1.0
        self.__task = None
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset

    @property
    def _devname(self):
        return f"/{self._dev}/ai{self._line}"

    def _convert_to_units(self):
        data = super()._convert_to_units()
        return self.data_type(data)

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        samples_read = PyDAQmx.int32()
        self.__task.ReadAnalogF64(self.samples_per_read, sleep_time, DAQmx_Val_GroupByChannel, self._buffer,
                                  self.samples_per_read, PyDAQmx.byref(samples_read), None)
        self._buffer_t = time.perf_counter()

    def open(self, dev, line):
        super().open()
        self._dev = dev
        self._line = line
        try:
            if self.__task:
                self.close()

            self.__task = Task()
            volt_min = self._volts_offset - 0.5 * self._volts_p2p
            volt_max = self._volts_offset + 0.5 * self._volts_p2p
            self.__task.CreateAIVoltageChan(self._devname, None, DAQmx_Val_RSE, volt_min, volt_max, DAQmx_Val_Volts, None)
            hz = 1.0 / (self._period_sampling_ms / 1000.0)
            self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                         self.samples_per_read)
        except PyDAQmx.DAQError as e:
            print("Could not create AO Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def start(self):
        if self.__task:
            self.__task.StartTask()
        super().start()

    def stop(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None
