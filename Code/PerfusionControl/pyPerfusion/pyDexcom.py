# -*- coding: utf-8 -*-
""" Class for reading from a Dexcom G6 sensor
    Requires dexcom_G6_reader library

    @project: LiverPerfusion NIH
    @author: John Kakareka, NIH

    This work was created by an employee of the US Federal Gov
    and under the public domain.
"""
import logging
import struct
from time import perf_counter
from threading import Thread, Event
from time import perf_counter, sleep, time
from collections import deque
from queue import Queue, Empty
from dataclasses import dataclass, asdict

import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class DexcomConfig:
    name: str = ''
    com_port: str = ''
    serial_number: str = ''
    read_period_ms: int = 0


class DexcomReceiver:
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        self.cfg = DexcomConfig()
        self.name = name
        self._receiver = None

        self.__thread = None
        self._event_halt = Event()
        self._queue = deque(maxlen=100)

        self._last_acq_time = None
        self._last_error = None
        # stores the perf_counter value at the start of the acquisition which defines the zero-time for all
        # following samples
        self.__acq_start_t = 0

    def read_config(self):
        cfg = DexcomConfig()
        PerfusionConfig.read_into_dataclass('dexcom', self.name, cfg)
        self.open(cfg)

    def write_config(self):
        PerfusionConfig.write_from_dataclass('dexcom', self.name, self.cfg)

    def open(self, cfg: DexcomConfig = None) -> None:
        if cfg is not None:
            self.cfg = cfg
        self._queue = Queue()
        self._receiver = Dexcom(self.cfg.com_port)
        # JWK, verify SN
        actual_SN = self._receiver.ReadManufacturingData().get('SerialNumber')
        if actual_SN != self.cfg.serial_number:
            self._lgr.error(f'Dexcom sensor {self.name} ({self.cfg.com_port}) did not match serial'
                            f' number (expected={self.cfg.serial_number}, found={actual_SN}')
            self._receiver = None
            self.cfg = DexcomConfig()
        else:
            self._receiver.Connect()

    def close(self):
        self._receiver.Disconnect()
        self.stop()

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.__acq_start_t = perf_counter()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyDexcom {self.name}'
        self.__thread.start()

    def stop(self):
        if self.__thread and self.__thread.is_alive():
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def run(self):
        next_t = time()
        offset = 0
        while not self._event_halt.is_set():
            next_t += offset + self.cfg.read_period_ms / 1000.0
            delay = next_t - time()
            if delay > 0:
                sleep(delay)
                offset = 0
            else:
                offset = -delay
            self._acq_samples()

    def _acq_samples(self):
        data, new_time, error = self._receiver.get_data()
        ts = struct.pack('i', int(perf_counter() * 1000.0))
        self._last_error = error
        if new_time != self._last_acq_time:
            self._queue.append((data, ts))
            self._last_acq_time = new_time

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.pop()
        except IndexError:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t

    def clear(self):
        self._queue.clear()
