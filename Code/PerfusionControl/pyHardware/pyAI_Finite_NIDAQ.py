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

import PyDAQmx

from pyHardware.pyAI_NIDAQ import NIDAQ_AI


class AI_Finite_NIDAQ(NIDAQ_AI):
    def __init__(self, period_ms, volts_p2p, volts_offset):
        super().__init__(period_ms, volts_p2p, volts_offset)
        self._logger = logging.getLogger(__name__)
        self._sample_mode = PyDAQmx.DAQmxConstants.DAQmx_Val_FiniteSamps

    def start(self, samples=None):
        if samples:
            self.samples_per_read = samples
            self._read_period_ms = samples * len(self.get_ids()) * self._period_sampling_ms * 1.1
            self._update_task()
            self._task.StartTask()

    def is_done(self):
        done = False
        try:
            done = self._task.WaitUntilTaskDone(0) == 0
        except PyDAQmx.DAQmxFunctions.WaitUntilDoneDoesNotIndicateDoneError:
            done = False

        return done
