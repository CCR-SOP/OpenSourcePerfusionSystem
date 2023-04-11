# -*- coding: utf-8 -*-
""" Class to auto adjust the percentages of gases in a GB100 gas mixer
    based on physiological values read from a CDI monitor

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from threading import Thread, Event

from time import sleep

from pyPerfusion.pyCDI import CDIData
from pyPerfusion.utils import get_epoch_ms


class AutoGasMixer:
    def __init__(self, name: str, gas_device, cdi_reader):
        self._lgr = logging.getLogger(__name__)
        self.name = name
        self.gas_device = gas_device
        self.cdi_reader = cdi_reader

        self.adjust_rate_ms = 10_000

        self.acq_start_ms = 0
        self._event_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def is_running(self):
        return self.is_streaming

    def run(self):
        self.is_streaming = True
        next_t = self.acq_start_ms + self.adjust_rate_ms
        # sleep only 1 second so the thread can be terminated
        # in a quicker fashion. if adjust_rate is smaller, then use that
        sleep_time = min(1_000, self.adjust_rate_ms)
        while not self._event_halt.is_set():
            if get_epoch_ms() > next_t:
                if self.gas_device and self.cdi_reader:
                    ts, all_vars = self.cdi_reader.get_last_acq()
                    if all_vars is not None:
                        cdi_data = CDIData(all_vars)
                        self.update_gas_on_cdi(cdi_data)
                    else:
                        self._lgr.debug(f'{self.name} No CDI data. Cannot run gas mixers automatically')
                next_t += self.adjust_rate_ms
            else:
                sleep(sleep_time/1_000)

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'AutoGasMixer {self.name}'
        self.__thread.start()
        self._lgr.debug(f'AutoGasMixer {self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.debug(f'AutoGasMixer {self.name} stopped')

    def update_gas_on_cdi(self, cdi_data):
        # this is the base class, so do nothing
        self._lgr.warning('Attempting to use the base AutoGasMixer class, no adjustment will be made')


class AutoGasMixerVenous(AutoGasMixer):
    def __init__(self, name: str, gas_device, cdi_reader):
        super().__init__(name, gas_device, cdi_reader)
        self.o2_ch = 1
        self.co2_ch = 2
        self.o2_adjust = 1  # in %
        self.flow_adjust = 5

    def update_gas_on_cdi(self, cdi_data):
        try:
            self._update_O2(cdi_data.venous_sO2)
            self._update_flow(cdi_data.venous_pH)
        except AttributeError:
            # this will happen if there is invalid CDI data
            pass

    def _update_flow(self, pH: float):
        if pH == -1:
            self._lgr.warning(f'{self.name} pH is out of range. Cannot be adjusted automatically')
        elif pH < self.gas_device.cfg.pH_range[0]:
            self.gas_device.adjust_flow(self.flow_adjust)
        elif pH > self.gas_device.cfg.pH_range[1]:
            self.gas_device.adjust_flow(-self.flow_adjust)

    def _update_O2(self, O2: float):
        o2_adjust = 0
        o2 = self.gas_device.get_percent_value(self.o2_ch)

        if O2 == -1:
            self._lgr.warning(f'{self.name}: O2 is out of range. Cannot be adjusted automatically')
        elif O2 < self.gas_device.cfg.O2_range[0]:
            o2_adjust = self.o2_adjust
            self._lgr.warning(f'{self.name}: O2 low')
        elif O2 > self.gas_device.cfg.O2_range[1]:
            o2_adjust = -self.o2_adjust
            self._lgr.warning(f'{self.name}: O2 high')
        new_percent = o2 + o2_adjust
        if o2_adjust is not 0:
            self.gas_device.set_percent_value(self.o2_ch, new_percent)


class AutoGasMixerArterial(AutoGasMixer):
    def __init__(self, name: str, gas_device, cdi_reader):
        super().__init__(name, gas_device, cdi_reader)
        self.o2_ch = 1
        self.co2_ch = 2

        self.co2_adjust = 1  # in %

    def update_gas_on_cdi(self, cdi_data):
        try:
            self.update_CO2(cdi_data.arterial_pH, cdi_data.arterial_CO2)
        except AttributeError:
            # this will happen if there is invalid CDI data
            pass

    def update_CO2(self, pH: float, CO2: float):
        co2_adjust = 0
        co2 = self.gas_device.get_percent_value(self.co2_ch)

        check_co2 = False
        if pH == -1:
            self._lgr.warning(f'{self.name}: pH is out of range. Cannot be adjusted automatically')
            check_co2 = True
        elif pH > self.gas_device.cfg.pH_range[1]:
            co2_adjust = self.co2_adjust
            self._lgr.warning(f'{self.name}: pH high, blood alkalotic')
        elif pH < self.gas_device.cfg.pH_range[0]:
            co2_adjust = -self.co2_adjust
            self._lgr.warning(f'{self.name}: pH low, blood acidotic')
        else:
            check_co2 = True

        if check_co2 is True:  # only check CO2 is pH checking didn't work - pH more important parameter to monitor
            if CO2 == -1:
                self._lgr.warning(f'{self.name}: CO2 is out of range. Cannot be adjusted automatically')
            elif CO2 < self.gas_device.cfg.CO2_range[0]:
                co2_adjust = self.co2_adjust
                self._lgr.warning(f'{self.name}: CO2 low, blood alkalotic')
            elif CO2 > self.gas_device.cfg.CO2_range[1]:
                co2_adjust = -self.co2_adjust
                self._lgr.warning(f'{self.name}: CO2 high, blood acidotic')

        new_percent = co2 + co2_adjust
        if co2_adjust is not 0:
            self.gas_device.set_percent_value(self.co2_ch, new_percent)

