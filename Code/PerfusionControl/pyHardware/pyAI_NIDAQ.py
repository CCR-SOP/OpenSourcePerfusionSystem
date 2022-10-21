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
import time
import logging
import ctypes
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import PyDAQmx
from PyDAQmx import Task
import PyDAQmx.DAQmxConstants 

import pyHardware.pyAI as pyAI


@dataclass
class AINIDAQDeviceConfig(pyAI.AIDeviceConfig):
    pk2pk_volts: float = 5.0
    offset_volts: float = 2.5
    # override the default buffer type to match how
    # NIDAQ devices return data
    buf_type: npt.DTypeLike = np.dtype(np.float64).name


class NIDAQAIDevice(pyAI.AIDevice):
    def __init__(self):
        super().__init__()
        self._lgr = logging.getLogger(__name__)
        self.__timeout = 1.0
        self._task = None
        self._exception_msg_ack = False
        self._last_acq = None
        self._acq_buf = None
        self._sample_mode = PyDAQmx.DAQmx_Val_ContSamps

    # def read_config(self):
    #     info = PerfusionConfig.read_section(self.cfg.name, 'General')
    #     self.cfg = AINIDAQDeviceConfig(**info)
    #     for ch_name, ch_cfg in self.cfg.ch_info.items():
    #         self.add_channel(ch_cfg, ch_cfg.line)


    @property
    def devname(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = [ch.cfg.line for ch in self.ai_channels.values()]
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
        buffer_t = time.perf_counter()
        try:
            if self._task and len(self.ai_channels) > 0:
                self._task.ReadAnalogF64(self.samples_per_read, 1.05 * self.cfg.read_period_ms / 1000.0,
                                         PyDAQmx.DAQmxConstants.DAQmx_Val_GroupByChannel,
                                         self._acq_buf, len(self._acq_buf), PyDAQmx.byref(samples_read), None)

                offset = 0
                for ch in self.ai_channels.values():
                    self._lgr.debug(f'_acq_samples: len(buf) = {len(self._acq_buf)}')
                    buf = self._acq_buf[offset:offset + self.samples_per_read]
                    ch.put_data(buf, buffer_t)
                    offset += self.samples_per_read
        except PyDAQmx.ReadBufferTooSmallError:
            self._lgr.error(f'ReadBufferTooSmallError when reading {self.devname}')
            self._lgr.error(f'Samples/read = {self.samples_per_read}, '
                           f'Acq Buffer len = {len(self._acq_buf)}, '
                           f'Total channels = {len(self.ai_channels)}')
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError:
            self._lgr.error(f'Attempt to acquire data from {self.devname} before channels were added')
        except PyDAQmx.DAQmxFunctions.WaitUntilDoneDoesNotIndicateDoneError:
            self._lgr.warning(f'For device {self.cfg.name}, read not completed before timeout in _acq_samples.')
        except PyDAQmx.DAQmxFunctions.InvalidTaskError:
            self._lgr.error(f'For device {self.cfg.name}, invalid task error in _acq_samples.')


    def _is_valid_device_name(self, device):
        try:
            bytes_needed = PyDAQmx.DAQmxGetSysDevNames(None, 0)
        except PyDAQmx.DAQError as e:
            self._lgr.error('Error occurred trying to get valid NIDAQ device names')
            self._lgr.error(f'Error is {str(e)}')
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
            self._lgr.error(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChanDoesNotExistError:
            msg = f'Channel "{self.ai_channels.keys()}" does not exist on device {self.cfg.device_name}'
            self._lgr.error(msg)
        except PyDAQmx.DAQmxFunctions.PhysicalChannelNotSpecifiedError:
            msg = f'A input channel/line must be specified.'
            self._lgr.error(msg)
            self._lgr.error(f'task is {self._task}')
        except PyDAQmx.DAQmxFunctions.InvalidDeviceIDError:
            msg = f'Device "{self.devname}" is not a valid device ID'
            self._lgr.error(msg)
        except PyDAQmx.DAQmxFunctions.InvalidTaskError:
            msg = f'Invalid task for {self.devname}'
            self._lgr.error(msg)
        except PyDAQmx.DAQmxFunctions.CanNotPerformOpWhenNoChansInTaskError:
            msg = f'No channels added for {self.devname}'
            self._lgr.error(msg)
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

    def open(self, cfg: AINIDAQDeviceConfig):
        """ Open a pyAI_NIDAQ device
            dev: the name of a valid NI device
        """
        self._task = Task()
        cfg.buf_type = np.float64
        super().open(cfg=cfg)
        if not self._is_valid_device_name(cfg.device_name):
            msg = f'Device "{cfg.device_name}" is not a valid device name on this system. ' \
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
                                     dtype='float64')
            self._update_task()
            self._task.StartTask()
            super().start()

    def stop(self):
        if self._task:
            self._task.StopTask()
            try:
                err = self._task.WaitUntilTaskDone(2.0)
            except PyDAQmx.DAQmxFunctions.WaitUntilDoneDoesNotIndicateDoneError:
                self._lgr.warning(f'For device {self.cfg.name}, read not completed before timeout.')
        super().stop()


