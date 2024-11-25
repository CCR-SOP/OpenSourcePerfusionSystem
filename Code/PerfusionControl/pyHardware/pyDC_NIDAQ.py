# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

Only supports DC tasks

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes

import PyDAQmx
import PyDAQmx.DAQmxConstants
import numpy as np

import pyHardware.pyDC as pyDC


class NIDAQDCDevice(pyDC.DCDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self._task = None
        self.__timeout = 1.0
        self.buf_dtype = np.dtype(np.float64)

    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        if self.cfg:
            dev_str = f'{self.cfg.device}/ao{self.cfg.line}'
        else:
            dev_str = 'None'
        return dev_str

    def open(self):
        super().open()
        self._open_task()

    def _open_task(self):
        self._task = PyDAQmx.Task()
        try:
            devname = self.devname
            self._task.CreateAOVoltageChan(devname, None, 0, 5,
                                           PyDAQmx.DAQmxConstants.DAQmx_Val_Volts, None)
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self.cfg.device}". Please ensure device is '\
                  f'plugged in and assigned the correct device name'
            self._lgr.exception(msg)
            raise(pyDC.DCDeviceException(msg))
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.cfg.line}" does not exist on device {self.cfg.device}'
            self._lgr.exception(msg)
            raise(pyDC.DCDeviceException(msg))
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            if self.cfg:
                name = self.cfg.device
            else:
                name = 'None'
            msg = f'Device "{name}" is not a valid device ID'
            self._lgr.exception(msg)
            raise(pyDC.DCDeviceException(msg))

    def set_output(self, output_volts: float):
        super().set_output(output_volts)
        self._open_task()
        try:
            written = ctypes.c_int32(0)
            self._task.WriteAnalogF64(len(self._buffer), True, self.__timeout * 5, PyDAQmx.DAQmx_Val_GroupByChannel,
                                      self._buffer, PyDAQmx.byref(written), None)
        except PyDAQmx.DAQmxFunctions.PALResourceReservedError as e:
            msg = f'{self.cfg.device} is reserved. Check for an invalid config or output type'
            self._lgr.exception(msg)
