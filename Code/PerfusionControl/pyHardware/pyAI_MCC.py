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
from mcculw.enums import ScanOptions, ULRange, AnalogInputMode, FunctionType, Status, InterfaceType
from mcculw.ul import ULError
from mcculw.device_info import DaqDeviceInfo

import pyHardware.pyAI as pyAI
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class AIMCCDeviceConfig(pyAI.AIDeviceConfig):
    ai_range: ULRange = ULRange.BIP10VOLTS
    total_buffers: int = 2


class MCCAIDevice(pyAI.AIDevice):
    def __init__(self, name: str):
        super().__init__(name)

        self.cfg = AIMCCDeviceConfig()
        self.board_num = None
        self.buf_dtype = np.float64
        self.__timeout = 1.0
        self._last_acq = None
        self._acq_buf = None
        self._read_buf_idx = -1
        self._chan_range = (-1, -1)
        self._scan_options = (ScanOptions.BACKGROUND |
                              ScanOptions.CONTINUOUS |
                              ScanOptions.BURSTMODE |
                              ScanOptions.SCALEDATA)

    @property
    def total_channels(self):
        total_channels = self._chan_range[1] - self._chan_range[0] + 1
        return total_channels

    @property
    def acq_points(self):
        return self.total_channels * self.samples_per_read

    def get_status(self):
        status = Status.IDLE
        try:
            if self.board_num:
                status = ul.get_status(self.board_num, FunctionType.AIFUNCTION)
        except ULError as e:
            self._lgr.error(f'Failure getting status from MCC Board {self.board_num}')
            self._lgr.error(e)
            raise pyAI.AIDeviceException(f'In MCCAIDevice.get_status: {e.message}')
        return status

    def is_open(self):
        # if channels were added and device name is valid, then we have
        # confirmed that the device is present and the configuration
        # is valid
        return self.board_num is not None

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            time.sleep(self.__timeout)
            if self.board_num:
                status, transfer_status = ul.get_scan_status(self.board_num)
                if status == Status.RUNNING:
                    buf_idx = (transfer_status % self.acq_points) - 1
                    if not self._read_buf_idx == buf_idx:
                        self._read_buf_idx = buf_idx - 1
                        self._acq_samples()

    def _acq_samples(self):
        buffer_t = utils.get_epoch_ms() - self.get_acq_start_ms()
        try:
            offset = self._read_buf_idx * self.acq_points
            for ch in self.ai_channels:
                buf = self._acq_buf[slice(offset, offset+self.acq_points, self.total_channels)]
                ch.put_data(buf, buffer_t)
                offset += 1
        except Exception as e:
            self._lgr.exception(f'For device {self.name}, unknown exception {e}')

    def remove_channel(self, name: str):
        acquiring = self.is_acquiring
        self.stop()
        super().remove_channel(name)
        if acquiring:
            self.start()

    def open(self):
        # ensure the buffer type is float64 for MCC devices
        self.cfg.buf_type = 'float64'
        super().open()

        descriptors = ul.get_daq_device_inventory(InterfaceType.USB)
        device = next(filter(lambda desc: ul.get_board_number(desc) == self.board_num, descriptors), None)
        if device:
            self.board_num = ul.get_board_number(device)
            ul.a_input_mode(self.board_num, AnalogInputMode.SINGLE_ENDED)
        else:
            msg = f'Device "{self.board_num}" is not a valid MCC Board Num on this system. ' \
                  f'Please check that the hardware had been plugged in and the correct' \
                  f'device name has been used'
            self._lgr.error(msg)
            self.board_num = None
            raise pyAI.AIDeviceException(msg)

    def close(self):
        self.stop()

    def start(self):
        lines = [ch.cfg.line for ch in self.ai_channels]
        self._chan_range = (min(lines), max(lines))

        total_count = self.total_channels * self.samples_per_read * self.cfg.total_buffers
        self._acq_buf = ul.scaled_win_buf_alloc(total_count)
        rate = np.ceil(1.0 / self.cfg.sampling_period_ms)
        self._read_buf_idx = -1
        ul.a_in_scan(self.board_num, self._chan_range[0], self._chan_range[1],
                     self.acq_points, rate, self.cfg.ai_range, self._acq_buf, self._scan_options)

        super().start()

    def stop(self):
        if self.board_num:
            ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
        running = self.get_status()
        waiting = 0
        while running == Status.RUNNING and (waiting < 1.0):
            time.sleep(0.1)
            waiting += 0.1
            running = self.get_status()

        if running == Status.RUNNING:
            self._lgr.error(f'MCC Board {self.board_num} could not be stopped')
        else:
            ul.win_buf_free(self._acq_buf)
        super().stop()
