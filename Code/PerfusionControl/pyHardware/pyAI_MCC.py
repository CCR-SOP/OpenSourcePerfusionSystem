# -*- coding: utf-8 -*-
"""Provides concrete class for controlling MCC through mcculw

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
import time

import numpy as np
from mcculw import ul
from mcculw.enums import ScanOptions, ULRange, AnalogInputMode, FunctionType, Status
from mcculw.ul import ULError
from mcculw.device_info import DaqDeviceInfo

import pyHardware.pyAI as pyAI
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class AIMCCDeviceConfig(pyAI.AIDeviceConfig):
    ai_range: ULRange = ULRange.BIP10VOLTS


class MCCAIDevice(pyAI.AIDevice):
    def __init__(self, name: str):
        super().__init__(name)

        self.cfg = AIMCCDeviceConfig()
        self.buf_dtype = np.float64
        self.__timeout = 1.0
        self._task = None
        self._exception_msg_ack = False
        self._last_acq = None
        self._acq_buf = None
        self._chan_range = (-1, -1)
        self._scan_options = (ScanOptions.BACKGROUND |
                              ScanOptions.CONTINUOUS |
                              ScanOptions.BURSTMODE |
                              ScanOptions.SCALEDATA)

    def dev_info(self):
        # recreate from scratch so base naming convention does not need
        # to be consistent with actual hardware naming convention
        lines = [ch.cfg.line for ch in self.ai_channels]
        self._chan_range = (min(lines), max(lines))

    @property
    def total_channels(self):
        total_channels = self._chan_range[1] - self._chan_range[0] + 1
        return total_channels

    @property
    def acq_points(self):
        return self.total_channels * self.samples_per_read

    @property
    def board_num(self):
        return int(self.cfg.device_name)

    def is_open(self):
        # if channels were added and device name is valid, then we have
        # confirmed that the device is present and the configuration
        # is valid
        return self.cfg.device_name and super().is_open()

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            # period_timeout = 100
            #if not self._event_halt.wait(timeout=period_timeout):
            self._acq_samples()

    def _acq_samples(self):
        buffer_t = utils.get_epoch_ms() - self.get_acq_start_ms()
        try:
            if self._task and len(self.ai_channels) > 0:

                offset = 0
                for ch in self.ai_channels:
                    buf = self._acq_buf[slice(offset, None, self.total_channels)]
                    ch.put_data(buf, buffer_t)
                    offset += 1
        except Exception as e:
            self._lgr.exception(f'For device {self.name}, unknown exception {e}')

    def _is_valid_device_name(self, device):
        try:
            dev_info = DaqDeviceInfo(device)
        except ULError as e:
            self._lgr.exception(f'Device {device} is not a valid device')
            return False
        else:
            return True

    def remove_channel(self, name: str):
        if not self._task:
            raise pyAI.AIDeviceException(f'Cannot remove channel {name}, device {self.cfg.device_name} not yet opened')
        acquiring = self.is_acquiring
        self.stop()
        super().remove_channel(name)
        if acquiring:
            self.start()

    def open(self):
        ul.a_input_mode(self.board_num, AnalogInputMode.SINGLE_ENDED)
        # ensure the buffer type is float64 for MCC devices
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

    def start(self):
        rate = np.ceil(1.0 / self.cfg.sampling_period_ms)
        ul.a_in_scan(int(self.cfg.device_name), self._chan_range[0], self._chan_range[1],
                     self.acq_points, rate, self.cfg.ai_range, self._acq_buf, self._scan_options)
        total_count = self.total_channels * self.samples_per_read
        self._acq_buf = ul.scaled_win_buf_alloc(total_count)
        super().start()

    def stop(self):
        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
        running = ul.get_status(self.board_num, FunctionType.AIFUNCTION).status
        waiting = 0
        while running == Status.RUNNING and (waiting < 1.0):
            time.sleep(0.1)
            waiting += 0.1
            running = ul.get_status(self.board_num, FunctionType.AIFUNCTION).status

        if running == Status.RUNNING:
            self._lgr.error(f'MCC Board {self.board_num} could not be stopped')
        super().stop()
