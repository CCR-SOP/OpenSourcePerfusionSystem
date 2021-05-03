# -*- coding: utf-8 -*-
"""Provides abstract class for generating an sine wave on analog output

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import threading
import logging

import numpy as np


class AODeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


class AO:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._period_ms = None
        self._volts_p2p = 0
        self._volts_offset = 0
        self._Hz = 0.0
        self._bits = None
        self._fid = None
        self.__thread = None
        self.__ramp2dc = False

        self._data_type = np.float64
        self._buffer = np.array([0] * 10, dtype=self._data_type)

        self._event_halt = threading.Event()
        self._lock_buf = threading.Lock()

    @property
    def devname(self):
        return 'ao'

    def open(self, period_ms, bits=12):
        self._period_ms = period_ms
        self._bits = bits
        self._gen_cycle()

    def close(self):
        self.halt()

    def start(self):
        if self.__thread:
            self.halt()
        self.__thread = threading.Thread(target=self.run)
        self.__thread.start()

    def _output_samples(self):
        self._buffer.tofile(self._fid)

    def _calc_timeout(self):
        if self._Hz > 0.0:
            timeout = 1.0 / self._Hz
        else:
            timeout = 0.1
        return timeout

    def run(self):
        while not self._event_halt.wait(self._calc_timeout()):
            with self._lock_buf:
                self._output_samples()

    def halt(self):
        if self.__thread:
            self.set_dc(0)
            self.wait_for_task()
            if self.__thread.is_alive():
                self._event_halt.set()
                self.__thread.join(timeout=2.0)
            self.__thread = None
        if self._fid:
            self._fid.close()
            self._fid = None
        self._logger.debug('halted pyAO')

    def set_sine(self, volts_p2p, volts_offset, Hz):
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._Hz = Hz
        self._set_sine()

    def _set_sine(self):
        self._logger.info(f'Creating sine {self._volts_p2p}*sine(2*pi*{self._Hz}) + {self._volts_offset}')
        self._gen_cycle()

    def _gen_cycle(self):
        if self._Hz > 0.0:
            t = np.arange(0, 1 / self._Hz, step=self._period_ms / 1000.0)
            with self._lock_buf:
                self._buffer = self._volts_p2p / 2.0 * \
                               np.sin(2 * np.pi * self._Hz * t, dtype=self._data_type) \
                               + self._volts_offset
        else:
            self._buffer = np.full(1, self._volts_offset)
            self._logger.info(f"creating dc of {self._volts_offset}")

    def set_dc(self, volts):
        self._Hz = 0.0
        self._volts_offset = volts
        self._logger.info(f"setting dc voltage to {self._volts_offset}")

    def set_ramp(self, start_volts, stop_volts, accel):
        self._Hz = 0.0
        with self._lock_buf:
            if not start_volts == stop_volts:
                seconds = abs(start_volts - stop_volts) / accel
                calc_len = int(seconds/(self._period_ms / 1000.0))
                if calc_len == 0:
                    calc_len = 1
                self._buffer = np.linspace(start_volts, stop_volts, num=calc_len)
                self._logger.info(f'setting ramp from {start_volts} to {stop_volts} over {seconds} seconds with {calc_len} samples')
            else:
                self._buffer = np.array([stop_volts], dtype=self._data_type)
                self._logger.info('no change, no ramp set')
