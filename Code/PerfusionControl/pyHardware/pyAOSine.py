# -*- coding: utf-8 -*-
"""Provides abstract class for generating an sine wave on analog output

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import threading
from pathlib import Path
import numpy as np


class AOSine(threading.Thread):
    def __init__(self, line, period_ms, volts_p2p, volts_offset, Hz, bits=12):
        threading.Thread.__init__(self)
        self._line = line
        self._period_ms = period_ms
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._Hz = Hz
        self._bits = bits
        self._fid = None

        self._data_type = np.float64
        self._buffer = np.array([0] * 10, dtype=self._data_type)


        self._event_halt = threading.Event()
        self._lock_buf = threading.Lock()

        self._gen_cycle()

    def _output_samples(self):
        self._buffer.tofile(self._fid)

    def run(self):
        while not self._event_halt.wait(1.0 / self._Hz):
            with self._lock_buf:
                self._output_samples()

    def halt(self):
        self._event_halt.set()
        if self._fid:
            self._fid.close()

    def open(self):
        self._fid = open(Path('__data__') / 'sine.dat', 'w+')

    def set_sine(self, volts_p2p, volts_offset, Hz):
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._Hz = Hz
        self._set_sine()

    def _set_sine(self):
        print(f'Creating sine {self._volts_p2p}*sine(2*pi*{self._Hz}) + {self._volts_offset}')
        self._gen_cycle()

    def _gen_cycle(self):
        t = np.arange(0, 1 / self._Hz, step=self._period_ms / 1000.0)
        with self._lock_buf:
            self._buffer = self._volts_p2p / 2.0 * np.sin(2 * np.pi * self._Hz * t, dtype=self._data_type) + self._volts_offset
