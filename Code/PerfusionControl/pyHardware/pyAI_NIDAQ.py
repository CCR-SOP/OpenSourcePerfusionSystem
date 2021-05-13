# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx
This work was created by an employee of the US Federal Gov
and under the public domain.
Author: John Kakareka
"""

import time
from datetime import datetime
import logging
import ctypes

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAI as pyAI


class NIDAQ_AI(pyAI.AI):
    def __init__(self, period_ms, volts_p2p, volts_offset):
        super().__init__(period_ms, buf_type=np.float32)
        self._logger = logging.getLogger(__name__)
        self._dev = None
        self._line = None
        self.__timeout = 1.0
        self._task = None
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._exception_msg_ack = False
        self._last_acq = None
        self._acq_buf = None
        self._acq_type = np.float64
        self._sample_mode = PyDAQmx.DAQmx_Val_ContSamps

    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = self.get_ids()
        if len(lines) == 0:
            dev_str = f'{self._dev}/ai'
        else:
            dev_str = ','.join([f'{self._dev}/ai{line}' for line in lines])
        return dev_str

    def is_open(self):
        # if channels were added and _dev is valid, then we have
        # confirmed that the device is present and the configuration
        # is valid
        return self._dev and super().is_open()

    def _convert_to_units(self, buffer, channel):
        data = super()._convert_to_units(buffer, channel)
        return self.data_type(data)

    def set_calibration(self, ch, low_pt, low_read, high_pt, high_read):
        super().set_calibration(ch, low_pt, low_read, high_pt, high_read)

    def _acq_samples(self):
        samples_read = PyDAQmx.int32()
        buffer_t = time.perf_counter()
        try:
            if self._task and len(self.get_ids()) > 0:
                self._task.ReadAnalogF64(self.samples_per_read, self._read_period_ms / 1000.0, DAQmx_Val_GroupByChannel,
                                         self._acq_buf, len(self._acq_buf), PyDAQmx.byref(samples_read), None)
        except PyDAQmx.ReadBufferTooSmallError:
            self._logger.error(f'ReadBufferTooSmallError when reading {self.devname}')
            self._logger.error(f'Samples/read = {self.samples_per_read}, '
                               f'Acq Buffer len = {len(self._acq_buf)}, '
                               f'Total channels = {len(self.get_ids())}')
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError:
            self._logger.error(f'Attempt to acquire data from {self.devname} before channels were added')
        else:
            offset = 0
            for ch in self.get_ids():
                buf = self.data_type(self._acq_buf[offset:offset+self.samples_per_read])
                if len(self._calibration[ch]):  # If the ai channel has been calibrated:
                    buf = self._convert_to_units(buf, ch)
                with self._lock_buf:
                    self._queue_buffer[ch].put((buf, buffer_t))
                offset += self.samples_per_read

    def _is_valid_device_name(self, device):
        try:
            bytes_needed = PyDAQmx.DAQmxGetSysDevNames(None, 0)
        except PyDAQmx.DAQError as e:
            self._logger.error('Error occurred trying to get valid NIDAQ device names')
            self._logger.error(f'Error is {str(e)}')
            return False
        else:
            dev_names = ctypes.create_string_buffer(bytes_needed)
            PyDAQmx.DAQmxGetSysDevNames(dev_names, bytes_needed)
            self._logger.debug(f'Device="{device}", devnames={str(ctypes.string_at(dev_names))}')
            self._logger.debug(f'valid device: {device in str(ctypes.string_at(dev_names))}')
            return device and device in str(ctypes.string_at(dev_names))

    def open(self, dev=None):
        """ Open a pyAI_NIDAQ device
            dev: the name of a valid NI device
        """
        if self._is_valid_device_name(dev):
            self._logger.debug(f'Opening device "{dev}"')
            self._dev = dev
            self._task = Task()
            super().open()
        else:
            msg = f'Device "{dev}" is not a valid device name on this system. ' \
                  f'Please check that the hardware had been plugged in and the correct' \
                  f'device name has been used'
            self._logger.error(msg)
            raise pyAI.AIDeviceException(msg)

    def add_channel(self, channel_id):
        if channel_id in self.get_ids():
            self._logger.warning(f'Channel {channel_id} already exists')
            return
        if not self._task:
            raise pyAI.AIDeviceException(f'Cannot add channel {channel_id}, device {self._dev} not yet opened')
        super().add_channel(channel_id)
        try:
            self._logger.debug(f'Creating new pyDAQmx AI Voltage Channel for {self.devname}')
            self._update_task()
        except pyAI.AIDeviceException:
            super().remove_channel(channel_id)
            raise

    def remove_channel(self, channel_id):
        if channel_id not in self.get_ids():
            self._logger.warning(f'Channel {channel_id} does not exist')
            return
        if not self._task:
            raise pyAI.AIDeviceException(f'Cannot remove channel {channel_id}, device {self._dev} not yet opened')
        super().remove_channel(channel_id)
        self._update_task()

    def _update_task(self):
        cleanup = True
        msg = ''
        try:
            if self._dev and len(self.get_ids()) > 0:
                if self._task:
                    self._task.ClearTask()
                    self._task = Task()

                volt_min = self._volts_offset - 0.5 * self._volts_p2p
                volt_max = self._volts_offset + 0.5 * self._volts_p2p
                self._task.CreateAIVoltageChan(self.devname, None, DAQmx_Val_RSE, volt_min, volt_max, DAQmx_Val_Volts, None)
                hz = 1.0 / (self._period_sampling_ms / 1000.0)
                self._task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, self._sample_mode, self.samples_per_read)
            cleanup = False
        except PyDAQmx.DevCannotBeAccessedError as e:
            msg = f'Could not access device "{self._dev}". Please ensure device is ' \
                  f'plugged in and assigned the correct device name'
            self._logger.error(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.get_ids()}" does not exist on device {self._dev}'
            self._logger.error(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChannelNotSpecifiedError:
            msg = f'A input channel/line must be specified.'
            self._logger.error(msg)
            self._logger.error(f'task is {self._task}')

        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self.devname}" is not a valid device ID'
            self._logger.error(msg)
        except PyDAQmx.DAQmxFunctions.InvalidTaskError:
            msg = f'Invalid task for {self.devname}'
            self._logger.error(msg)
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError:
            msg = f'No channels added for {self.devname}'
            self._logger.error(msg)
        finally:
            if cleanup:
                raise pyAI.AIDeviceException(msg)

    def close(self):
        self.stop()
        self._task.ClearTask()
        self._task = None

    def start(self):
        if self._task:
            ch_ids = self.get_ids()
            self._acq_buf = np.zeros(self.samples_per_read * len(ch_ids), dtype=self._acq_type)
            self._task.StartTask()
            super().start()

    def stop(self):
        super().stop()
        if self._task:
            self._task.StopTask()
            self._task.WaitUntilTaskDone(2.0)
