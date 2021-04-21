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

    def is_open(self):
        return self.__task is not None

    def open(self, period_ms, bits=12, dev=None, line=None):
        self.__dev = dev
        self.__line = line
        super().open(period_ms, bits)
        self.__check_hw_clk_support()

    def _open_task(self, task):
        try:
            task.CreateAOVoltageChan(self._devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)
            self.__hw_clk = True
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self.__dev}". Please ensure device is '\
                  f'plugged in and assigned the correct device name'
            self._logger.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.__line}" does not exist on device {self.__dev}'
            self._logger.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self.__dev}" is not a valid device ID'
            self._logger.error(msg)
            raise(pyAO.AODeviceException(msg))

    def __check_hw_clk_support(self):
        task = PyDAQmx.Task()
        try:
            self._open_task(task)
        except pyAO.AODeviceException as e:
            self.__hw_clk = False
            raise
        else:
            try:
                task.CfgSampClkTiming("", 1.0, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, 10)
                self.__hw_clk = True
            except PyDAQmx.DAQmxFunctions.InvalidAttributeValueError:
                self.__hw_clk = False

            task.StopTask()
            task.ClearTask()
            phrase = 'is' if self.__hw_clk else 'is not'
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
        try:
            self.__task.CreateAOVoltageChan(self._devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)
        except PyDAQmx.DevCannotBeAccessedError as e:
            self._logger.error(f'Could not access device {self.__dev}. Please ensure device is'
                               f'plugged in and assigned the correct device name')
            self.__task = None
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            self._logger.error(f'Channel {self.__line} does not exist on device {self.__dev}')
            self.__task = None

    def set_sine(self, volts_p2p, volts_offset, Hz):
        if self.__hw_clk:
            super().set_sine(volts_p2p, volts_offset, Hz)
            written = ctypes.c_int32(0)
            self.__clear_and_create_task()
            hz = 1.0 / (self._period_ms / 1000.0)
            if self.__task:
                self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                            len(self._buffer))
                self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                            self._buffer, PyDAQmx.byref(written), None)
        else:
            msg = f'Attempted to setup up sine wave output which is unsupported on {self._devname}'
            self._logger.error(msg)
            raise pyAO.AODeviceException(msg)

    def set_dc(self, volts):
        self.__clear_and_create_task()
        if self.__task:
            super().set_ramp(self._volts_offset, volts, self.__max_accel)
            written = ctypes.c_int32(0)
            self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                       self._buffer, PyDAQmx.byref(written), None)
            super().set_dc(volts)

