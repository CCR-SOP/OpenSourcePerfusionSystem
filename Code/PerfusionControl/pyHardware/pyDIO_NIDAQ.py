# -*- coding: utf-8 -*-
"""Provides concrete class for controlling DIO through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import logging

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyDIO as pyDIO


class NIDAQ_DIO(pyDIO.DIO):
    def __init__(self, name: str = None):
        super().__init__(name)
        self._logger = logging.getLogger(__name__)
        self._dev = None
        self.__timeout = 1.0
        self.__task = None

    @property
    def devname(self):
        return f"/{self._dev}/{self._port}/{self._line}"

    @property
    def is_open(self):
        return self.__task is not None

    def open(self, port, line, active_high=True, read_only=True, dev=None):
        self._dev = dev
        cleanup = True
        super().open(port, line, active_high, read_only)
        if self.__task:
            self.close()
        task = None
        try:
            task = Task()
            if self._read_only:
                task.CreateDIChan(self.devname, '', DAQmx_Val_ChanPerLine)
            else:
                task.CreateDOChan(self.devname, '', DAQmx_Val_ChanPerLine)
            cleanup = False
            self._logger.debug('successfully opened device')
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self._dev}". Please ensure device is ' \
                  f'plugged in and assigned the correct device name'
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self._line}" on "{self._port}" does not exist on device "{self._dev}"'
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self._dev}" is not a valid device ID'
        except PyDAQmx.DAQmxFunctions.InvalidOptionForDigitalPortChannelError:
            msg = f'Need to specify specific lines/channels in addition to a port for {self._dev} and {self._port}'
        finally:
            if cleanup:
                self.__task = None
                self._logger.error(msg)
                raise (pyDIO.DIODeviceException(msg))
        self.__task = task
        cleanup = True
        msg = ''
        try:
            self.__task.StartTask()
            cleanup = False
        except PyDAQmx.DAQmxFunctions.DigitalOutputNotSupportedError:
            msg = f'Channel {self.devname} is read (input) only'
        except PyDAQmx.DAQmxFunctions.DigInputNotSupportedError:
            msg = f'Channel {self.devname} is output only'
        finally:
            if cleanup:
                self.__task = None
                self._logger.error(msg)
                raise (pyDIO.DIODeviceException(msg))

    def close(self):
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def _activate(self):
        data = np.array([self._active_state.ACTIVE], dtype=np.uint8)
        if self.__task:
            # self._logger.debug(f'activating {self.devname}')
            self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
            super()._activate()

    def _deactivate(self):
        data = np.array([self._active_state.INACTIVE], dtype=np.uint8)
        if self.__task:
            self.__task.WriteDigitalLines(1, True, self.__timeout, DAQmx_Val_GroupByChannel, data, None, None)
            super()._deactivate()
