# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""

import time
import threading
import ctypes

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAOSine as pyAOSine


class NIDAQ_AOSine(pyAOSine.AOSine):
    def __init__(self, line, period_ms, volts_p2p, volts_offset, Hz, bits=12, dev=None):
        super().__init__(line, period_ms, volts_p2p, volts_offset, Hz, bits)
        self.__dev = dev
        self.__timeout = 1.0
        self.__task = None

    @property
    def _devname(self):
        return f"/{self.__dev}/ao{self._line}"

    def _output_samples(self):
        # super()._output_samples()
        written = ctypes.c_int32()
        self.__task.WriteAnalogF64(len(self._buffer), True, 1.0 / self._Hz, DAQmx_Val_GroupByChannel, self._buffer, PyDAQmx.byref(written), None)

    def open(self):
        # super().open()
        try:
            if self.__task:
                self.close()

            self.__task = Task()
            # NI USB-6009 does not support FuncGen Channels
            # self.__task.CreateAOFuncGenChan(self._devname, None, DAQmx_Val_Sine, self._Hz, self._volts_p2p, self._volts_offset)
            volt_min = self._volts_offset - 0.5 * self._volts_p2p
            volt_max = self._volts_offset + 0.5 * self._volts_p2p
            self.__task.CreateAOVoltageChan(self._devname, None, 0, 5, DAQmx_Val_Volts, None)
            self.__task.StartTask()
        except PyDAQmx.DAQError as e:
            print("Could not create AO Func Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def set_sine(self, volts_p2p, volts_offset, Hz):
        super().set_sine(volts_p2p, volts_offset, Hz)
        self.close()
        self.open()
