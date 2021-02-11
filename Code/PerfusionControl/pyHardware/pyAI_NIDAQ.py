# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import time
import threading

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAI as pyAI


class NIDAQ_AI(pyAI.AI):
    def __init__(self, period_ms, volts_p2p, volts_offset):
        super().__init__(period_ms, buf_type=np.float32)
        self._dev = None
        self._line = None
        self.__timeout = 1.0
        self.__task = None
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset

    @property
    def _devname(self):
        lines = self._queue_buffer.keys()
        devstr = ','.join([f'{self._dev}/ai{line}' for line in lines])
        print(devstr)
        return devstr

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        samples_read = PyDAQmx.int32()
        buffer_t = time.perf_counter()
        ch_ids = self._queue_buffer.keys()
        buffer = np.zeros(self.samples_per_read * len(ch_ids), dtype=np.float64)
        self.__task.ReadAnalogF64(self.samples_per_read, self._read_period_ms, DAQmx_Val_GroupByChannel, buffer,
                                  len(buffer), PyDAQmx.byref(samples_read), None)
        offset = 0
        for ch in ch_ids:
            # buf = self.data_type(buffer[offset::len(ch_ids)])
            buf = self.data_type(buffer[offset:offset+self.samples_per_read])
            self._queue_buffer[ch].put((buf, buffer_t))
            offset += self.samples_per_read

    def open(self, dev):
        super().open()
        self._dev = dev
        try:
            if self.__task:
                self.close()

            print('Creating task')
            self.__task = Task()
            volt_min = self._volts_offset - 0.5 * self._volts_p2p
            volt_max = self._volts_offset + 0.5 * self._volts_p2p
            self.__task.CreateAIVoltageChan(self._devname, None, DAQmx_Val_RSE, volt_min, volt_max, DAQmx_Val_Volts, None)
            hz = 1.0 / (self._period_sampling_ms / 1000.0)
            self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                         self.samples_per_read)
        except PyDAQmx.DAQError as e:
            print("Could not create AO Channel for {}".format(self._devname))
            print(f"{e}")
            self.__task = None

    def close(self):
        self.stop()
        if self.__task:
            self.__task.StopTask()
            self.__task = None

    def start(self):
        if self.__task:
            self.__task.StartTask()
        super().start()

    def stop(self):
        super().stop()
        if self.__task:
            self.__task.StopTask()
