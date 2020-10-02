# -*- coding: utf-8 -*-
"""Provides abstract class for generating an sine wave on analog output

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import threading


class AOSine:
    def __init__(self, line, period_ms, volts_p2p, volts_offset, Hz, bits=12):
        self._line = line
        self._period_ms = period_ms
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._Hz = Hz
        self._bits = bits

        self._volts_per_bit = self._calc_volts_per_bit()

    def _calc_volts_per_bit(self):
        vpb = self._volts_p2p / (2 ** self._bits)
        return vpb

    def _adc_to_volts(self, adc):
        return adc * self._volts_per_bit + self._volts_offset

    def _volts_to_adc(self, volts):
        return int((volts - self._volt_range[0]) / self._volts_per_bit)

    def set_sine(self, volts_p2p, volts_offset, Hz):
        self._volts_p2p = volts_p2p
        self._volts_offset = volts_offset
        self._Hz = Hz
        self._set_sine()

    def _set_sine(self):
        print(f'Creating sine {self._volts_p2p}*sine(2*pi*{self._Hz}) + {self._volts_offset}')
