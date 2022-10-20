# -*- coding: utf-8 -*-
"""Class for acquiring a finite number of samples
Intended for use with chemical sensors which are acquired periodically through a
valve control system

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import warnings
from dataclasses import dataclass

import PyDAQmx

import pyHardware.pyAI_NIDAQ as pyAI_NIDAQ


@dataclass
class FiniteNIDAQAIDeviceConfig(pyAI_NIDAQ.AINIDAQDeviceConfig):
    samples_per_read: int = 1


class FiniteNIDAQAIDevice(pyAI_NIDAQ.NIDAQAIDevice):
    def __init__(self):
        super().__init__()
        self._sample_mode = PyDAQmx.DAQmxConstants.DAQmx_Val_FiniteSamps
        self._acq_complete = False
        self._notify = None

    @property
    def expected_acq_time(self):
        return self.samples_per_read * self.cfg.sampling_period_ms

    @property
    def samples_per_read(self):
        return self.cfg.samples_per_read

    def start(self, notify=None):
        self._acq_complete = False
        self.cfg.read_period_ms = self.samples_per_read * len(self.ai_channels) * self.cfg.sampling_period_ms
        self._notify = notify
        super().start()

    def stop(self):
        # catch and ignore StoppedBeforeDoneWarning
        # since starting an acq automatically calls stop, the finite acq mode of NIDAQ issues a warning
        # indicating that the specified number of samples was not acquired.
        # this warning can safely be ignored
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            super().stop()

    def is_done(self):
        return self._acq_complete

    def run(self):
        self._acq_samples()
        self._acq_complete = True
        self._lgr.debug(f'completed finite acq for device {self.cfg.name}/{self.cfg.device_name}')
        if self._notify:
            self._lgr.debug(f'notifying {self._notify}')
            self._notify()
            self._notify = None
