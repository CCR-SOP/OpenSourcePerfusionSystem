# -*- coding: utf-8 -*-
"""Base class for generating analog output

Provides basic interface for accessing analog outputs.
Used directly only for testing other code without direct access to the hardware

Requires numpy library

Uses a thread to output a new data buffer at required intervals. For this base class, the thread allows outputting data
similar to how actual hardware would produce data. Derived classes can use this to output buffers as needed.

This class will output the data to a file to verify operation. This can also be used by derived classes to verify
the data being written to the analog output channel.

Provides functions to create a sine wave, DC voltage, and a ramp waveform. The ramp waveform is intended to provide
as lower acceleration/deceleration to DC value to prevent stalling of motors.

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import threading
import logging

import numpy as np


class AODeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


class AO:
    def __init__(self, filename=None):
        self._lgr = logging.getLogger(__name__)
        self._period_ms = None
        self._volts_p2p = 0
        self._volts_offset = 0
        self._Hz = 0.0
        self._bits = None
        self._file_id = None
        self._filename = filename
        self.__thread = None
        self.__ramp2dc = False

        self._data_type = np.float64
        self._buffer = np.array([0] * 10, dtype=self._data_type)

        self._event_halt = threading.Event()
        self._lock_buf = threading.Lock()

    @property
    def devname(self):
        return 'ao'

    @property
    def bits(self):
        return self._bits

    @property
    def period_ms(self):
        return self._period_ms

    def open(self, period_ms, bits=12):
        self._period_ms = period_ms
        self._bits = bits
        if self._filename:
            self._file_id = open(self._filename, 'wb')
        self.set_dc(0)

    def close(self):
        self.stop()

    def start(self):
        if self.__thread:
            self.stop()
        self.__thread = threading.Thread(target=self.run)
        self.__thread.name = f'pyAO {self.devname}'
        self.__thread.start()

    def stop(self):
        if self.__thread:
            self.set_dc(0)
            if self.__thread.is_alive():
                self._event_halt.set()
                self.__thread.join(timeout=2.0)
            self.__thread = None
        if self._file_id:
            self._file_id.close()
            self._file_id = None
        self._lgr.debug('halted pyAO')

    def _output_samples(self):
        if self._file_id:
            self._buffer.tofile(self._file_id)

    def _calc_output_delay(self):
        if self._Hz > 0.0:
            delay = 1.0 / self._Hz
        else:
            delay = 0.1
        return delay

    def run(self):
        while not self._event_halt.wait(self._calc_output_delay()):
            with self._lock_buf:
                self._output_samples()

    def set_sine(self, volts_p2p, volts_offset, hertz):
        if hertz > 0.0:
            self._lgr.info(f'Creating sine {self._volts_p2p}*sine(2*pi*{self._Hz}) + {self._volts_offset}')
            self._volts_p2p = volts_p2p
            self._volts_offset = volts_offset
            self._Hz = hertz
            t = np.arange(0, 1 / self._Hz, step=self._period_ms / 1000.0)
            with self._lock_buf:
                self._buffer = self._volts_p2p / 2.0 * \
                               np.sin(2 * np.pi * self._Hz * t, dtype=self._data_type) \
                               + self._volts_offset
        else:
            self._lgr.error(f"Attempt to create a non-positive frequency {hertz}")

    def set_dc(self, volts):
        self._Hz = 0.0
        self._volts_offset = volts
        self._lgr.info(f"creating dc of {self._volts_offset}")
        self._buffer = np.full(1, self._volts_offset)

    def set_ramp(self, start_volts, stop_volts, accel):
        self._Hz = 0.0
        with self._lock_buf:
            if not start_volts == stop_volts:
                seconds = abs(start_volts - stop_volts) / accel
                calc_len = int(seconds/(self._period_ms / 1000.0))
                if calc_len == 0:
                    calc_len = 1
                self._buffer = np.linspace(start_volts, stop_volts, num=calc_len)
                self._lgr.info(f'setting ramp from {start_volts} to {stop_volts} over {seconds} seconds with {calc_len} samples')
            else:
                self._buffer = np.array([stop_volts], dtype=self._data_type)
                self._lgr.info('no change, no ramp set')
