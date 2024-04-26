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
from ctypes import cast, POINTER, c_double
from dataclasses import dataclass
import time
import inspect

import numpy as np
from mcculw import ul
from mcculw.enums import ScanOptions, ULRange, FunctionType, Status, InterfaceType
from mcculw.ul import ULError
from mcculw.device_info import DaqDeviceInfo

import pyHardware.pyAI as pyAI
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class AIMCCDeviceConfig(pyAI.AIDeviceConfig):
    ai_range: ULRange = ULRange.BIP10VOLTS
    total_buffers: int = 10  # require a minimum of 2 buffers, larger is better


class MCCAIDevice(pyAI.AIDevice):
    def __init__(self, name: str):
        super().__init__(name)

        self.cfg = AIMCCDeviceConfig()
        self.board_num = None
        self.buf_dtype = np.float64
        self.__timeout = 1.0
        self._last_acq = None
        self._acq_buf = None
        self._memhandle = None
        self._device = None
        self._read_buf_idx = 0
        self._chan_range = (-1, -1)
        self._scan_options = ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA

    @property
    def total_channels(self):
        total_channels = self._chan_range[1] - self._chan_range[0] + 1
        return total_channels

    @property
    def acq_points(self):
        return self.total_channels * self.samples_per_read

    def get_status(self):
        status_info = None
        try:
            if self.board_num is not None:
                status_info = ul.get_status(self.board_num, FunctionType.AIFUNCTION)
        except ULError as e:
            self._lgr.error(f'Failure getting status from MCC Board {self.board_num}')
            self._lgr.error(e)
            raise pyAI.AIDeviceException(f'In MCCAIDevice.get_status: {e.message}')
        return status_info

    def is_open(self):
        return self.board_num is not None

    def run(self):
        # setup is done at the start of the run() as the UL library showed strange
        # behavior when the setup was done in another function during early testing

        first_run = True
        lines = [ch.cfg.line for ch in self.ai_channels]
        self._chan_range = (min(lines), max(lines))
        self._read_buf_idx = 0

        total_count = self.acq_points * self.cfg.total_buffers
        if self._memhandle is not None:
            try:
                ul.win_buf_free(self._memhandle)
            except ULError as e:
                self._lgr.exception(e)
                raise pyAI.AIDeviceException(e)

        self._memhandle = ul.scaled_win_buf_alloc(total_count)

        if self._memhandle == 0:
            raise pyAI.AIDeviceException(f'Could not allocate memory of size {total_count}')

        self._acq_buf = cast(self._memhandle, POINTER(c_double))
        self._lgr.debug(f'period is {self.cfg.sampling_period_ms}')
        rate = int(1000.0 / self.cfg.sampling_period_ms)
        self._lgr.debug(f'rate is {rate}')
        try:
            actual_rate = ul.a_in_scan(self.board_num, self._chan_range[0], self._chan_range[1],
                                       total_count, rate,
                                       self.cfg.ai_range, self._memhandle, self._scan_options)
        except Exception as e:
            self._lgr.exception(e)
        if actual_rate != rate:
            self._lgr.warning(f'Actual sampling rate for MCC Board {self.board_num} is {actual_rate}, should be {rate}')

        while not PerfusionConfig.MASTER_HALT.is_set():
            period_timeout = self.cfg.read_period_ms / 1_000.0 / 2.0
            if not self._event_halt.wait(timeout=period_timeout):
                try:
                    if self.board_num is not None:

                        status_info = self.get_status()
                        if status_info.status == Status.RUNNING:

                            if status_info.cur_index >= 0:
                                buf_idx = int(status_info.cur_index / self.acq_points)
                                if first_run:
                                    if buf_idx == 0:
                                        first_run = False
                                else:
                                    self._lgr.debug(f'buf_idx={buf_idx}, read_idx={self._read_buf_idx}, '
                                                    f'cur_index={status_info.cur_index}, acq_pts={self.acq_points}')
                                    if buf_idx != self._read_buf_idx:
                                        self._acq_samples();
                except Exception as e:
                    raise pyAI.AIDeviceException(e)

        self._lgr.debug('pyAI_MCC thread has ended.')

    def _acq_samples(self):
        self._lgr.debug('acquiring samples')
        buffer_t = utils.get_epoch_ms() - self.get_acq_start_ms()
        try:
            offset = self._read_buf_idx * self.acq_points
            for ch in self.ai_channels:
                ch_offset = offset + ch.cfg.line
                buf = self._acq_buf[slice(ch_offset, ch_offset+self.acq_points, self.total_channels)]
                ch.put_data(buf, buffer_t)
            self._read_buf_idx += 1
            if self._read_buf_idx == self.cfg.total_buffers:
                self._read_buf_idx = 0
        except Exception as e:
            self._lgr.exception(f'For device {self.name}, unknown exception {e}')

    def remove_channel(self, name: str):
        self._lgr.info(f'Removing channel {str}')
        acquiring = self.is_acquiring
        if acquiring:
            self.stop()
        super().remove_channel(name)
        if acquiring:
            self.start()

    def open(self):
        # ensure the buffer type is float64 for MCC devices
        self.cfg.buf_type = 'float64'
        super().open()
        descriptors = ul.get_daq_device_inventory(InterfaceType.USB)
        if len(descriptors) == 1:
            device = descriptors[0]
            self.board_num = 0
        elif len(descriptors) > 1:
            self._lgr.info(f'Found multiple MCC devices, checking for matching board numbers')
            device = next(filter(lambda desc: ul.get_board_number(desc) == int(self.cfg.device_name), descriptors), None)
            self.board_num = self.cfg.device_number
        else:
            device = None
            self.board_num = None

        if device is None:
            msg = f'Device "{self.board_num}" is not a valid MCC Board Num on this system. ' \
                  f'Please check that the hardware had been plugged in and the correct' \
                  f'device name has been used'
            self._lgr.error(msg)
            self.board_num = None
            raise pyAI.AIDeviceException(msg)

        self._device = DaqDeviceInfo(self.board_num)
        self.board_num = ul.get_board_number(device)

    def close(self):
        if self.is_acquiring:
            self.stop()

    def stop(self):
        super().stop()
        if self.board_num is not None:
            ul.stop_background(self.board_num, FunctionType.AIFUNCTION)

            status_info = self.get_status()
            if status_info is not None:
                waiting = 0
                while status_info.status == Status.RUNNING and (waiting < 1.0):
                    time.sleep(0.1)
                    waiting += 0.1
                    status_info = self.get_status()

                if status_info.status == Status.RUNNING:
                    self._lgr.error(f'MCC Board {self.board_num} could not be stopped')
                else:
                    self._lgr.debug('MCC Board stopped')
                    ul.win_buf_free(self._memhandle)

