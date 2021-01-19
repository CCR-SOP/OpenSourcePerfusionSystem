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

    def _output_samples(self):
        # super()._output_samples()
        if self._Hz > 0.0:
            written = ctypes.c_int32()
            self.__task.WriteAnalogF64(len(self._buffer), True, 1.0 / self._Hz, DAQmx_Val_GroupByChannel, self._buffer, PyDAQmx.byref(written), None)
        else:
            if self._volts_offset != self.__last_dc_val:
                self.__task.WriteAnalogScalarF64(True, self.__timeout, self._volts_offset, None)
                self.__last_dc_val = self._volts_offset

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
            self.__task.StartTask()
        except PyDAQmx.DAQError as e:
            print("Could not create AO Func Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        self.halt()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def set_sine(self, volts_p2p, volts_offset, Hz):
        super().set_sine(volts_p2p, volts_offset, Hz)

    def set_dc(self, volts):
        self.__last_dc_val = None
        super().set_dc(volts)
