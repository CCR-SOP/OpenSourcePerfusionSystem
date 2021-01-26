# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes
from time import sleep

import PyDAQmx
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAO as pyAO


class NIDAQ_AO(pyAO.AO):
    def __init__(self):
        super().__init__()
        self.__dev = None
        self.__line = None
        self.__timeout = 1.0
        self.__task = None
        self.__max_accel = 1  # Volts/second
        self.__hw_clk = False

    @property
    def _devname(self):
        return f"/{self.__dev}/ao{self.__line}"

    def _output_samples(self):
        # super()._output_samples()
        pass

    def open(self, period_ms, bits=12, dev=None, line=None):
        self.__dev = dev
        self.__line = line
        super().open(period_ms, bits)
        self.__task = PyDAQmx.Task()


    def close(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def __clear_and_create_task(self):
        if self.__task:
            self.__task.StopTask()
            self.__task.ClearTask()
            self.__task = PyDAQmx.Task()
            self.__task.CreateAOVoltageChan(self._devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)
            err = self.__task.CfgSampClkTiming("", 1.0, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, 10)
            self.__hw_clk = err == 0
            if self.__hw_clk:
                print('Hardware clock supported')
            else:
                print('Hardware clock not supported')

    def set_sine(self, volts_p2p, volts_offset, Hz):
        super().set_sine(volts_p2p, volts_offset, Hz)
        written = ctypes.c_int32(0)
        self.__clear_and_create_task()
        hz = 1.0 / (self._period_ms / 1000.0)
        if self.__task:
            self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                         len(self._buffer))
            self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                       self._buffer, PyDAQmx.byref(written), None)

    def set_dc(self, volts):
        if self.__task:
            self.__clear_and_create_task()

            super().set_ramp(self._volts_offset, volts, 1.0)
            hz = 1.0 / (self._period_ms / 1000.0)
            written = ctypes.c_int32(0)
            if self.__hw_clk and len(self._buffer) > 0:
                self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_FiniteSamps, len(self._buffer))
                self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                           self._buffer, PyDAQmx.byref(written), None)
            else:
                self.__task.WriteAnalogScalarF64(True, self.__timeout, volts, None)
            super().set_dc(volts)

