# -*- coding: utf-8 -*-
"""Provides abstract class for controlling DIO

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import logging
import threading
from dataclasses import dataclass


@dataclass
class DIOState:
    LOW = 0
    HIGH = 1


class DIOActiveHighState(DIOState):
    def __init__(self):
        self.ACTIVE = DIOState.HIGH
        self.INACTIVE = DIOState.LOW

    def __str__(self):
        return "ActiveHigh"


class DIOActiveLowState(DIOState):
    def __init__(self):
        self.ACTIVE = DIOState.LOW
        self.INACTIVE = DIOState.HIGH

    def __str__(self):
        return "ActiveLow"


class DIODeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


class DIO:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._port = None
        self._line = None
        self._active_high = True
        self._read_only = False

        self._active_state = DIOActiveHighState() if self._active_high else DIOActiveLowState()
        self.__value = self._active_state.INACTIVE

        # create a dummy timer so is_alive function is always valid
        self.__timer = threading.Timer(0, self.activate)
        # timer is still considered alive when the callback is called

    @property
    def active_state(self):
        return self._active_state

    @property
    def read_only(self):
        return self._read_only

    @property
    def devname(self):
        return f"port{self._port}/line{self._line}"

    @property
    def is_open(self):
        return self._port is not None and self._line is not None

    @property
    def is_active(self):
        return self.value == self.active_state.ACTIVE

    def open(self, port, line, active_high=True, read_only=True):
        self._port = port
        self._line = line
        self._active_high = active_high
        self._read_only = read_only

        self._active_state = DIOActiveHighState() if self._active_high else DIOActiveLowState()
        self.__value = self._active_state.INACTIVE

    def activate(self):
        if not self.__timer.is_alive() and not self._read_only:
            self._activate()

    def _activate(self):
        self.__value = self._active_state.ACTIVE
        self._logger.debug(f"Activating DIO with value of {self.__value}")

    def deactivate(self):
        if not self.__timer.is_alive() and not self._read_only:
            self._deactivate()

    def _deactivate(self):
        self.__value = self._active_state.INACTIVE
        self._logger.debug(f"Deactivating DIO with value of {self.__value}")

    def toggle(self):
        if not self.__timer.is_alive() and not self._read_only:
            self._toggle()

    def _toggle(self):
        if self.__value == self._active_state.INACTIVE:
            self._activate()
        else:
            self._deactivate()

    def pulse(self, milliseconds):
        if not self._read_only:
            if self.is_open():
                # pulse starts immediately
                self._toggle()
                self.__timer = threading.Timer(milliseconds/1000.0, self._toggle)
                self.__timer.start()

    @property
    def value(self):
        return self.__value
