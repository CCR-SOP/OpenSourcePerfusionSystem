# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx
This work was created by an employee of the US Federal Gov
and under the public domain.
Author: John Kakareka
"""

import time
import logging

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
        self.__task = None
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._acq_buf = None
        self._acq_type = np.float64

    @property
    def _devname(self):
        lines = self.get_ids()
        devstr = ','.join([f'{self._dev}/ai{line}' for line in lines])
        return devstr

    def _convert_to_units(self, buffer, channel):
        data = super()._convert_to_units(buffer, channel)
        return self.data_type(data)

    def set_calibration(self, ch, low_pt, low_read, high_pt, high_read):
        super().set_calibration(ch, low_pt, low_read, high_pt, high_read)

    def _acq_samples(self):
        samples_read = PyDAQmx.int32()
        buffer_t = time.perf_counter()
        try:
            if self.__task:
                self.__task.ReadAnalogF64(self.samples_per_read, self._read_period_ms, DAQmx_Val_GroupByChannel,
                                          self._acq_buf, len(self._acq_buf), PyDAQmx.byref(samples_read), None)
        except PyDAQmx.ReadBufferTooSmallError:
            self._logger.error(f'ReadBufferTooSmallError when reading {self._devname}')
            self._logger.error(f'Samples/read = {self.samples_per_read}, Buffer len = {len(self._acq_buf)}')
        offset = 0
        for ch in self.get_ids():
            buf = self.data_type(self._acq_buf[offset:offset+self.samples_per_read])
            if len(self._calibration[ch]):  # If the ai channel has been calibrated:
                buf = self._convert_to_units(buf, ch)
            self._queue_buffer[ch].put((buf, buffer_t))
            offset += self.samples_per_read

    def open(self, dev):
        super().open()
        self._dev = dev
        self.reopen()

    def reopen(self):
        try:
            if self.__task:
                self.close()

            if self._dev:
                self.__task = Task()
                volt_min = self._volts_offset - 0.5 * self._volts_p2p
                volt_max = self._volts_offset + 0.5 * self._volts_p2p
                self._logger.debug(f'opening {self._devname}')
                self.__task.CreateAIVoltageChan(self._devname, None, DAQmx_Val_RSE, volt_min, volt_max, DAQmx_Val_Volts, None)
                hz = 1.0 / (self._period_sampling_ms / 1000.0)
                self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                             self.samples_per_read)
        except PyDAQmx.DAQError as e:
            self._logger.error("Could not create AI Channel for {}".format(self._devname))
            self._logger.error(f"{e}")
            self.__task = None

    def close(self):
        self.stop()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def start(self):
        if self.__task:
            ch_ids = self.get_ids()
            self._acq_buf = np.zeros(self.samples_per_read * len(ch_ids), dtype=self._acq_type)
            self.__task.StartTask()
            super().start()

    def stop(self):
        super().stop()
        if self.__task:
            self.__task.StopTask()
            self.__task.WaitUntilTaskDone(2.0)