# -*- coding: utf-8 -*-
""" Base class for serial communication over USB
    Uses pySerial library available on PyPi

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import serial


class USBSerial:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._port_name = None
        self._baud = None
        self.__serial = serial.Serial()

    @property
    def port_name(self):
        return self._port_name

    @property
    def baud(self):
        return self._baud

    def open(self, port_name, baud):
        self._port_name = port_name
        self._baud = baud
        if self.__serial.is_open:
            self.__serial.close()

        self.__serial.port = self._port_name
        self.__serial.baudrate = self._baud
        self.__serial.open()

    def close(self):
        self.__serial.close()

    def send(self, str2send):
        if self.__serial.is_open:
            self.__serial.write(str2send.encode('UTF-8'))
            self.__serial.flush()

    def get_response(self, max_bytes=1, eol='\r', timeout=1.0):
        response = ''
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            response = self.__serial.read_until(eol, size=max_bytes).decode('UTF-8')
        return response

    def recv(self, expected_bytes, timeout=0):
        if self.__serial.is_open:
            self.__serial.timeout = timeout
            recv_bytes = self.__serial.read(expected_bytes)
            return recv_bytes
