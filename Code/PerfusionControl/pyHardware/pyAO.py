# -*- coding: utf-8 -*-
"""Provides abstract class for controlling Analog Output

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import threading


class AO:
    def __init__(self, line, period_ms, volt_range=[-10, 10], bits=12):
        self._line = line
        self._period_ms = period_ms
        self._volt_range = volt_range
        self._bits = bits

        self._volts_per_bit = self._calc_volts_per_bit()

    def _calc_volts_per_bit(self):
        volt_rng = self._volt_range[1] - self._volt_range[0]
        vpb = (volt_rng / (2 ** self._bits))
        return vpb

    def _adc_to_volts(self, adc):
        return adc * self._volts_per_bit + self._volt_range[0]

    def _volts_to_adc(self, volts):
        return int((volts - self._volt_range[0]) / self._volts_per_bit)

    def _set_ao_counts(self, adc):
        print(f'Setting analog output to {adc} counts, {self._adc_to_volts(adc)} Volts')

    def config(self, volt_range):
        self._volt_range = volt_range

    def set_voltage(self, volts):
        adc = self._volts_to_adc(volts)
        self._set_ao_counts(adc)

    def set_adc_counts(self, adc):
        self._set_ao_counts(adc)