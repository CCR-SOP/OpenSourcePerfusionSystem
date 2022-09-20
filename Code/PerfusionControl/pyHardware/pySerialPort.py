# -*- coding: utf-8 -*-
""" Base class for standard RS-232 based serial communication

    Uses pySerial library available on PyPi to provide basic serial
    communication functions such as open/close and send/recv.

    This class should implement the SerialInterface defined in pyPump11Elite

    @project: LiverPerfusion NIH
    @author: John Kakareka, NIH

    This work was created by an employee of the US Federal Gov
    and under the public domain.
"""
import logging

import serial


class SerialPort:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)
        self.__serial = serial.Serial()

    @property
    def port_name(self):
        return self.__serial.portstr

    @property
    def baud_rate(self):
        return self.__serial.baudrate

    @property
    def is_open(self):
        return self.__serial.isOpen()

    def open(self, port_name: str, baud_rate: int, xonoff: bool = False) -> None:
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = port_name
        self.__serial.baudrate = baud_rate
        self.__serial.xonxoff = xonoff
        try:
            self.__serial.open()
        except serial.serialutil.SerialException as e:
            self._lgr.error(f'Could not open serial port {self.__serial.portstr}')
            self._lgr.error(f'{e}')
            self._port_name = None
            self._baud_rate = None

    def close(self) -> None:
        if self.__serial:
            self.__serial.close()

    def send(self, str2send: str) -> None:
        if self.__serial.is_open:
            self.__serial.write(str2send.encode('UTF-8'))
            self.__serial.flush()

    def wait_for_string(self, max_bytes: int = 1, terminator: str = '\r', timeout: float = 1.0) -> str:
        response = ''
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            response = self.__serial.read_until(terminator, size=max_bytes).decode('UTF-8')
        return response
