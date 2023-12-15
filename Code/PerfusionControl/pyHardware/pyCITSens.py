"""  class for reading from CITSens MeMo USB glucose sensor

@project: Liver Perfusion, NIH
@author: John Kakareka, NIH

"""
from threading import Thread, Event
from time import sleep
from queue import Queue
from enum import IntEnum
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import serial
import serial.tools.list_ports

import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyHardware.pyGeneric as pyGeneric


class CITSensException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class CITSensConfig:
    port: str = ''


class CITSens(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = CITSensConfig()

        self.__serial = serial.Serial()
        self._timeout = 1.0

        self._buffer = np.zeros(1, dtype=self.data_dtype)

        self._evt_halt = Event()
        self.__thread = None
        self.is_streaming = False
        self.sampling_period_ms = 5000
        self.buf_len = 1

    @property
    def hw(self):
        return self

    def is_open(self):
        return self.__serial and self.__serial.is_open

    def open(self) -> None:
        super().open()
        if self.__serial.is_open:
            self.__serial.close()
        self.__serial.port = self.cfg.port
        self.__serial.baudrate = 115200
        self.__serial.stopbits = serial.STOPBITS_ONE
        self.__serial.parity = serial.PARITY_NONE
        self.__serial.bytesize = serial.EIGHTBITS
        self.__serial.timeout = self._timeout
        try:
            self.__serial.open()
        except serial.serialutil.SerialException as e:
            self.__serial = None
            self._lgr.exception(e)
            raise CITSensException(f' Could not open serial port at {self.cfg.port}')

    def close(self):
        super().close()
        self.stop()
        if self.__serial:
            self.__serial.close()

    def parse_response(self, response: str):
        try:
            data = self.data_dtype.type(response.strip('\r\n'))
        except ValueError as e:
            data = self.data_dtype.type(0)
            self._lgr.debug(f'could not interpret response ||{response}||')
        return data

    def read_from_serial(self):
        # self._lgr.debug('Attempting to read serial data from CDI')
        resp = self.__serial.read_until(expected=b'\r\n').decode('utf-8')
        return resp

    def run(self):  # continuous data stream
        self.is_streaming = True
        self._evt_halt.clear()
        while not PerfusionConfig.MASTER_HALT.is_set():
            if self._evt_halt.wait(self.sampling_period_ms / 1000.0):
                break
            if self.is_open():
                resp = ''
                try:
                    resp = self.read_from_serial()
                except serial.SerialException as e:
                    self._lgr.exception(e)
                    # assuming this is an occasional glitch so log, but keep going
                else:
                    if resp != '':
                        self._buffer[0] = self.parse_response(resp)
                        # self._lgr.debug(f'parsing {resp} to {self._buffer[0]}')
                        self._queue.put((self._buffer, utils.get_epoch_ms()))
        self.is_streaming = False

    def start(self):
        super().start()
        self._evt_halt.clear()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{self.name}'
        self.__thread.start()

    def stop(self):
        if self.is_streaming:
            self._evt_halt.set()
        super().stop()


class MockCITSens(CITSens):
    def __init__(self, name):
        super().__init__(name)
        self._is_open = False
        self.last_pkt = ''
        self.last_pkt_index = 0

    def is_open(self):
        return self._is_open

    def open(self) -> None:
        self._is_open = True
        self._queue = Queue()

    def close(self):
        pass

    def read_from_serial(self):
        rand = np.random.randint(10, size=1)[0]
        return f'{rand}\r\n'
