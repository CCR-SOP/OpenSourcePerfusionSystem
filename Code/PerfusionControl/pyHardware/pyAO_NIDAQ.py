# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes

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
        self.__last_dc_val = None

    @property
    def _devname(self):
        return f"/{self.__dev}/ao{self._line}"

    def _calc_timeout(self):
        # NIDAQ WriteAnalog64 is a synchronous operation, so the main loop
        # should immediately write the next cycle of a sine wave immediately
        if self._Hz > 0:
            timeout = 0
        else:
            # for DC, the timeout can be longer as it really just needs to check
            # that if an new value was requested
            timeout = 0.25
        return timeout

    def _output_samples(self):
        # super()._output_samples()
        pass

    def open(self, line, period_ms, bits=12, dev=None):
        self.__dev = dev
        super().open(line, period_ms, bits)
        try:
            if self.__task:
                self.close()

            self.__task = Task()

            # NI USB-6009 does not support FuncGen Channels
            # self.__task.CreateAOFuncGenChan(self._devname, None, DAQmx_Val_Sine, self._Hz, self._volts_p2p, self._volts_offset)

            self.__task.CreateAOVoltageChan(self._devname, None, 0, 5, DAQmx_Val_Volts, None)
            self.__task.CfgSampClkTiming("", 100.0, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, 200)
        except PyDAQmx.DAQError as e:
            print("Could not create AO Func Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def __update_timing(self):
        if self.__task:
            buf_len = len(self._buffer)
            self.__task.StopTask()
            rate = 1.0 / (self._period_ms / 1000.0)
            self.__task.CfgSampClkTiming(None, rate,
                                         DAQmx_Val_Rising, DAQmx_Val_ContSamps,
                                         buf_len)

    def set_sine(self, volts_p2p, volts_offset, Hz):
        super().set_sine(volts_p2p, volts_offset, Hz)
        written = ctypes.c_int32(0)
        self.__task.StopTask()
        self.__task.WriteAnalogF64(len(self._buffer), True, 2.0, DAQmx_Val_GroupByChannel,
                                   self._buffer, PyDAQmx.byref(written), None)
        # self.__update_timing()

    def set_dc(self, volts):
        self.__last_dc_val = None
        super().set_dc(volts)
        self.__task.WriteAnalogScalarF64(True, self.__timeout, self._volts_offset, None)
        # self.__update_timing()
