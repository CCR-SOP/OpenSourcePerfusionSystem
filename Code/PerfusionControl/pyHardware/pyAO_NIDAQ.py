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
    def __init__(self, name=''):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.name = name
        self._dev = None
        self._line = None
        self.__timeout = 1.0
        self.__task = None
        self.__max_accel = 1  # Volts/second
        self.__hw_clk = False

    @property
    def devname(self):
        return f"/{self._dev}/ao{self._line}"

    def _output_samples(self):
        # super()._output_samples()
        pass

    def is_open(self):
        return self.__task is not None

    def open(self, period_ms, bits=12, dev=None, line=None):
        self._dev = dev
        self._line = line
        super().open(period_ms, bits)
        self.__check_hw_clk_support()
        self.__task = PyDAQmx.Task()

    def close(self):
        self.stop()

    # no need to override start() as NIDAQ hardware does not require
    # task to be explicitly started
    def stop(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None
        super().stop()

    def _open_task(self, task):
        try:
            task.CreateAOVoltageChan(self.devname, None, 0, 5, PyDAQmx.DAQmx_Val_Volts, None)
            self.__hw_clk = True
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self._dev}". Please ensure device is '\
                  f'plugged in and assigned the correct device name'
            self._logger.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self._line}" does not exist on device {self._dev}'
            self._logger.error(msg)
            raise(pyAO.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self._dev}" is not a valid device ID'
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
            self._logger.info(f'Hardware clock {phrase} supported for {self.devname}')

    def wait_for_task(self):
        if self.__task:
            self.__task.WaitUntilTaskDone(10.0)

    def __clear_and_create_task(self):
        if self.__task:
            self.__task.StopTask()
            self.__task.ClearTask()
        self.__task = PyDAQmx.Task()
        try:
            self._open_task(self.__task)
        except pyAO.AODeviceException as e:
            self.__task = None
            raise

    def set_sine(self, volts_p2p, volts_offset, Hz):
        if self.__hw_clk:
            super().set_sine(volts_p2p, volts_offset, Hz)
            written = ctypes.c_int32(0)
            self.__clear_and_create_task()
            hz = 1.0 / (self._period_ms / 1000.0)
            if self.__task:
                try:
                    self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                                 len(self._buffer))
                    self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout,
                                               PyDAQmx.DAQmx_Val_GroupByChannel,
                                               self._buffer, PyDAQmx.byref(written), None)
                except PyDAQmx.DAQmxFunctions.InvalidAttributeValueError as e:
                    msg = f'{self.devname} does not support hardware sampling {self._dev} required for sine output'
                    self._lgr.error(msg)
        else:
            msg = f'Attempted to setup up sine wave output which is unsupported on {self.devname}'
            self._logger.error(msg)
            raise pyAO.AODeviceException(msg)

    def set_dc(self, volts):
        try:
            self.__clear_and_create_task()
        except pyAO.AODeviceException as e:
            raise
        else:
            if self.__task:
                super().set_ramp(self._volts_offset, volts, self.__max_accel)
                written = ctypes.c_int32(0)
                self.__task.WriteAnalogF64(len(self._buffer), True, self.__timeout, PyDAQmx.DAQmx_Val_GroupByChannel,
                                           self._buffer, PyDAQmx.byref(written), None)
                super().set_dc(volts)

