# -*- coding: utf-8 -*-
"""Class for acquiring a finite number of samples
Intended for use with chemical sensors which are acquired periodically through a
valve control system

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from threading import Event
import warnings

import PyDAQmx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI


class AI_Finite_NIDAQ(NIDAQ_AI):
    def __init__(self, period_ms, volts_p2p, volts_offset, samples_per_read=None):
        super().__init__(period_ms, volts_p2p, volts_offset)
        self._logger = logging.getLogger(__name__)
        self._sample_mode = PyDAQmx.DAQmxConstants.DAQmx_Val_FiniteSamps
        self.samples_per_read = samples_per_read
        self._acq_complete = False
        self.semaphore = None

    @property
    def expected_acq_time(self):
        return self.samples_per_read * self.period_sampling_ms

    def start(self):
        self._acq_complete = False
        self._read_period_ms = self.samples_per_read * len(self.get_ids()) * self._period_sampling_ms * 1.1
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
        if self.semaphore:
            self.semaphore.acquire()
        self._acq_samples()
        self._acq_complete = True
        if self.semaphore:
            self.semaphore.release()
