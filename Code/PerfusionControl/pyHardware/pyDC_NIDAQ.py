# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AO through NIDAQmx

Only supports DC tasks

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import ctypes
import logging

import PyDAQmx
import PyDAQmx.DAQmxConstants

import pyHardware.pyDC as pyDC


class NIDAQDCDevice(pyDC.DCDevice):
    def __init__(self):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self._task = None
        self.__timeout = 1.0

    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        if self.cfg:
            dev_str = f'{self.cfg.Device}/ao{self.cfg.LineName}'
        else:
            dev_str = 'None'
        return dev_str

    def open(self, cfg: pyDC.DCChannelConfig):
        super().open()
        self._open_task()

    def _open_task(self):
        self._task = PyDAQmx.Task()
        try:
            devname = self.devname
            self._lgr.debug(f'devname is {devname}')
            self._task.CreateAOVoltageChan(devname, None, 0, 5,
                                           PyDAQmx.DAQmxConstants.DAQmx_Val_Volts, None)
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self.device.cfg.Device}". Please ensure device is '\
                  f'plugged in and assigned the correct device name'
            self._lgr.error(msg)
            raise(pyDC.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.cfg.LineName}" does not exist on device {self.device.cfg.Device}'
            self._lgr.error(msg)
            raise(pyDC.AODeviceException(msg))
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            if self.cfg:
                name = self.cfg.Device
            else:
                name = 'None'
            msg = f'Device "{name}" is not a valid device ID'
            self._lgr.error(msg)
            raise(pyDC.DCDeviceException(msg))

    def set_output(self, output_volts: float):
        super().set_output(output_volts)
        self._open_task()
        self._lgr.debug(f'output is {output_volts} V')
        try:
            written = ctypes.c_int32(0)
            self._task.WriteAnalogF64(len(self._buffer), True, self.__timeout * 5, PyDAQmx.DAQmx_Val_GroupByChannel,
                                      self._buffer, PyDAQmx.byref(written), None)
        except PyDAQmx.DAQmxFunctions.PALResourceReservedError as e:
            msg = f'{self.device.cfg.Device} is reserved. Check for an invalid config or output type'
            self._lgr.error(msg)
            self._lgr.error(e)
