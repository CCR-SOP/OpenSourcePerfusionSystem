# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes

import PyDAQmx
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAO as pyAO


class NIDAQ_AO(pyAO.AO):
    def __init__(self):
        super().__init__()
        self.__dev = None
        self.__timeout = 1.0
        self.__task = None
        self.__last_dc_val = None

    @property
    def _devname(self):
        return f"/{self.__dev}/ao{self._line}"

    def _output_samples(self):
        # super()._output_samples()
        pass

    def open(self, line, period_ms, bits=12, dev=None):
        self.__dev = dev
        super().open(line, period_ms, bits)
        self.__task = PyDAQmx.Task()

    def close(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def __clear_and_create_task(self):
        self.__task.StopTask()
        self.__task.ClearTask()
        self.__task = PyDAQmx.Task()
        self.__task.CreateAOVoltageChan(self._devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)

    def set_sine(self, volts_p2p, volts_offset, Hz):
        super().set_sine(volts_p2p, volts_offset, Hz)
        written = ctypes.c_int32(0)
        self.__clear_and_create_task()
        hz = 1.0 / (self._period_ms / 1000.0)
        self.__task.CfgSampClkTiming("", hz,
                                     PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, len(self._buffer))
        self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                   self._buffer, PyDAQmx.byref(written), None)

    def set_dc(self, volts):
        self.__last_dc_val = None
        super().set_dc(volts)
        self.__clear_and_create_task()
        self.__task.WriteAnalogScalarF64(True, self.__timeout, self._volts_offset, None)
