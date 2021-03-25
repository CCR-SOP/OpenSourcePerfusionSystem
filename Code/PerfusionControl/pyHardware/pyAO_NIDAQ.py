# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes
import logging

import PyDAQmx
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAO as pyAO


class NIDAQ_AO(pyAO.AO):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
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
        self.__check_hw_clk_support()

    def __check_hw_clk_support(self):
        task = PyDAQmx.Task()
        task.CreateAOVoltageChan(self._devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)
        try:
            self.__hw_clk = True
            task.CfgSampClkTiming("", 1.0, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, 10)
        except PyDAQmx.DAQmxFunctions.InvalidAttributeValueError:
            self.__hw_clk = False

        task.StopTask()
        task.ClearTask()
        if self.__hw_clk:
            phrase = 'is'
        else:
            phrase = 'is not'
        self._logger.info(f'Hardware clock {phrase} supported for {self._devname}')

    def wait_for_task(self):
        if self.__task:
            self.__task.WaitUntilTaskDone(10.0)

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
        self.__clear_and_create_task()
        super().set_ramp(self._volts_offset, volts, self.__max_accel)
        hz = 1.0 / (self._period_ms / 1000.0)
        written = ctypes.c_int32(0)
        # if self.__hw_clk and len(self._buffer) > 1:
            # self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_FiniteSamps, len(self._buffer))
        self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                   self._buffer, PyDAQmx.byref(written), None)
        super().set_dc(volts)
