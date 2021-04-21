# -*- coding: utf-8 -*-
"""Provides concrete class for controlling AI through NIDAQmx
This work was created by an employee of the US Federal Gov
and under the public domain.
Author: John Kakareka
"""

import time
from datetime import datetime
import logging

import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *

import pyHardware.pyAI as pyAI


class NIDAQ_AI(pyAI.AI):
    def __init__(self, period_ms, volts_p2p, volts_offset):
        self._logger = logging.getLogger(__name__)
        self._logger.debug('opening nidaq_ai')
        super().__init__(period_ms, buf_type=np.float32)
        self._dev = None
        self._line = None
        self.__timeout = 1.0
        self.__task = None
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._exception_msg_ack = False
        self._last_acq = None

    @property
    def _devname(self):
        lines = self.get_ids()
        devstr = ','.join([f'{self._dev}/ai{line}' for line in lines])
        return devstr

    def is_open(self):
        return self.__task is not None

    def _convert_to_units(self, buffer, channel):
        data = super()._convert_to_units(buffer, channel)
        return self.data_type(data)

    def set_calibration(self, ch, low_pt, low_read, high_pt, high_read):
        super().set_calibration(ch, low_pt, low_read, high_pt, high_read)

    def _acq_samples(self):
        sleep_time = self._read_period_ms / self._period_sampling_ms / 1000.0
        samples_read = PyDAQmx.int32()
        buffer_t = time.perf_counter()
        ch_ids = self.get_ids()
        buffer = np.zeros(self.samples_per_read * len(ch_ids), dtype=np.float64)
        try:
            if self.__task:
                # self._logger.debug(f'Attempting to read {self.samples_per_read} from {self._devname}')
                self.__task.ReadAnalogF64(self.samples_per_read, self._read_period_ms, DAQmx_Val_GroupByChannel, buffer,
                                          len(buffer), PyDAQmx.byref(samples_read), None)
                self._last_acq = datetime.now()
            if self._exception_msg_ack:
                self._logger.info('Recovered from previous exception.')
                self._exception_msg_ack = False
        except PyDAQmx.ReadBufferTooSmallError:
            if not self._exception_msg_ack:
                self._logger.error(f'ReadBufferTooSmallError when reading {self._devname}')
                self._logger.error(f'Samples/read = {self.samples_per_read}, Buffer len = {len(buffer)}')
                self._exception_msg_ack = True
        except PyDAQmx.DAQmxFunctions.ResourceNotInPool_RoutingError:
            # the RuntimeAborted_RoutingError will probably got caught first
            if not self._exception_msg_ack:
                self._logger.error(f'DAQ resource no longer available, possibly due to hibernation or USB disconnect')
                self._exception_msg_ack = True
        except PyDAQmx.DAQmxFunctions.RuntimeAborted_RoutingError:
            if not self._exception_msg_ack:
                self._logger.error(f'DAQ resource no longer available, possibly due to hibernation or USB disconnect')
                self._exception_msg_ack = True
        except PyDAQmx.SamplesNoLongerAvailableError:
            if not self._exception_msg_ack:
                recovery = datetime.now()
                self._logger.error(f'DAQ {self._devname} could not keep up with HW acquisition. '
                                   f'This error could be caused by the laptop entering sleep mode. '
                                   f'Last acq time was {self._last_acq}, recovery time is {recovery}')
                self._exception_msg_ack = True
                self._logger.info(f'Stopping NIDAQ task for {self._devname}')
                self.__task.StopTask()
                self.__task.WaitUntilTaskDone(2.0)
                self._logger.info(f'Restarting NIDAQ task for {self._devname}')
                self.__task.StartTask()
        except PyDAQmx.DAQException as e:
            if not self._exception_msg_ack:
                self._logger.error('Exception attempting to read analog data')
                self._logger.exception(e)
                self._exception_msg_ack = True
        offset = 0
        for ch in ch_ids:
            # buf = self.data_type(buffer[offset::len(ch_ids)])
            buf = self.data_type(buffer[offset:offset+self.samples_per_read])
            if len(self._calibration[ch]):  # If the ai channel has been calibrated:
                buf = self._convert_to_units(buf, ch)
            self._queue_buffer[ch].put((buf, buffer_t))
            offset += self.samples_per_read

    def open(self, dev):
        self._logger.debug(f'Opening device {self._devname}')
        super().open()
        self._dev = dev
        self.reopen()

    def reopen(self):
        try:
            if self.__task:
                self.close()

            if self._dev:
                self._logger.debug(f'Creating new pyDAQmx AI Voltage Channel for {self._devname}')
                self.__task = Task()
                volt_min = self._volts_offset - 0.5 * self._volts_p2p
                volt_max = self._volts_offset + 0.5 * self._volts_p2p
                self.__task.CreateAIVoltageChan(self._devname, None, DAQmx_Val_RSE, volt_min, volt_max, DAQmx_Val_Volts, None)
                hz = 1.0 / (self._period_sampling_ms / 1000.0)
                self.__task.CfgSampClkTiming("", hz, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps,
                                             self.samples_per_read)
        except PyDAQmx.DevCannotBeAccessedError as e:
            self._logger.error(f'Could not access device {self._dev}. Please ensure device is'
                               f'plugged in and assigned the correct device name')
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
            self.__task.WaitUntilTaskDone(2.0)
