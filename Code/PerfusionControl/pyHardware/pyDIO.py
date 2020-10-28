# -*- coding: utf-8 -*-
"""Provides abstract class for controlling DIO

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""

import time
import threading
from dataclasses import dataclass


@dataclass
class DIOState:
    LOW = 0
    HIGH = 1


class DIOActiveHighState(DIOState):
    ACTIVE = DIOState.HIGH
    INACTIVE = DIOState.LOW


class DIOActiveLowState(DIOState):
    ACTIVE = DIOState.LOW
    INACTIVE = DIOState.HIGH


class DIO:
    def __init__(self, port, line, active_high=True, read_only=True):
        self._port = port
        self._line = line
        self._active_high = active_high
        self._read_only = read_only

        self._active_state = DIOActiveHighState if self._active_high else DIOActiveLowState
        self.__value = self._active_state.INACTIVE

        # create a dummy timer so is_alive function is always valid
        self.__timer = threading.Timer(0, self.activate)
        # timer is still considered alive when the callback is called

    def activate(self):
        if not self.__timer.is_alive() and not self._read_only:
            self._activate()

    def _activate(self):
        self.__value = self._active_state.ACTIVE
        print(f"{self.__value}")

    def deactivate(self):
        if not self.__timer.is_alive() and not self._read_only:
            self._deactivate()

    def _deactivate(self):
        self.__value = self._active_state.INACTIVE
        print(f"{self.__value}")

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
            # pulse starts immediately
            self._toggle()
            self.__timer = threading.Timer(milliseconds/1000.0, self._toggle)
            self.__timer.start()

    @property
    def value(self):
        return self.__value
