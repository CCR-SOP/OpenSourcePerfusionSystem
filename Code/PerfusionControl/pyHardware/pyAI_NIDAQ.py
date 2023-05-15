# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx

Derived from pyAI base class

Requires numpy library

Sample buffers are read periodically from the hardware and stored in a Queue for later processing. This helps to ensure
that no samples are dropped from the hardware due to slow processing. There is one queue per analog input line/channel


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import ctypes
from dataclasses import dataclass

import numpy as np
import PyDAQmx
from PyDAQmx import Task
import PyDAQmx.DAQmxConstants 

import pyHardware.pyAI as pyAI
import pyPerfusion.utils as utils


@dataclass
class AINIDAQDeviceConfig(pyAI.AIDeviceConfig):
    pk2pk_volts: float = 5.0
    offset_volts: float = 2.5


class NIDAQAIDevice(pyAI.AIDevice):
    def __init__(self, name: str):
        super().__init__(name)

        self.cfg = AINIDAQDeviceConfig()
        self.buf_dtype = np.float64
        self.__timeout = 1.0
        self._task = None
        self._exception_msg_ack = False
        self._last_acq = None
        self._acq_buf = None
        self._sample_mode = PyDAQmx.DAQmx_Val_ContSamps

    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = [ch.cfg.line for ch in self.ai_channels]
        if len(lines) == 0:
            dev_str = f'{self.cfg.device_name}/ai'
        else:
            dev_str = f','.join([f'{self.cfg.device_name}/ai{line}' for line in lines])
        return dev_str

    def is_open(self):
        # if channels were added and device name is valid, then we have
        # confirmed that the device is present and the configuration
        # is valid
        return self.cfg.device_name and super().is_open()

    def _acq_samples(self):
        samples_read = PyDAQmx.int32()
        buffer_t = utils.get_epoch_ms() - self.get_acq_start_ms()
        try:
            if self._task and len(self.ai_channels) > 0:
                self._task.ReadAnalogF64(self.samples_per_read, 1.05 * self.cfg.read_period_ms / 1000.0,
                                         PyDAQmx.DAQmxConstants.DAQmx_Val_GroupByChannel,
                                         self._acq_buf, len(self._acq_buf), PyDAQmx.byref(samples_read), None)

                offset = 0
                for ch in self.ai_channels:
                    buf = self._acq_buf[offset:offset + self.samples_per_read]
                    ch.put_data(buf, buffer_t)
                    offset += self.samples_per_read
        except PyDAQmx.ReadBufferTooSmallError:
            self._lgr.exception(f'ReadBufferTooSmallError when reading {self.devname}')
            self._lgr.error(f'Samples/read = {self.samples_per_read}, '
                            f'Acq Buffer len = {len(self._acq_buf)}, '
                            f'Total channels = {len(self.ai_channels)}')
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError as e:
            self._lgr.exception(f'Attempt to acquire data from {self.devname} before channels were added')
        except PyDAQmx.DAQmxFunctions.WaitUntilDoneDoesNotIndicateDoneError:
            self._lgr.exception(f'For device {self.name}, read not completed before timeout in _acq_samples.')
        except PyDAQmx.DAQmxFunctions.InvalidTaskError:
            self._lgr.exception(f'For device {self.name}, invalid task error in _acq_samples.')


    def _is_valid_device_name(self, device):
        try:
            bytes_needed = PyDAQmx.DAQmxGetSysDevNames(None, 0)
        except PyDAQmx.DAQError:
            self._lgr.exception('Error occurred trying to get valid NIDAQ device names')
            return False
        else:
            dev_names = ctypes.create_string_buffer(bytes_needed)
            PyDAQmx.DAQmxGetSysDevNames(dev_names, bytes_needed)
            return device and device in str(ctypes.string_at(dev_names))

    def _update_task(self):
        cleanup = True
        msg = ''
        try:
            if self.cfg.device_name and len(self.ai_channels) > 0:
                if self._task:
                    self._task.ClearTask()
                    self._task = Task()

                volt_min = self.cfg.offset_volts - 0.5 * self.cfg.pk2pk_volts
                volt_max = self.cfg.offset_volts + 0.5 * self.cfg.pk2pk_volts

                self._task.CreateAIVoltageChan(self.devname, None, PyDAQmx.DAQmxConstants.DAQmx_Val_RSE,
                                               volt_min, volt_max, PyDAQmx.DAQmxConstants.DAQmx_Val_Volts, None)
                hz = 1.0 / (self.cfg.sampling_period_ms / 1000.0)
                self._task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, self._sample_mode, self.samples_per_read)
            cleanup = False
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self.cfg.device_name}". Please ensure device is ' \
                  f'plugged in and assigned the correct device name'
            self._lgr.exception(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.ai_channels.keys()}" does not exist on device {self.cfg.device_name}'
            self._lgr.exception(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChannelNotSpecifiedError:
            msg = f'A input channel/line must be specified.'
            self._lgr.exception(msg)
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self.devname}" is not a valid device ID'
            self._lgr.exception(msg)
        except PyDAQmx.DAQmxFunctions.InvalidTaskError:
            msg = f'Invalid task for {self.devname}'
            self._lgr.exception(msg)
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError:
            msg = f'No channels added for {self.devname}'
            self._lgr.exception(msg)
        except Exception as e:
            msg = f'Generic exception for {self.devname}'
            self._lgr.exception(e)
        finally:
            if cleanup:
                raise pyAI.AIDeviceException(msg)

    def remove_channel(self, name: str):
        if not self._task:
            raise pyAI.AIDeviceException(f'Cannot remove channel {name}, device {self.cfg.device_name} not yet opened')
        acquiring = self.is_acquiring
        self.stop()
        super().remove_channel(name)
        self._update_task()
        if acquiring:
            self.start()

    def open(self):
        """ Open a pyAI_NIDAQ device
            dev: the name of a valid NI device
        """
        self._task = Task()

        # ensure the buffer type is float64 for NIDAQ devices
        self.cfg.buf_type = 'float64'
        super().open()
        if not self._is_valid_device_name(self.cfg.device_name):
            msg = f'Device "{self.cfg.device_name}" is not a valid device name on this system. ' \
                  f'Please check that the hardware had been plugged in and the correct' \
                  f'device name has been used'
            self._lgr.error(msg)
            raise pyAI.AIDeviceException(msg)

    def close(self):
        self.stop()
        if self._task:
            self._task.ClearTask()
        self._task = None

    def start(self):
        if self._task:
            self._acq_buf = np.zeros(self.samples_per_read * len(self.ai_channels),
                                     dtype=self.buf_dtype)

            self._update_task()
            self._task.StartTask()
            super().start()

    def stop(self):
        if self._task:
            self._task.StopTask()
            try:
                self._task.WaitUntilTaskDone(2.0)
            except PyDAQmx.DAQmxFunctions.WaitUntilDoneDoesNotIndicateDoneError:
                self._lgr.warning(f'For device {self.name}, read not completed before timeout.')
        super().stop()
